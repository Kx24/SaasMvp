"""
COMP-01 / BOLT-62: componente `navbar` compartido.

Un solo `templates/components/navbar.html` que despacha según `variant`; el
marcado de cada variante vive en `components/slots/navbar_<variant>.html`.
Los archivos de navbar de cada tema son envoltorios finos o no existen. El
HTML que ve el visitante no cambia: cada render se compara con una fixture
capturada antes de generalizar (solo se toleran diferencias de espacios en
blanco, también dentro de `class`, y comentarios HTML).

Variantes: 'simple' (omitida; el navbar global que usan los tenants sin tema
propio), 'default' (themes/default), 'stripe' (andesscale) y 'servelec'.
"""
import re
from pathlib import Path
from types import SimpleNamespace as NS

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
SHARED = TEMPLATES_DIR / 'components' / 'navbar.html'
THEME_FILES = {
    theme: TEMPLATES_DIR / 'themes' / theme / 'components' / 'navbar.html'
    for theme in ('default', 'andesscale', 'servelec')
}
MAX_WRAPPER_LINES = 15
PARAMS = {
    'simple': {},
    'default': {'variant': 'default'},
    'andesscale': {'variant': 'stripe'},
    'servelec': {'variant': 'servelec'},
}
FULL = NS(logo=NS(url='https://img.test/logo.png'), facebook_url='https://f.test',
          instagram_url='https://i.test', linkedin_url='https://l.test', contact_phone='+5611',
          tagline='Lema', navbar_cta_text='Pide ya', navbar_cta_url='/x/', primary_color='#123456')
ANON = NS(is_authenticated=False)
USER = NS(is_authenticated=True, username='ana', is_superuser=False, is_staff=False)
STAFF = NS(is_authenticated=True, username='root', is_superuser=True, is_staff=True)
CASES = {
    'anon_vacio': (NS(), ANON),
    'anon_completo': (FULL, ANON),
    'usuario_completo': (FULL, USER),
    'staff_vacio': (NS(), STAFF),
}


def normalize_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'class="([^"]*)"', lambda m: 'class="%s"' % ' '.join(m.group(1).split()), html)
    html = re.sub(r'\s+', ' ', html)
    return re.sub(r'>\s+<', '><', html).strip()


class NavbarStructureTest(SimpleTestCase):
    def test_shared_component_exists(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/navbar.html')

    def test_shared_component_dispatches_by_variant(self):
        text = SHARED.read_text(encoding='utf-8')
        self.assertIn('variant', text)
        for variant in ('simple', 'default', 'stripe', 'servelec'):
            with self.subTest(variant=variant):
                self.assertTrue((TEMPLATES_DIR / 'components' / 'slots' / ('navbar_%s.html' % variant)).is_file())

    def test_theme_files_are_thin_wrappers(self):
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue  # borrar el envoltorio también es válido
            with self.subTest(theme=theme):
                text = path.read_text(encoding='utf-8')
                self.assertLessEqual(len(text.strip().splitlines()), MAX_WRAPPER_LINES)
                self.assertIn('components/navbar.html', text)

    def test_theme_files_do_not_repeat_shared_markup(self):
        slots = TEMPLATES_DIR / 'components' / 'slots'
        shared = set()
        for src in [SHARED, *slots.glob('navbar_*.html')]:
            shared |= {line.strip() for line in src.read_text(encoding='utf-8').splitlines()
                       if len(line.strip()) > 25}
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue
            with self.subTest(theme=theme):
                own = {line.strip() for line in path.read_text(encoding='utf-8').splitlines()}
                self.assertEqual(shared & own, set())


class NavbarEquivalenceTest(SimpleTestCase):
    def test_render_matches_pre_refactor_fixture(self):
        for theme, params in PARAMS.items():
            for case, (client_settings, user) in CASES.items():
                with self.subTest(theme=theme, case=case):
                    ctx = dict(params, client=NS(name='Cliente X', settings=client_settings), user=user)
                    html = render_to_string('components/navbar.html', ctx)
                    expected = (FIXTURES_DIR / ('navbar_%s_%s.html' % (theme, case))
                                ).read_text(encoding='utf-8')
                    self.assertEqual(normalize_html(html), normalize_html(expected))

    def test_theme_bases_include_shared_navbar(self):
        for theme in ('default', 'andesscale', 'servelec'):
            with self.subTest(theme=theme):
                base = (TEMPLATES_DIR / 'themes' / theme / 'base.html').read_text(encoding='utf-8')
                self.assertIn('components/navbar.html', base)
                self.assertNotIn('themes/%s/components/navbar.html' % theme, base)
