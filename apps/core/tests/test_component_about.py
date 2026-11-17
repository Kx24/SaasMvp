"""
COMP-01 / BOLT-58: componente `about` compartido.

Un solo `templates/components/about.html`; los archivos de tema son
envoltorios finos o no existen. El HTML que ve el visitante no cambia: cada
render se compara con una fixture capturada antes de generalizar (solo se
toleran diferencias de espacios en blanco y comentarios HTML).

`themes/default` no tenía componente `about` (su archivo estaba vacío y
`home.html` renderiza la sección en línea), así que no participa.
"""
import re
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
SHARED = TEMPLATES_DIR / 'components' / 'about.html'
THEME_FILES = {
    'default': TEMPLATES_DIR / 'themes' / 'default' / 'components' / 'about.html',
    'andesscale': TEMPLATES_DIR / 'themes' / 'andesscale' / 'components' / 'about.html',
    'servelec': TEMPLATES_DIR / 'themes' / 'servelec' / 'components' / 'about.html',
}
MAX_WRAPPER_LINES = 15
VARIANTS = {'andesscale': 'stripe', 'servelec': 'blocks'}


def normalize_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'\s+', ' ', html)
    return re.sub(r'>\s+<', '><', html).strip()


def fake_about(with_image):
    return SimpleNamespace(
        is_active=True, title='Quienes somos', subtitle='Un subtitulo',
        description='Linea uno\n\nLinea dos',
        image=SimpleNamespace(url='https://img.test/a.jpg') if with_image else None)


def render_about(theme, with_image):
    # Como lo incluye el home.html de cada tema (sin archivo propio del tema).
    with mock.patch('apps.website.templatetags.website_tags.Section.objects') as objects:
        objects.get.return_value = fake_about(with_image)
        return render_to_string('components/about.html', {
            'request': SimpleNamespace(client=SimpleNamespace(slug='x')),
            'client': SimpleNamespace(name='Acme'),
            'variant': VARIANTS[theme],
        })


class AboutStructureTest(SimpleTestCase):
    def test_shared_component_exists(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/about.html')

    def test_theme_files_are_thin_wrappers(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/about.html')
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue  # borrar el envoltorio también es válido
            with self.subTest(theme=theme):
                text = path.read_text(encoding='utf-8')
                self.assertLessEqual(len(text.strip().splitlines()), MAX_WRAPPER_LINES)
                self.assertIn('components/about.html', text)

    def test_theme_files_do_not_repeat_shared_markup(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/about.html')
        shared = {line.strip() for line in SHARED.read_text(encoding='utf-8').splitlines()
                  if len(line.strip()) > 25}
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue
            with self.subTest(theme=theme):
                own = {line.strip() for line in path.read_text(encoding='utf-8').splitlines()}
                self.assertEqual(shared & own, set())


class AboutEquivalenceTest(SimpleTestCase):
    def test_render_matches_pre_refactor_fixture(self):
        for theme in VARIANTS:
            for with_image in (True, False):
                suffix = 'con' if with_image else 'sin'
                with self.subTest(theme=theme, image=with_image):
                    expected = (FIXTURES_DIR / f'about_{theme}_{suffix}_imagen.html'
                                ).read_text(encoding='utf-8')
                    self.assertEqual(normalize_html(render_about(theme, with_image)),
                                     normalize_html(expected))
