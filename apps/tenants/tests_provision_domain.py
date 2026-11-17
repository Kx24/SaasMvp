"""FLOW-04 (BOLT-44): provision_tenant siempre deja un Domain primario
y no avisa sobre la carpeta obsoleta `_default`."""
from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from apps.tenants.models import Client, Domain


def _run(slug, *extra):
    out = StringIO()
    call_command(
        'provision_tenant', slug, '--industry=servicios_profesionales',
        '--theme=themes/default', *extra, stdout=out,
    )
    return out.getvalue()


class ProvisionDomainTests(TestCase):
    @override_settings(DEBUG=False, PREVIEW_DOMAIN='preview.example.test')
    def test_sin_domain_crea_primario_desde_preview_domain(self):
        out = _run('flow04-a')
        client = Client.objects.get(slug='flow04-a')
        doms = Domain.objects.filter(client=client)
        self.assertEqual(doms.count(), 1)
        self.assertTrue(doms.get().is_primary)
        self.assertEqual(doms.get().domain, 'flow04-a.preview.example.test')
        self.assertNotIn('no existe', out)
        self.assertNotIn('_default', out)

    @override_settings(DEBUG=True)
    def test_en_debug_usa_localhost(self):
        _run('flow04-b')
        d = Domain.objects.get(client__slug='flow04-b')
        self.assertEqual((d.domain, d.is_primary), ('flow04-b.localhost', True))

    @override_settings(DEBUG=False, PREVIEW_DOMAIN=None)
    def test_sin_fuente_de_dominio_falla_sin_crear_nada(self):
        with self.assertRaises(CommandError):
            _run('flow04-c')
        self.assertFalse(Client.objects.filter(slug='flow04-c').exists())

    def test_domain_explicito_sigue_funcionando(self):
        _run('flow04-d', '--domain=flow04d.example.test')
        prim = Domain.objects.filter(client__slug='flow04-d', is_primary=True)
        self.assertEqual(prim.count(), 1)
        self.assertEqual(prim.get().domain, 'flow04d.example.test')

    @override_settings(DEBUG=True)
    def test_check_tenant_setup_no_falla_por_dominio(self):
        _run('flow04-e')
        out = StringIO()
        call_command('check_tenant_setup', 'flow04-e', '--warn-only', stdout=out)
        text = out.getvalue()
        self.assertIn('[OK]   Dominio principal: flow04-e.localhost', text)
        self.assertNotIn('ningún dominio', text)
