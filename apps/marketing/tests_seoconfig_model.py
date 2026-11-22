"""Comportamiento de los métodos de SEOConfig (fallbacks, schema.org, URL de verificación)."""
from django.test import TestCase

from apps.marketing.models import SEOConfig
from apps.tenants.models import Client, Domain


class SEOConfigMethodsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = Client.objects.create(name='Acme', slug='seo-model', company_name='Acme')

    def _cfg(self, **kw):
        return SEOConfig.objects.create(client=self.client_obj, page_key=kw.pop('page_key', 'home'), **kw)

    def test_title_falls_back_to_client_name(self):
        self.assertEqual(self._cfg().get_title(), 'Acme')
        self.assertEqual(self._cfg(page_key='x', title='Mi título').get_title(), 'Mi título')

    def test_og_title_and_description_fallbacks(self):
        cfg = self._cfg(title='T', meta_description='D')
        self.assertEqual(cfg.get_og_title(), 'T')
        self.assertEqual(cfg.get_og_description(), 'D')
        cfg2 = self._cfg(page_key='y', og_title='OG', og_description='OGD', meta_description='D')
        self.assertEqual(cfg2.get_og_title(), 'OG')
        self.assertEqual(cfg2.get_og_description(), 'OGD')

    def test_has_schema(self):
        self.assertFalse(self._cfg().has_schema())
        self.assertTrue(self._cfg(page_key='a', schema_type='Organization').has_schema())
        self.assertTrue(self._cfg(page_key='b', schema_json={'a': 1}).has_schema())

    def test_verification_file_url(self):
        self.assertIsNone(self._cfg().get_verification_file_url())
        cfg = self._cfg(page_key='v', google_verification_file='abc')
        self.assertEqual(cfg.get_verification_file_url(), '/googleabc.html')

    def test_get_schema_json_custom_wins_and_none_without_type(self):
        self.assertEqual(self._cfg(schema_json={'k': 'v'}).get_schema_json(), {'k': 'v'})
        self.assertIsNone(self._cfg(page_key='n').get_schema_json())

    def test_get_schema_json_generated_with_domain_and_description(self):
        Domain.objects.create(client=self.client_obj, domain='acme.test', is_primary=True,
                              is_active=True, is_verified=True)
        cs = self.client_obj.settings
        cs.description = 'Desc'
        cs.save()
        client = Client.objects.get(pk=self.client_obj.pk)
        cfg = SEOConfig.objects.create(client=client, page_key='s', schema_type='LocalBusiness')
        schema = cfg.get_schema_json()
        self.assertEqual(schema['@type'], 'LocalBusiness')
        self.assertEqual(schema['name'], 'Acme')
        self.assertEqual(schema['url'], 'https://acme.test')
        self.assertNotIn('telephone', schema)
        self.assertNotIn('address', schema)
        self.assertEqual(schema['description'], 'Desc')
