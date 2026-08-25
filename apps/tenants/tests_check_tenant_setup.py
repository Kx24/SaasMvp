"""
Tests del gate de calidad check_tenant_setup (#FLOW-02 / BOLT-05).

El comando audita el provisioning de un tenant (tema, dominio, email, SEO).
Ampliado como GATE: SEOConfig("home") con título/descripción reales (no
vacíos ni placeholder), secciones activas sin marcadores de relleno
(lorem/placeholder/TODO/xxx) y ClientEmailSettings presente cuando el
tenant tiene formulario de contacto. Con fallos → CommandError (exit != 0);
--warn-only conserva el comportamiento informativo previo.

Convención de tests de la app tenants: archivo PLANO tests_*.py (§0.0 del
kanban agéntico) — no crear apps/tenants/tests/.
"""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.marketing.models import SEOConfig
from apps.tenants.models import Client, ClientEmailSettings, Domain
from apps.website.models import Section


def _make_tenant(slug):
    client = Client.objects.create(
        name=f'Tenant {slug}', slug=slug, company_name=f'{slug} SpA',
        contact_email=f'{slug}@test.com', contact_phone='+56900000001',
        is_active=True, template='themes/servelec',  # carpeta real en templates/
    )
    Domain.objects.create(
        client=client, domain=f'{slug}.test',
        domain_type='custom', is_primary=True, is_active=True, is_verified=True,
    )
    return client


def _complete_tenant(slug):
    client = _make_tenant(slug)
    SEOConfig.objects.create(
        client=client, page_key='home',
        title='Servelec Ingeniería — Proyectos eléctricos en Chile',
        meta_description='Diseño, ejecución y certificación de proyectos eléctricos.',
    )
    Section.objects.create(
        client=client, section_type='hero', title='Soluciones eléctricas',
        description='Más de 10 años de experiencia certificada.', is_active=True,
    )
    return client


class CheckTenantSetupGateTestCase(TestCase):
    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command('check_tenant_setup', *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    # ------------------------------------------------------------------
    # Tenant incompleto: cada chequeo nuevo debe reportar FAIL y el
    # comando salir con error (rojo: la versión base pasa en silencio).
    # ------------------------------------------------------------------

    def test_missing_home_seo_fails(self):
        _make_tenant('sin-seo')
        with self.assertRaises(CommandError) as ctx:
            self._run('sin-seo')
        self.assertIn('SEO', str(ctx.exception))

    def test_placeholder_seo_fails(self):
        client = _make_tenant('seo-lorem')
        SEOConfig.objects.create(
            client=client, page_key='home',
            title='Lorem ipsum dolor', meta_description='placeholder',
        )
        with self.assertRaises(CommandError):
            self._run('seo-lorem')

    def test_empty_seo_title_fails(self):
        client = _make_tenant('seo-vacio')
        SEOConfig.objects.create(client=client, page_key='home', title='',
                                 meta_description='Descripción real del negocio.')
        with self.assertRaises(CommandError):
            self._run('seo-vacio')

    def test_active_section_with_placeholder_fails(self):
        client = _complete_tenant('seccion-lorem')
        Section.objects.create(
            client=client, section_type='about', title='Nosotros',
            description='Lorem ipsum dolor sit amet.', is_active=True,
        )
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command('check_tenant_setup', 'seccion-lorem', stdout=out)
        self.assertIn('lorem', out.getvalue().lower())

    def test_inactive_section_with_placeholder_does_not_fail(self):
        client = _complete_tenant('seccion-inactiva')
        Section.objects.create(
            client=client, section_type='about', title='Draft',
            description='TODO: escribir contenido', is_active=False,
        )
        self._run('seccion-inactiva')  # no debe lanzar

    def test_spanish_todo_word_is_not_a_placeholder(self):
        """'todo' en minúsculas es español legítimo — solo TODO (mayúsculas)
        es marcador de trabajo pendiente."""
        client = _complete_tenant('espanol')
        Section.objects.create(
            client=client, section_type='services',
            title='Todo para tu proyecto',
            description='Encuentra todo lo que necesitas.', is_active=True,
        )
        self._run('espanol')  # no debe lanzar

    def test_contact_form_without_email_settings_fails(self):
        client = _complete_tenant('sin-email')
        # El signal crea ClientEmailSettings; el gate cubre el caso en que
        # no exista (tenants pre-signal o borrado manual).
        ClientEmailSettings.objects.filter(client=client).delete()
        with self.assertRaises(CommandError) as ctx:
            self._run('sin-email')
        self.assertIn('ClientEmailSettings', str(ctx.exception))

    # ------------------------------------------------------------------
    # Tenant completo y modo warn-only
    # ------------------------------------------------------------------

    def test_complete_tenant_passes(self):
        _complete_tenant('completo')
        output = self._run('completo')
        self.assertIn('[OK]', output)
        self.assertNotIn('[FAIL]', output)

    def test_warn_only_preserves_informative_behavior(self):
        _make_tenant('incompleto-warn')  # sin SEO home: fallaría el gate
        output = self._run('incompleto-warn', warn_only=True)
        self.assertIn('[FAIL]', output)  # el problema se reporta igual

    def test_command_is_read_only(self):
        client = _complete_tenant('solo-lectura')
        seo_before = list(SEOConfig.objects.filter(client=client).values())
        sections_before = list(Section.objects.filter(client=client).values())
        self._run('solo-lectura')
        self.assertEqual(seo_before, list(SEOConfig.objects.filter(client=client).values()))
        self.assertEqual(sections_before, list(Section.objects.filter(client=client).values()))
