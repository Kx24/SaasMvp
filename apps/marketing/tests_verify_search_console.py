"""CONS-13 (parte 1): cobertura de `verify_search_console`."""
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.marketing.models import SEOConfig
from apps.tenants.models import Client, Domain


def run(**kwargs):
    out = StringIO()
    call_command('verify_search_console', stdout=out, **kwargs)
    return out.getvalue()


class VerifySearchConsoleTests(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(name='Acme', slug='acme', company_name='Acme')
        Domain.objects.create(client=self.client_obj, domain='acme.test', is_primary=True)

    def test_requires_domain_or_all(self):
        with self.assertRaises(CommandError):
            call_command('verify_search_console', stdout=StringIO())

    def test_unknown_domain_raises(self):
        with self.assertRaises(CommandError):
            run(domain='nope.test')

    def test_without_seoconfig_warns(self):
        out = run(domain='acme.test')
        self.assertIn('Dominio primario: acme.test', out)
        self.assertIn("Sin SEOConfig para 'home'", out)

    def test_without_primary_domain_warns(self):
        Domain.objects.filter(client=self.client_obj).update(is_primary=False)
        out = run(**{'all': True})
        self.assertIn('Sin dominio primario', out)

    def test_seoconfig_without_any_method_is_red(self):
        SEOConfig.objects.create(client=self.client_obj, page_key='home')
        out = run(domain='acme.test')
        self.assertIn('Meta tag: vacío', out)
        self.assertIn('Archivo HTML: vacío', out)
        self.assertIn('Configura al menos un método', out)

    def test_seoconfig_with_both_methods_is_ready(self):
        SEOConfig.objects.create(
            client=self.client_obj, page_key='home',
            google_site_verification='abcdefghijklmnopqrstuvwxyz',
            google_verification_file='abc123')
        out = run(domain='acme.test')
        self.assertIn('Meta tag: configurado', out)
        self.assertIn('https://acme.test/googleabc123.html', out)
        self.assertIn('LISTO para verificar', out)
