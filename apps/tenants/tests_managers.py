"""Cobertura de TenantAwareManager y de ramas del TenantMiddleware (CONS-11)."""
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from apps.tenants.managers import TenantAwareManager
from apps.tenants.middleware import TenantMiddleware
from apps.tenants.models import Client, Domain
from apps.website.models import ContactSubmission, Section, Service


class TenantAwareManagerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = Client.objects.create(name='Tenant A', contact_email='a@test.com')
        cls.b = Client.objects.create(name='Tenant B', contact_email='b@test.com')

    def test_for_client_no_devuelve_filas_de_otro_tenant(self):
        sa = Section.objects.create(client=self.a, section_type='hero', title='A')
        Section.objects.create(client=self.b, section_type='hero', title='B')
        self.assertEqual(list(Section.objects.for_client(self.a)), [sa])

    def test_active_excluye_inactivos(self):
        activo = Section.objects.create(client=self.a, section_type='hero', is_active=True)
        Section.objects.create(client=self.a, section_type='about', is_active=False)
        self.assertEqual(list(Section.objects.active()), [activo])

    def test_featured_con_is_featured_filtra_destacados_activos(self):
        dest = Service.objects.create(
            client=self.a, name='Dest', description='d', is_featured=True, is_active=True)
        Service.objects.create(
            client=self.a, name='Normal', description='d', is_featured=False, is_active=True)
        Service.objects.create(
            client=self.a, name='Inactivo', description='d', is_featured=True, is_active=False)
        self.assertEqual(list(Service.objects.featured()), [dest])

    def test_featured_sin_is_featured_devuelve_solo_activos(self):
        self.assertFalse(hasattr(Section, 'is_featured'))
        s1 = Section.objects.create(client=self.a, section_type='hero', is_active=True)
        Section.objects.create(client=self.a, section_type='about', is_active=False)
        self.assertEqual(list(Section.objects.featured()), [s1])

    def test_ordered_con_order_ordena_por_order(self):
        s2 = Section.objects.create(client=self.a, section_type='hero', order=2)
        s1 = Section.objects.create(client=self.a, section_type='about', order=1)
        self.assertEqual(list(Section.objects.ordered()), [s1, s2])

    def test_ordered_sin_order_devuelve_todos(self):
        self.assertFalse(hasattr(ContactSubmission, 'order'))
        c = ContactSubmission.objects.create(
            client=self.a, name='x', email='x@test.com', message='m')
        self.assertEqual(list(ContactSubmission.objects.ordered()), [c])

    def test_es_manager_tenant_aware(self):
        self.assertIsInstance(Section.objects, TenantAwareManager)


class MiddlewareBranchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_a = Client.objects.create(name='Tenant A', contact_email='a@test.com')
        Domain.objects.create(
            client=cls.client_a, domain='tenant-a.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True)

    def setUp(self):
        self.mw = TenantMiddleware(lambda r: HttpResponse('ok'))
        self.rf = RequestFactory()

    @override_settings(DEBUG=True)
    def test_atajo_tenant_param_con_debug_resuelve_tenant(self):
        req = self.rf.get('/', {'tenant': self.client_a.slug})
        client, domain = self.mw._detect_tenant(req, 'localhost')
        self.assertEqual(client, self.client_a)
        self.assertIsNone(domain)

    @override_settings(DEBUG=True)
    def test_atajo_tenant_param_slug_inexistente_no_resuelve(self):
        req = self.rf.get('/', {'tenant': 'no-existe'})
        self.assertEqual(self.mw._detect_tenant(req, 'localhost'), (None, None))

    @override_settings(DEBUG=False)
    def test_atajo_tenant_param_se_ignora_sin_debug(self):
        req = self.rf.get('/', {'tenant': self.client_a.slug})
        self.assertEqual(self.mw._detect_tenant(req, 'localhost'), (None, None))

    def test_preview_sin_otro_primario_no_agrega_headers(self):
        domain = self.client_a.domains.get()
        domain.is_primary = False
        domain.save()
        resp = self.mw._apply_preview_seo_headers(
            self.rf.get('/'), HttpResponse('ok'), self.client_a, domain)
        self.assertNotIn('X-Robots-Tag', resp)

    def test_preview_con_otro_primario_agrega_noindex_y_canonical(self):
        preview = Domain.objects.create(
            client=self.client_a, domain='preview.test', domain_type='custom',
            is_primary=False, is_active=True)
        resp = self.mw._apply_preview_seo_headers(
            self.rf.get('/x/'), HttpResponse('ok'), self.client_a, preview)
        self.assertEqual(resp['X-Robots-Tag'], 'noindex, nofollow')
        self.assertIn('https://tenant-a.test/x/', resp['Link'])

    def test_preview_response_none_se_devuelve_tal_cual(self):
        self.assertIsNone(self.mw._apply_preview_seo_headers(
            self.rf.get('/'), None, self.client_a, None))

    def test_host_vacio_no_es_dominio_de_sistema(self):
        self.assertFalse(self.mw._is_system_domain(''))

    def test_subdominio_onrender_es_dominio_de_sistema(self):
        self.assertTrue(self.mw._is_system_domain('mi-app.onrender.com'))

    def test_host_desconocido_no_es_dominio_de_sistema(self):
        self.assertFalse(self.mw._is_system_domain('evil.example.org'))
