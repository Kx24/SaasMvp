"""
Management command: check_tenant_setup
========================================

Audita el estado de provisioning de uno o varios tenants. Pensado como
gate de QA antes de dar por terminado el onboarding de un cliente nuevo
(y para re-auditar tenants existentes).

No modifica nada -- solo reporta. Salida en texto plano ASCII (sin
emojis) para que sea segura en cualquier consola.

Ampliado como GATE (#FLOW-02 / BOLT-05): con chequeos en [FAIL] el
comando termina con CommandError (exit != 0), salvo --warn-only, que
conserva el comportamiento informativo original. Chequeos nuevos:
SEOConfig("home") con titulo/descripcion reales (no vacios ni
placeholder), secciones activas sin marcadores de relleno y
ClientEmailSettings presente cuando el tenant tiene formulario de
contacto.

Uso:
    python manage.py check_tenant_setup mi-empresa
    python manage.py check_tenant_setup --all
    python manage.py check_tenant_setup mi-empresa --warn-only
"""
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.tenants.models import Client, ClientEmailSettings, FormConfig
from apps.website.models import Section

# Marcadores de contenido de relleno. 'todo' en minusculas es espanol
# legitimo ("todo lo que necesitas") -- solo TODO en mayusculas cuenta
# como marcador, por eso va en la lista case-sensitive.
PLACEHOLDER_MARKERS_CI = ('lorem', 'placeholder', 'xxx')
PLACEHOLDER_MARKERS_CS = ('TODO',)


def _find_placeholder(text):
    """Devuelve el marcador encontrado en `text`, o None."""
    if not text:
        return None
    for marker in PLACEHOLDER_MARKERS_CI:
        if re.search(rf'\b{marker}\b', text, re.IGNORECASE):
            return marker
    for marker in PLACEHOLDER_MARKERS_CS:
        if re.search(rf'\b{marker}\b', text):
            return marker
    return None


class Command(BaseCommand):
    help = (
        'Audita el estado de provisioning de uno o varios tenants '
        '(theme, dominio, email, SEO, contenido). Exit != 0 con fallos, '
        'salvo --warn-only.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'slug',
            type=str,
            nargs='?',
            help='Slug del tenant a auditar'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Auditar todos los tenants activos'
        )
        parser.add_argument(
            '--warn-only',
            action='store_true',
            help='Solo reportar: no terminar con error aunque haya fallos '
                 '(comportamiento informativo original del comando)'
        )

    def handle(self, *args, **options):
        slug = options.get('slug')
        check_all = options['all']

        if not slug and not check_all:
            raise CommandError('Debes pasar un slug o usar --all')

        if check_all:
            clients = Client.objects.filter(is_active=True).order_by('name')
            if not clients.exists():
                self.stdout.write('No hay tenants activos.')
                return
        else:
            try:
                clients = [Client.objects.get(slug=slug)]
            except Client.DoesNotExist:
                raise CommandError(f'El tenant "{slug}" no existe')

        failures = []
        for client in clients:
            failures.extend(self._check_client(client))

        if failures and not options['warn_only']:
            raise CommandError(
                'Gate de tenant con fallos: ' + '; '.join(failures)
            )

    def _fail(self, failures, label, message):
        failures.append(f'{label}: {message}')
        self.stdout.write(self.style.ERROR(f'[FAIL] {message}'))

    def _check_client(self, client):
        self.stdout.write('')
        self.stdout.write('='*60)
        self.stdout.write(f'  {client.name} ({client.slug})')
        self.stdout.write('='*60)

        failures = []
        self._check_theme(client, failures)
        self._check_domain(client, failures)
        self._check_email(client, failures)
        self._check_seo(client, failures)
        self._check_sections(client, failures)
        return failures

    def _check_theme(self, client, failures):
        # Misma lógica de resolución que TenantTemplateLoader
        client_folder = client.slug
        if client.template:
            client_folder = client.template.strip().lower()

        theme_path = Path(settings.BASE_DIR) / 'templates' / client_folder
        if theme_path.exists():
            self.stdout.write(f'[OK]   Tema visual "{client.template}" -> {theme_path}')
        else:
            self._fail(
                failures, 'Tema',
                f'Tema visual "{client.template}" no resuelve a ninguna carpeta real '
                f'({theme_path} no existe). El sitio cae a un fallback genérico sin marca.'
            )

    def _check_domain(self, client, failures):
        domain = client.primary_domain
        if domain:
            self.stdout.write(f'[OK]   Dominio principal: {domain.domain}')
        else:
            self._fail(failures, 'Dominio', 'El tenant no tiene ningún dominio asignado.')

    def _check_email(self, client, failures):
        has_contact_form = FormConfig.objects.filter(client=client).exists()

        try:
            email_settings = client.email_settings
        except ClientEmailSettings.DoesNotExist:
            if has_contact_form:
                self._fail(
                    failures, 'ClientEmailSettings',
                    'El tenant tiene formulario de contacto pero no existe '
                    'ClientEmailSettings (debería auto-crearse vía signal; revisar).'
                )
            else:
                self.stdout.write(self.style.WARNING(
                    '[WARN] No existe ClientEmailSettings para este tenant (debería '
                    'auto-crearse vía signal; revisar).'
                ))
            return

        if email_settings.notify_mode == 'dashboard':
            self.stdout.write(self.style.WARNING(
                '[WARN] notify_mode="dashboard": los emails del formulario de contacto '
                'NO se envían, solo quedan visibles en el dashboard. Configurar provider '
                'y notify_mode en ClientEmailSettings si el cliente espera notificaciones.'
            ))
        elif has_contact_form and not email_settings.from_email:
            self._fail(
                failures, 'Email',
                f'notify_mode="{email_settings.notify_mode}" pero from_email está '
                'vacío: los envíos del formulario de contacto van a fallar.'
            )
        else:
            self.stdout.write(f'[OK]   Email de contacto configurado (notify_mode={email_settings.notify_mode})')

    def _check_seo(self, client, failures):
        seo = client.seo_configs.filter(page_key='home').first()
        if seo is None:
            self._fail(
                failures, 'SEO',
                'No existe SEOConfig(page_key="home") para este tenant -- '
                'el sitio funciona pero sin meta description/OG reales.'
            )
            return

        problems = []
        if not (seo.title or '').strip():
            problems.append('title vacío')
        if not (seo.meta_description or '').strip():
            problems.append('meta_description vacía')
        for field_name in ('title', 'meta_description'):
            marker = _find_placeholder(getattr(seo, field_name) or '')
            if marker:
                problems.append(f'{field_name} contiene marcador de relleno "{marker}"')

        if problems:
            self._fail(failures, 'SEO', 'SEOConfig("home") incompleto: ' + ', '.join(problems))
        else:
            self.stdout.write('[OK]   SEOConfig("home") con título y descripción reales')

    def _check_sections(self, client, failures):
        sections = Section.objects.filter(client=client, is_active=True)
        dirty = []
        for section in sections:
            for field_name in ('title', 'subtitle', 'description'):
                marker = _find_placeholder(getattr(section, field_name) or '')
                if marker:
                    dirty.append(
                        f'sección "{section.title}" ({section.section_type}): '
                        f'{field_name} contiene "{marker}"'
                    )

        if dirty:
            self._fail(failures, 'Contenido', 'Marcadores de relleno visibles: ' + '; '.join(dirty))
        elif sections.exists():
            self.stdout.write(f'[OK]   {sections.count()} sección(es) activa(s) sin marcadores de relleno')
        else:
            self.stdout.write(self.style.WARNING(
                '[WARN] El tenant no tiene ninguna sección activa.'
            ))
