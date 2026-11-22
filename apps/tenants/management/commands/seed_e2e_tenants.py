"""
Seed idempotente de los 3 tenants que cubre la suite Playwright de
#TOOL-01 (tests/e2e/): servelec, andesscale, ranchocachimba.

Pensado para correr contra config.settings.e2e (DB SQLite descartable)
antes de levantar el servidor -- nunca contra datos reales. Reusa
update_or_create en vez de provision_tenant porque este último no es
idempotente (CommandError si el slug ya existe) y hace cosas que no
hacen falta acá (copiar carpetas de templates, subir a Cloudinary).

Uso:
    python manage.py seed_e2e_tenants --settings=config.settings.e2e
"""
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain
from apps.website.models import ContactSubmission, Section, Service

# DASH-05: tenant propio para la suite del dashboard (galería activa, un
# usuario owner y un mensaje sin leer). Separado de los 3 de arriba para no
# alterar lo que miden smoke.spec.js y a11y.spec.js. La contraseña es solo
# de desarrollo: este comando se niega a correr con DEBUG=False.
DASHBOARD_TENANT = {
    'slug': 'dash-e2e',
    'name': 'Dashboard E2E',
    'domain': 'dash-e2e.localhost',
    'template': 'themes/default',
    'primary_color': '#0b5fa5',
}
DASHBOARD_OWNER = {'username': 'owner-e2e', 'password': 'e2e-only-owner-pass'}

# domain usa *.localhost: todo resolver de SO/browser moderno lo manda a
# 127.0.0.1 por RFC 6761 sin tocar /etc/hosts (confirmado en Windows con
# nslookup). Un header Host manual (vía Playwright) no sirve -- Chromium
# rechaza sobreescribir Host con ERR_INVALID_ARGUMENT.
TENANTS = [
    {
        'slug': 'andesscale',
        'name': 'Andes Scale',
        'domain': 'andesscale.localhost',
        'template': 'themes/default',
        'primary_color': '#0ea5e9',
    },
    {
        'slug': 'servelec-e2e',
        'name': 'Servelec E2E',
        'domain': 'servelec-e2e.localhost',
        'template': 'themes/servelec',
        'primary_color': '#16a34a',
    },
    {
        'slug': 'ranchocachimba-e2e',
        'name': 'Rancho Cachimba E2E',
        'domain': 'ranchocachimba-e2e.localhost',
        'template': 'ranchocachimba',
        'primary_color': '#064B20',
    },
]


class Command(BaseCommand):
    help = 'Seed idempotente de tenants para la suite Playwright (#TOOL-01)'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                'seed_e2e_tenants solo corre con DEBUG=True (crea un usuario con '
                'contraseña de desarrollo): usa --settings=config.settings.e2e.')

        for spec in [*TENANTS, DASHBOARD_TENANT]:
            client, _ = Client.objects.update_or_create(
                slug=spec['slug'],
                defaults={
                    'name': spec['name'],
                    'company_name': spec['name'],
                    'contact_email': f"contacto@{spec['slug']}.test",
                    'contact_phone': '+56912345678',
                    'template': spec['template'],
                    'is_active': True,
                    'mode_under_construction': False,
                    'setup_completed': True,
                },
            )

            Domain.objects.update_or_create(
                client=client,
                domain=spec['domain'],
                defaults={
                    'domain_type': 'custom',
                    'is_primary': True,
                    'is_active': True,
                    'is_verified': True,
                },
            )

            # El signal post_save de Client ya crea ClientSettings.
            settings_obj = client.settings
            settings_obj.primary_color = spec['primary_color']
            settings_obj.contact_email = f"contacto@{spec['slug']}.test"
            settings_obj.contact_phone = '+56912345678'
            settings_obj.whatsapp_number = '56912345678'
            settings_obj.save()

            Section.objects.update_or_create(
                client=client, section_type='hero',
                defaults={
                    'title': f"Bienvenido a {spec['name']}",
                    'subtitle': 'Sitio de prueba E2E',
                    'order': 10,
                    'is_active': True,
                },
            )
            Section.objects.update_or_create(
                client=client, section_type='contact',
                defaults={
                    'title': 'Contáctanos',
                    'subtitle': 'Formulario de prueba E2E',
                    'order': 30,
                    'is_active': True,
                },
            )
            Service.objects.update_or_create(
                client=client, name='Servicio E2E',
                defaults={
                    'description': 'Servicio de prueba para la suite Playwright.',
                    'is_active': True,
                    'order': 10,
                },
            )

            if spec is DASHBOARD_TENANT:
                self._seed_dashboard(client)

            self.stdout.write(self.style.SUCCESS(f"OK: {spec['slug']} -> {spec['domain']}"))

    def _seed_dashboard(self, client):
        client.settings.enable_gallery = True
        client.settings.save(update_fields=['enable_gallery'])
        # Mismas secciones editables que ve el dueño en "Secciones".
        Section.objects.update_or_create(
            client=client, section_type='about',
            defaults={'title': 'Quiénes somos', 'description': 'Texto de prueba E2E',
                      'order': 20, 'is_active': True},
        )
        user, _ = User.objects.get_or_create(username=DASHBOARD_OWNER['username'])
        user.set_password(DASHBOARD_OWNER['password'])
        user.save()
        # El profile lo crea el signal de User: update_or_create, no create.
        UserProfile.objects.update_or_create(
            user=user, defaults={'client': client, 'role': 'owner'})
        if not ContactSubmission.objects.filter(client=client).exists():
            ContactSubmission.objects.create(
                client=client, name='Visita E2E', email='visita@e2e.test',
                message='Mensaje de prueba E2E')
