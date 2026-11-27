"""DEUDA-18: el JSON-LD debe leer ClientSettings.contact_phone para `telephone`."""
from django.test import TestCase

from apps.marketing.models import SEOConfig
from apps.tenants.models import Client


class SchemaTelefonoTests(TestCase):
    def _schema(self, slug, phone):
        client = Client.objects.create(name='Tel', slug=slug, company_name='Tel')
        cs = client.settings
        cs.contact_phone = phone
        cs.save()
        client = Client.objects.get(pk=client.pk)
        cfg = SEOConfig.objects.create(client=client, page_key='home', schema_type='LocalBusiness')
        return cfg.get_schema_json()

    def test_con_telefono_incluye_telephone(self):
        schema = self._schema('schema-tel-1', '+56911112222')
        self.assertEqual(schema['telephone'], '+56911112222')

    def test_sin_telefono_omite_la_clave(self):
        schema = self._schema('schema-tel-2', '')
        self.assertNotIn('telephone', schema)
