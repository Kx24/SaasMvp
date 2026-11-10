"""
#FLOW-01: provision_tenant/list_tenants/update_domain -- procedimiento de
ingreso de cliente.

Bug real encontrado al escribir el procedimiento: provision_tenant tenía
un solo flag --template que mezclaba industria (contenido semilla) con
tema visual (Client.template). Sus valores ('electricidad',
'servicios_profesionales', etc.) nunca coincidían con ninguna carpeta
real de templates/ ni con Client.THEME_CHOICES -- cada tenant creado con
este comando caía en el fallback global sin marca, sin ningún error
visible (`check_tenant_setup` sí lo hubiera detectado, pero nada obliga
a correrlo). Se separan en --industry (contenido) y --theme (validado
contra Client.THEME_CHOICES, ver test_theme_choice_is_validated_by_argparse).

list_tenants y update_domain referenciaban Client.domain, un campo que
no existe (el dominio vive en el modelo Domain) -- el primero crasheaba
siempre que había al menos un tenant, el segundo (con el diseño viejo)
pisaba el dominio de TODOS los tenants con el mismo valor tomado de
RENDER_EXTERNAL_HOSTNAME.
"""
import io

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.tenants.models import Client, Domain
from apps.website.models import Section, Service


class ProvisionTenantThemeIndustryTestCase(TestCase):

    def test_theme_choice_is_validated_by_argparse(self):
        # call_command con kwargs no pasa por la validacion de choices de
        # argparse -- hay que invocar en estilo CLI (todo strings) para
        # que CommandParser la ejecute de verdad.
        with self.assertRaises(CommandError):
            call_command(
                'provision_tenant', 'invalid-theme-test',
                '--industry=servicios_profesionales', '--theme=no-existe',
                stdout=io.StringIO(),
            )
        self.assertFalse(Client.objects.filter(slug='invalid-theme-test').exists())

    def test_valid_theme_choices_accepted(self):
        for value, _label in Client.THEME_CHOICES:
            slug = f"theme-ok-{value.replace('/', '-')}"
            call_command(
                'provision_tenant', slug,
                industry='servicios_profesionales', theme=value,
                stdout=io.StringIO(),
            )
            client = Client.objects.get(slug=slug)
            self.assertEqual(client.template, value)

    def test_theme_and_industry_are_independent(self):
        """El tema visual no debe depender de la industria elegida, y
        viceversa -- eran el mismo flag antes del fix."""
        call_command(
            'provision_tenant', 'independent-test',
            industry='electricidad', theme='themes/default',
            stdout=io.StringIO(),
        )
        client = Client.objects.get(slug='independent-test')
        self.assertEqual(client.template, 'themes/default')
        # El contenido semilla sí debe reflejar la industria (electricidad).
        services = Service.objects.filter(client=client)
        self.assertTrue(
            services.filter(name='Instalaciones Eléctricas').exists(),
            'El contenido semilla de "electricidad" no se aplicó',
        )

    def test_created_sections_and_theme_folder_pass_check_tenant_setup_theme_check(self):
        """Confirma en vivo que el tema resuelve a una carpeta real --
        mismo chequeo que hace check_tenant_setup._check_theme."""
        from pathlib import Path

        from django.conf import settings as django_settings

        call_command(
            'provision_tenant', 'resolves-real-folder',
            industry='servicios_profesionales', theme='themes/default',
            stdout=io.StringIO(),
        )
        client = Client.objects.get(slug='resolves-real-folder')
        theme_path = Path(django_settings.BASE_DIR) / 'templates' / client.template
        self.assertTrue(theme_path.exists(), f'{theme_path} no existe')

    def test_creates_hero_about_contact_sections(self):
        call_command(
            'provision_tenant', 'sections-test',
            industry='servicios_profesionales', theme='themes/default',
            stdout=io.StringIO(),
        )
        client = Client.objects.get(slug='sections-test')
        section_types = set(
            Section.objects.filter(client=client).values_list('section_type', flat=True)
        )
        self.assertEqual(section_types, {'hero', 'about', 'contact'})


class ListTenantsTestCase(TestCase):

    def test_does_not_crash_with_no_domain(self):
        Client.objects.create(name='Sin dominio', slug='sin-dominio-test')
        out = io.StringIO()
        call_command('list_tenants', stdout=out)
        self.assertIn('(sin dominio asignado)', out.getvalue())

    def test_shows_primary_domain(self):
        client = Client.objects.create(name='Con dominio', slug='con-dominio-test')
        Domain.objects.create(
            client=client, domain='con-dominio-test.cl',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )
        out = io.StringIO()
        call_command('list_tenants', stdout=out)
        self.assertIn('con-dominio-test.cl', out.getvalue())


class UpdateDomainTestCase(TestCase):

    def setUp(self):
        self.client_a = Client.objects.create(name='Tenant A', slug='update-domain-a')
        self.client_b = Client.objects.create(name='Tenant B', slug='update-domain-b')
        self.domain_a = Domain.objects.create(
            client=self.client_a, domain='old-a.cl',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )
        self.domain_b = Domain.objects.create(
            client=self.client_b, domain='old-b.cl',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )

    def test_updates_only_the_target_tenant(self):
        call_command('update_domain', 'update-domain-a', domain='new-a.cl', stdout=io.StringIO())

        self.domain_a.refresh_from_db()
        self.domain_b.refresh_from_db()
        self.assertEqual(self.domain_a.domain, 'new-a.cl')
        self.assertEqual(self.domain_b.domain, 'old-b.cl')  # sin tocar

    def test_creates_domain_when_tenant_has_none(self):
        client_c = Client.objects.create(name='Tenant C', slug='update-domain-c')
        call_command('update_domain', 'update-domain-c', domain='new-c.cl', stdout=io.StringIO())

        client_c.refresh_from_db()
        self.assertIsNotNone(client_c.primary_domain)
        self.assertEqual(client_c.primary_domain.domain, 'new-c.cl')

    def test_unknown_slug_raises_command_error(self):
        with self.assertRaises(CommandError):
            call_command('update_domain', 'no-existe-este-slug', domain='x.cl', stdout=io.StringIO())
