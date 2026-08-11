"""
Management command: check_tenant_setup
========================================

Audita el estado de provisioning de uno o varios tenants. Pensado como
gate de QA antes de dar por terminado el onboarding de un cliente nuevo
(y para re-auditar tenants existentes).

No modifica nada -- solo reporta. Salida en texto plano ASCII (sin
emojis) para que sea segura en cualquier consola.

Uso:
    python manage.py check_tenant_setup mi-empresa
    python manage.py check_tenant_setup --all
"""
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.tenants.models import Client, ClientEmailSettings


class Command(BaseCommand):
    help = 'Audita el estado de provisioning de uno o varios tenants (theme, dominio, email, SEO)'

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

        for client in clients:
            self._check_client(client)

    def _check_client(self, client):
        self.stdout.write('')
        self.stdout.write('='*60)
        self.stdout.write(f'  {client.name} ({client.slug})')
        self.stdout.write('='*60)

        self._check_theme(client)
        self._check_domain(client)
        self._check_email(client)
        self._check_seo(client)

    def _check_theme(self, client):
        # Misma lógica de resolución que TenantTemplateLoader
        client_folder = client.slug
        if client.template:
            client_folder = client.template.strip().lower()

        theme_path = Path(settings.BASE_DIR) / 'templates' / client_folder
        if theme_path.exists():
            self.stdout.write(f'[OK]   Tema visual "{client.template}" -> {theme_path}')
        else:
            self.stdout.write(self.style.ERROR(
                f'[FAIL] Tema visual "{client.template}" no resuelve a ninguna carpeta real '
                f'({theme_path} no existe). El sitio cae a un fallback genérico sin marca.'
            ))

    def _check_domain(self, client):
        domain = client.primary_domain
        if domain:
            self.stdout.write(f'[OK]   Dominio principal: {domain.domain}')
        else:
            self.stdout.write(self.style.ERROR(
                '[FAIL] El tenant no tiene ningún dominio asignado.'
            ))

    def _check_email(self, client):
        try:
            email_settings = client.email_settings
        except ClientEmailSettings.DoesNotExist:
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
        else:
            self.stdout.write(f'[OK]   Email de contacto configurado (notify_mode={email_settings.notify_mode})')

    def _check_seo(self, client):
        has_home_seo = client.seo_configs.filter(page_key='home').exists()
        if has_home_seo:
            self.stdout.write('[OK]   SEOConfig("home") configurado')
        else:
            self.stdout.write(self.style.WARNING(
                '[WARN] No existe SEOConfig(page_key="home") para este tenant -- '
                'el sitio funciona pero sin meta description/OG reales. Paso manual pendiente.'
            ))
