"""
COMP-01 / BOLT-63: componentes `hero_ctas` y `hero_overlay_theme` compartidos.

Un solo `templates/components/hero_ctas.html` (y `hero_overlay_theme.html`);
los temas ya no tienen archivo propio (un `themes/<tema>/components/hero_ctas.html`
sombrearía al compartido por el TenantTemplateLoader). Las variantes viven en
`components/slots/<nombre>_<variante>.html`, que solo fijan parámetros. El HTML
no cambia: cada render se compara con una fixture capturada antes de generalizar
(solo se toleran diferencias de espacios en blanco).
"""
import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
MAX_WRAPPER_LINES = 15
COMPONENTS = ('hero_ctas', 'hero_overlay_theme')
THEMES = ('default', 'andesscale', 'servelec')
# (componente, tema) -> plantilla que consume el hero de ese tema
RENDER = {
    ('hero_ctas', 'default'): 'components/slots/hero_ctas_default.html',
    ('hero_ctas', 'servelec'): 'components/slots/hero_ctas_servelec.html',
    ('hero_overlay_theme', 'default'): 'components/hero_overlay_theme.html',
    ('hero_overlay_theme', 'servelec'): 'components/slots/hero_overlay_theme_servelec.html',
}


def normalize_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'\s+', ' ', html)
    return re.sub(r'>\s+<', '><', html).strip()


class HeroComponentsStructureTest(SimpleTestCase):
    def test_shared_components_exist(self):
        for name in COMPONENTS:
            with self.subTest(component=name):
                self.assertTrue((TEMPLATES_DIR / 'components' / f'{name}.html').is_file())

    def test_theme_files_are_thin_wrappers(self):
        for name in COMPONENTS:
            self.assertTrue((TEMPLATES_DIR / 'components' / f'{name}.html').is_file())
            for theme in THEMES:
                path = TEMPLATES_DIR / 'themes' / theme / 'components' / f'{name}.html'
                if not path.exists():
                    continue
                with self.subTest(component=name, theme=theme):
                    text = path.read_text(encoding='utf-8')
                    self.assertLessEqual(len(text.strip().splitlines()), MAX_WRAPPER_LINES)
                    self.assertIn(f'components/{name}.html', text)

    def test_theme_files_do_not_repeat_shared_markup(self):
        for name in COMPONENTS:
            shared_path = TEMPLATES_DIR / 'components' / f'{name}.html'
            self.assertTrue(shared_path.is_file())
            shared = {line.strip() for line in shared_path.read_text(encoding='utf-8').splitlines()
                      if len(line.strip()) > 25}
            for theme in THEMES:
                path = TEMPLATES_DIR / 'themes' / theme / 'components' / f'{name}.html'
                if not path.exists():
                    continue
                with self.subTest(component=name, theme=theme):
                    own = {line.strip() for line in path.read_text(encoding='utf-8').splitlines()}
                    self.assertEqual(shared & own, set())


class HeroComponentsEquivalenceTest(SimpleTestCase):
    def test_render_matches_pre_refactor_fixture(self):
        for (name, theme), template in RENDER.items():
            with self.subTest(component=name, theme=theme):
                html = render_to_string(template)
                expected = (FIXTURES_DIR / f'{name}_{theme}.html').read_text(encoding='utf-8')
                self.assertEqual(normalize_html(html), normalize_html(expected))

    def test_secondary_button_only_renders_with_text(self):
        html = render_to_string('components/hero_ctas.html', {'primary_text': 'Solo uno'})
        self.assertIn('Solo uno', html)
        self.assertNotIn('href="#servicios"', html)
