"""DEUDA-16: el sitemap ya no expone secciones (no son páginas con URL propia)."""
from django.test import RequestFactory, TestCase

from apps.marketing import sitemaps
from apps.marketing.views_sitemap import get_tenant_sitemaps
from apps.tenants.models import Client, Domain


class SitemapSinSeccionesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(name='T ns', slug='nosec', company_name='nosec')
        Domain.objects.create(client=cls.tenant, domain='nosec.test', is_primary=True,
                              is_active=True, is_verified=True)

    def test_get_tenant_sitemaps_solo_pages(self):
        request = RequestFactory().get('/')
        request.client = self.tenant
        self.assertEqual(set(get_tenant_sitemaps(request)), {'pages'})

    def test_modulo_no_expone_tenant_sections_sitemap(self):
        self.assertFalse(hasattr(sitemaps, 'TenantSectionsSitemap'))

    def test_sitemap_sections_xml_es_404(self):
        resp = self.client.get('/sitemap-sections.xml', HTTP_HOST='nosec.test')
        self.assertEqual(resp.status_code, 404)
