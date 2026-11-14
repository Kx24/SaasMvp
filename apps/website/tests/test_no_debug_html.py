"""
SEC-17 / BOLT-17: el HTML público no debe exponer comentarios `<!-- DEBUG`
(modo del componente, cantidad de items, nombre del cliente, URLs de fondo).
"""
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from apps.website.tests.test_home_render import _HomeRenderMixin


class NoDebugCommentsInTemplatesTest(TestCase):
    def test_no_template_contains_debug_comment(self):
        found = []
        for path in Path(settings.BASE_DIR, 'templates').rglob('*.html'):
            text = path.read_text(encoding='utf-8', errors='ignore')
            for lineno, line in enumerate(text.splitlines(), start=1):
                if '<!-- DEBUG' in line:
                    found.append(f'{path.relative_to(settings.BASE_DIR)}:{lineno}')
        self.assertEqual(found, [], f'Comentarios DEBUG en templates: {found}')


class _NoDebugRender(_HomeRenderMixin):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = cls._make_client(cls.slug, cls.host, cls.template)
        cls._add_full_content(cls.client_obj)

    def test_home_html_has_no_debug(self):
        response = self._get_home(self.host)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'DEBUG')


class DefaultThemeNoDebugTest(_NoDebugRender, TestCase):
    slug, template, host = 'nodebug-default', 'themes/default', 'nodebugdefault.test'


class ServelecThemeNoDebugTest(_NoDebugRender, TestCase):
    slug, template, host = 'nodebug-servelec', 'themes/servelec', 'nodebugservelec.test'
