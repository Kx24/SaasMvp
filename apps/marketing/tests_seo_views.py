"""CONS-13 (parte 2): robots.txt, verificación de Google y sitemaps por tenant."""
from django.test import RequestFactory, TestCase

from apps.marketing.models import SEOConfig
from apps.marketing.sitemaps import TenantSectionsSitemap, TenantStaticSitemap
from apps.marketing.views_sitemap import get_tenant_sitemaps
from apps.tenants.models import Client, Domain


def _tenant(slug):
    client = Client.objects.create(name='T ' + slug, slug=slug, company_name=slug)
    Domain.objects.create(client=client, domain=slug + '.test', is_primary=True,
                          is_active=True, is_verified=True)
    return client


class RobotsTxtTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = _tenant('robots-a')
        cls.b = _tenant('robots-b')

    def test_robots_uses_tenant_primary_domain_and_blocks_private_paths(self):
        resp = self.client.get('/robots.txt', HTTP_HOST='robots-a.test')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp['Content-Type'].startswith('text/plain'))
        body = resp.content.decode()
        self.assertIn('Sitemap: https://robots-a.test/sitemap.xml', body)
        self.assertNotIn('robots-b.test', body)
        for path in ('/dashboard/', '/superadmin/', '/auth/', '/checkout/'):
            self.assertIn('Disallow: ' + path, body)

    def test_robots_without_tenant_falls_back_to_request_host(self):
        resp = self.client.get('/robots.txt', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Sitemap: http://localhost/sitemap.xml', resp.content.decode())

    def test_robots_tenant_without_primary_domain_uses_request_host(self):
        Domain.objects.filter(client=self.a).update(is_primary=False)
        resp = self.client.get('/robots.txt', HTTP_HOST='robots-a.test')
        self.assertIn('Sitemap: http://robots-a.test/sitemap.xml', resp.content.decode())


class GoogleVerificationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = _tenant('verif-a')
        cls.b = _tenant('verif-b')
        SEOConfig.objects.create(client=cls.a, page_key='home', google_verification_file='abc123')
        SEOConfig.objects.create(client=cls.b, page_key='home', google_verification_file='zzz999',
                                 is_active=False)

    def test_serves_content_for_own_code(self):
        resp = self.client.get('/googleabc123.html', HTTP_HOST='verif-a.test')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content.decode(), 'google-site-verification: googleabc123.html')

    def test_code_of_other_tenant_is_404(self):
        resp = self.client.get('/googleabc123.html', HTTP_HOST='verif-b.test')
        self.assertEqual(resp.status_code, 404)

    def test_inactive_config_is_404(self):
        resp = self.client.get('/googlezzz999.html', HTTP_HOST='verif-b.test')
        self.assertEqual(resp.status_code, 404)

    def test_no_tenant_is_404(self):
        resp = self.client.get('/googleabc123.html', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 404)


class SitemapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = _tenant('sitemap-a')

    def test_simple_sitemap_lists_home_with_https(self):
        resp = self.client.get('/sitemap.xml', HTTP_HOST='sitemap-a.test')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('application/xml', resp['Content-Type'])
        self.assertIn('<loc>https://sitemap-a.test/</loc>', resp.content.decode())

    def test_section_sitemap_pages(self):
        resp = self.client.get('/sitemap-pages.xml', HTTP_HOST='sitemap-a.test')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('<loc>https://sitemap-a.test/</loc>', resp.content.decode())

    def test_unknown_section_is_404(self):
        resp = self.client.get('/sitemap-nope.xml', HTTP_HOST='sitemap-a.test')
        self.assertEqual(resp.status_code, 404)

    def test_get_tenant_sitemaps_keys(self):
        request = RequestFactory().get('/')
        request.client = self.a
        self.assertEqual(set(get_tenant_sitemaps(request)), {'pages', 'sections'})

    def test_static_sitemap_lastmod_follows_active_seoconfig(self):
        request = RequestFactory().get('/')
        request.client = self.a
        sm = TenantStaticSitemap(request)
        item = sm.items()[0]
        self.assertEqual(sm.location(item), '/')
        self.assertEqual(sm.priority(item), 1.0)
        self.assertEqual(sm.changefreq(item), 'weekly')
        self.assertIsNone(sm.lastmod(item))
        cfg = SEOConfig.objects.create(client=self.a, page_key='home')
        self.assertEqual(sm.lastmod(item), cfg.updated_at)

    def test_static_sitemap_without_client_has_no_lastmod(self):
        request = RequestFactory().get('/')
        sm = TenantStaticSitemap(request)
        self.assertIsNone(sm.lastmod(sm.items()[0]))

    def test_static_sitemap_location_falls_back_to_root(self):
        request = RequestFactory().get('/')
        self.assertEqual(TenantStaticSitemap(request).location({'url_name': 'no-existe'}), '/')

    def test_sections_sitemap_empty_without_client(self):
        request = RequestFactory().get('/')
        sm = TenantSectionsSitemap(request)
        self.assertEqual(sm.items(), [])
        self.assertEqual(sm.location(object()), '/')
        self.assertIsNone(sm.lastmod(object()))

    def test_sections_sitemap_with_client_never_raises(self):
        request = RequestFactory().get('/')
        request.client = self.a
        self.assertEqual(list(TenantSectionsSitemap(request).items()), [])
