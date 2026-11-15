"""LEY-01 (1/2): página pública /privacidad/ con versión vigente."""
import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.tenants.models import Client, Domain

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'


def _make_tenant(slug, name, host, template='themes/default', email='privacidad@example.test'):
    client = Client.objects.create(
        name=name, slug=slug, template=template, contact_email=email,
    )
    Domain.objects.create(
        client=client, domain=host, domain_type='custom',
        is_primary=True, is_active=True, is_verified=True,
    )
    cs = client.settings
    cs.contact_email = email
    cs.save()
    return client


class PrivacyPolicyTenantTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.default = _make_tenant('priv-default', 'Acme Privada SpA', 'priv-default.test')
        cls.servelec = _make_tenant(
            'priv-servelec', 'Servelec Privada Ltda', 'priv-servelec.test',
            template='themes/servelec', email='datos@servelec.test',
        )

    def _get(self, host):
        return self.client.get(reverse('privacy_policy'), HTTP_HOST=host)

    def test_tenant_policy_content_in_both_themes(self):
        for tenant, host in ((self.default, 'priv-default.test'), (self.servelec, 'priv-servelec.test')):
            with self.subTest(theme=tenant.template):
                response = self._get(host)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, tenant.company_name)
                self.assertContains(response, tenant.settings.contact_email)
                self.assertContains(response, 'Agencia de Protección de Datos Personales')
                self.assertContains(response, '30 días corridos')
                for right in ('acceder', 'rectificarlos', 'suprimirlos', 'oponerte', 'portabilidad'):
                    self.assertContains(response, right)
                self.assertContains(response, settings.PRIVACY_POLICY_VERSION)
                self.assertContains(response, f'{settings.CONTACT_MAX_RETENTION_DAYS} días')
                self.assertNotContains(response, 'MercadoPago')

    def test_platform_tenant_gets_platform_body(self):
        _make_tenant(settings.PLATFORM_TENANT_SLUG, 'AndesScale', 'plataforma-priv.test')
        response = self._get('plataforma-priv.test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'MercadoPago')
        self.assertNotContains(response, 'encargado del tratamiento')

    def test_system_domain_without_client_is_404(self):
        response = self.client.get(reverse('privacy_policy'), HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 404)

    def test_version_comes_from_settings(self):
        with override_settings(PRIVACY_POLICY_VERSION='X-TEST-9'):
            response = self._get('priv-default.test')
        self.assertContains(response, 'X-TEST-9')

    def test_no_template_comments_or_todo_leak(self):
        _make_tenant(settings.PLATFORM_TENANT_SLUG, 'AndesScale', 'plataforma-priv2.test')
        for host in ('priv-default.test', 'plataforma-priv2.test'):
            html = self._get(host).content.decode()
            for marker in ('{#', '#}', 'TODO', 'REVISAR', '{% comment'):
                self.assertNotIn(marker, html, f'{marker} visible en {host}')


class PrivacyLinksStaticTests(SimpleTestCase):
    def test_no_dead_privacy_links(self):
        offenders = []
        for path in TEMPLATES_DIR.rglob('*.html'):
            for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                if 'href="#"' in line and 'rivacidad' in line:
                    offenders.append(f'{path.relative_to(TEMPLATES_DIR)}:{n}')
        self.assertEqual(offenders, [])

    def test_footers_mentioning_privacy_link_to_policy(self):
        for path in TEMPLATES_DIR.rglob('footer.html'):
            for line in path.read_text(encoding='utf-8').splitlines():
                if re.search(r'>\s*Privacidad\s*<', line):
                    self.assertIn("{% url 'privacy_policy' %}", line, str(path))
