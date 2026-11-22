"""
COMP-01 / BOLT-57: componente `cta` compartido.

Un solo `templates/components/cta.html`; los archivos de tema son
envoltorios finos. El HTML que ve el visitante no cambia: cada render se
compara con una fixture capturada antes de generalizar (solo se toleran
diferencias de espacios en blanco y comentarios HTML).
"""
import re
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
SHARED = TEMPLATES_DIR / 'components' / 'cta.html'
THEME_FILES = {
    'andesscale': TEMPLATES_DIR / 'themes' / 'andesscale' / 'components' / 'cta.html',
    'servelec': TEMPLATES_DIR / 'themes' / 'servelec' / 'components' / 'cta.html',
}
MAX_WRAPPER_LINES = 15


def normalize_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'\s+', ' ', html)
    return re.sub(r'>\s+<', '><', html).strip()


VARIANTS = {'andesscale': 'orbs', 'servelec': 'glow'}


def render_cta(theme, phone=''):
    # Como lo incluye el home.html de cada tema (sin archivo propio del tema).
    client = SimpleNamespace(settings=SimpleNamespace(contact_phone=phone))
    return render_to_string('components/cta.html',
                            {'client': client, 'variant': VARIANTS[theme]})


CASES = {
    'andesscale': ('andesscale', ''),
    'servelec_sin_telefono': ('servelec', ''),
    'servelec_con_telefono': ('servelec', '+56912345678'),
}


class CtaStructureTest(SimpleTestCase):
    def test_shared_component_exists(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/cta.html')

    def test_theme_files_are_thin_wrappers(self):
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue  # borrar el envoltorio también es válido
            with self.subTest(theme=theme):
                text = path.read_text(encoding='utf-8')
                self.assertLessEqual(len(text.strip().splitlines()), MAX_WRAPPER_LINES)
                self.assertIn('components/cta.html', text)

    def test_theme_files_do_not_repeat_shared_markup(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/cta.html')
        shared = {line.strip() for line in SHARED.read_text(encoding='utf-8').splitlines()
                  if len(line.strip()) > 25}
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue
            with self.subTest(theme=theme):
                own = {line.strip() for line in path.read_text(encoding='utf-8').splitlines()}
                self.assertEqual(shared & own, set())


class CtaEquivalenceTest(SimpleTestCase):
    def test_render_matches_pre_refactor_fixture(self):
        for name, (theme, phone) in CASES.items():
            with self.subTest(case=name):
                expected = (FIXTURES_DIR / f'cta_{name}.html').read_text(encoding='utf-8')
                self.assertEqual(normalize_html(render_cta(theme, phone)),
                                 normalize_html(expected))
