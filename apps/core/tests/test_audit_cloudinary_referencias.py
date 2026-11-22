"""
DEUDA-17: `audit_cloudinary_assets` solo cuenta como referencia los
CloudinaryField y los CharField que parecen un public_id de Cloudinary.
Cloudinary está parcheado: ninguna llamada de red.
"""
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.tenants.models import Client
from apps.website.models import Service


def audit(**kwargs):
    out = StringIO()
    call_command('audit_cloudinary_assets', '--dry-run', stdout=out, stderr=StringIO(), **kwargs)
    return out.getvalue()


def listed(*ids):
    return {'resources': [{'public_id': i} for i in ids]}


class AuditReferenciasTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name='Acme', slug='acme', company_name='Acme')

    def test_charfield_que_no_es_public_id_no_cuenta(self):
        # El nombre del cliente coincide con un asset: no es una referencia.
        Service.objects.create(client=self.client_obj, name='Acme')
        with patch('cloudinary.api.resources', return_value=listed('Acme')):
            out = audit()
        self.assertIn('Huérfanos detectados: 1', out)

    def test_public_id_vigente_cuenta(self):
        Service.objects.create(client=self.client_obj, name='tenants/acme/gallery/x')
        with patch('cloudinary.api.resources',
                   return_value=listed('tenants/acme/gallery/x')):
            out = audit()
        self.assertIn('Huérfanos detectados: 0', out)

    def test_public_id_legacy_con_slug_cuenta(self):
        Service.objects.create(client=self.client_obj, name='acme/gallery/x')
        with patch('cloudinary.api.resources', return_value=listed('acme/gallery/x')):
            out = audit()
        self.assertIn('Huérfanos detectados: 0', out)
