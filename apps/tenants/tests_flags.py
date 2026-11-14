"""CONS-05 / BOLT-18: los flags sin módulo (blog, testimonios) ya no existen."""
from io import StringIO

from django.core.exceptions import FieldDoesNotExist
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.tenants.models import Client, ClientSettings, Domain


class FlagsSinModuloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.host = 'flags-test.example.com'
        cls.client_obj = Client.objects.create(
            name='Flags', slug='flags-test', contact_email='c@flags-test.example.com',
            template='themes/default',
        )
        Domain.objects.create(
            client=cls.client_obj, domain=cls.host, domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

    def test_campos_eliminados_del_modelo(self):
        for name in ('enable_blog', 'enable_testimonials'):
            with self.assertRaises(FieldDoesNotExist):
                ClientSettings._meta.get_field(name)

    def test_home_default_sin_enlace_testimonios(self):
        response = self.client.get(reverse('home'), HTTP_HOST=self.host)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '#testimonios')
        self.assertNotContains(response, 'Testimonios')

    def test_list_tenants_corre(self):
        call_command('list_tenants', stdout=StringIO())
