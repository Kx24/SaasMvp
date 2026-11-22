"""BOLT-78 (SEC-19): tenant_static y get_tenant_media_url rechazan rutas que salen del tenant."""
import tempfile
from pathlib import Path
from types import SimpleNamespace

from django.template import Context, Template
from django.test import SimpleTestCase, override_settings


def render(source, **ctx):
    return Template('{% load tenant_tags %}' + source).render(Context(ctx))


class TenantTagsTraversalTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.media = Path(self.tmp.name)
        (self.media / 'tenants' / 'acme').mkdir(parents=True)
        (self.media / 'tenants' / 'acme' / 'logo.png').write_bytes(b'x')
        (self.media / 'tenants' / 'otro').mkdir(parents=True)
        (self.media / 'tenants' / 'otro' / 'x.png').write_bytes(b'x')
        (self.media / 'secreto.txt').write_bytes(b'x')
        self.acme = SimpleNamespace(slug='acme')

    def r(self, source):
        with override_settings(MEDIA_ROOT=str(self.media), MEDIA_URL='/m/', STATIC_URL='/s/'):
            return render(source, client=self.acme)

    def test_tenant_static_rechaza_traversal(self):
        self.assertEqual(self.r("{% tenant_static '../otro/x.png' %}"), '/s/../otro/x.png')
        self.assertEqual(self.r("{% tenant_static '../../secreto.txt' %}"), '/s/../../secreto.txt')

    def test_tenant_static_rechaza_ruta_absoluta(self):
        absoluta = str(self.media / 'secreto.txt')
        out = self.r("{% tenant_static ruta %}".replace('ruta', repr(absoluta)))
        self.assertTrue(out.startswith('/s/'))

    def test_get_tenant_media_url_rechaza_traversal(self):
        self.assertEqual(self.r("{% get_tenant_media_url '../otro/x.png' %}"), '')
        self.assertEqual(self.r("{% get_tenant_media_url '../../secreto.txt' %}"), '')

    def test_get_tenant_media_url_rechaza_ruta_absoluta(self):
        absoluta = str(self.media / 'secreto.txt')
        self.assertEqual(self.r("{% get_tenant_media_url " + repr(absoluta) + " %}"), '')

    def test_archivo_legitimo_sigue_funcionando(self):
        self.assertEqual(self.r("{% tenant_static 'logo.png' %}"), '/m/tenants/acme/logo.png')
        self.assertEqual(self.r("{% get_tenant_media_url 'logo.png' %}"), '/m/tenants/acme/logo.png')
