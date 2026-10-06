"""
Tests de add_preview_domain (#PREV-04).

Convención de tests de la app tenants: archivo PLANO tests_*.py (§0.0 del
kanban agéntico) -- no crear apps/tenants/tests/.
"""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from apps.tenants.models import Client, Domain


def _make_client(slug, with_primary_domain=False):
    client = Client.objects.create(
        name=f'Cliente {slug}', slug=slug, company_name=f'{slug} SpA',
        contact_email=f'{slug}@test.com', is_active=True,
    )
    if with_primary_domain:
        Domain.objects.create(
            client=client, domain=f'{slug}-real.cl',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )
    return client


class AddPreviewDomainCommandTestCase(TestCase):
    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command('add_preview_domain', *args, stdout=out, stderr=out, **kwargs)
        return out.getvalue()

    @override_settings(PREVIEW_DOMAIN='andesscale.com')
    def test_creates_preview_domain_for_client_without_any_domain(self):
        client = _make_client('nuevo-cliente')

        self._run('nuevo-cliente')

        domain = Domain.objects.get(client=client)
        self.assertEqual(domain.domain, 'nuevo-cliente.andesscale.com')
        self.assertTrue(domain.is_preview)
        self.assertTrue(
            domain.is_primary,
            'sin otro dominio, el preview debe quedar como primario (Plan Esencial)',
        )

    @override_settings(PREVIEW_DOMAIN='andesscale.com')
    def test_does_not_override_existing_primary_domain(self):
        _make_client('con-dominio-propio', with_primary_domain=True)

        self._run('con-dominio-propio')

        preview = Domain.objects.get(domain='con-dominio-propio.andesscale.com')
        self.assertFalse(preview.is_primary)
        self.assertTrue(preview.is_preview)

        primary = Domain.objects.get(domain='con-dominio-propio-real.cl')
        self.assertTrue(primary.is_primary, 'el primario existente no debe tocarse')

    @override_settings(PREVIEW_DOMAIN='andesscale.com')
    def test_running_twice_is_idempotent(self):
        client = _make_client('repetido')

        self._run('repetido')
        self._run('repetido')

        self.assertEqual(
            Domain.objects.filter(client=client).count(), 1,
            'correr el comando dos veces no debe duplicar el Domain',
        )

    @override_settings(PREVIEW_DOMAIN='andesscale.com')
    def test_unknown_slug_raises_command_error(self):
        with self.assertRaises(CommandError):
            self._run('no-existe')

    @override_settings(PREVIEW_DOMAIN=None)
    def test_missing_preview_domain_setting_raises_command_error(self):
        _make_client('sin-preview-domain-configurado')

        with self.assertRaises(CommandError):
            self._run('sin-preview-domain-configurado')

    @override_settings(PREVIEW_DOMAIN='andesscale.com', ALLOWED_HOSTS=['*'])
    def test_prints_manual_steps_when_wildcard_not_configured(self):
        _make_client('necesita-pasos-manuales')

        output = self._run('necesita-pasos-manuales')

        self.assertIn('Faltan los pasos manuales', output)

    @override_settings(PREVIEW_DOMAIN='andesscale.com', ALLOWED_HOSTS=['*', '.andesscale.com'])
    def test_skips_manual_steps_when_wildcard_already_configured(self):
        _make_client('ya-tiene-wildcard')

        output = self._run('ya-tiene-wildcard')

        self.assertNotIn('Faltan los pasos manuales', output)
