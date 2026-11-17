"""
COMP-01 / BOLT-61: componente `footer` compartido.

Un solo `templates/components/footer.html`; los archivos de tema son
envoltorios finos o no existen. El HTML que ve el visitante no cambia: cada
render se compara con una fixture capturada antes de generalizar (solo se
toleran diferencias de espacios en blanco, también dentro de `class`, y
comentarios HTML).

`themes/default/components/footer.html` estaba vacío y sombreaba al footer
global, así que los tenants con tema base renderizaban un footer en blanco.
Su fixture captura el footer genérico global (la intención de `base.html`);
esa es la única diferencia visible y queda declarada en la card.
"""
import re
from datetime import date
from pathlib import Path
from types import SimpleNamespace as NS

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
SHARED = TEMPLATES_DIR / 'components' / 'footer.html'
THEME_FILES = {
    theme: TEMPLATES_DIR / 'themes' / theme / 'components' / 'footer.html'
    for theme in ('default', 'andesscale', 'servelec')
}
MAX_WRAPPER_LINES = 15
PARAMS = {
    'default': {},
    'andesscale': {'variant': 'stripe'},
    'servelec': {'variant': 'servelec'},
}
FULL = NS(logo=NS(url='https://img.test/logo.png'), logo_footer=NS(url='https://img.test/logo-footer.png'),
          linkedin_url='https://l.test', instagram_url='https://i.test', facebook_url='https://f.test',
          twitter_url='https://t.test', contact_email='a@b.cl', contact_phone='+5611',
          whatsapp_number='5691', description='Desc propia', company_name='Empresa SA')
CASES = {
    'completo': NS(name='Cliente X', settings=FULL),
    'vacio': NS(name='Cliente X', settings=NS()),
}


def normalize_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'class="([^"]*)"', lambda m: 'class="%s"' % ' '.join(m.group(1).split()), html)
    html = html.replace('© %s' % date.today().year, '© YEAR')
    html = re.sub(r'\s+', ' ', html)
    return re.sub(r'>\s+<', '><', html).strip()


class FooterStructureTest(SimpleTestCase):
    def test_shared_component_exists(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/footer.html')

    def test_theme_files_are_thin_wrappers(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/footer.html')
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue  # borrar el envoltorio también es válido
            with self.subTest(theme=theme):
                text = path.read_text(encoding='utf-8')
                self.assertLessEqual(len(text.strip().splitlines()), MAX_WRAPPER_LINES)
                self.assertIn('components/footer.html', text)

    def test_theme_files_do_not_repeat_shared_markup(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/footer.html')
        shared = {line.strip() for line in SHARED.read_text(encoding='utf-8').splitlines()
                  if len(line.strip()) > 25}
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue
            with self.subTest(theme=theme):
                own = {line.strip() for line in path.read_text(encoding='utf-8').splitlines()}
                self.assertEqual(shared & own, set())


class FooterEquivalenceTest(SimpleTestCase):
    def test_render_matches_pre_refactor_fixture(self):
        for theme, params in PARAMS.items():
            for case, client in CASES.items():
                with self.subTest(theme=theme, case=case):
                    html = render_to_string('components/footer.html', dict(params, client=client))
                    expected = (FIXTURES_DIR / ('footer_%s_%s.html' % (theme, case))
                                ).read_text(encoding='utf-8')
                    self.assertEqual(normalize_html(html), normalize_html(expected))

    def test_theme_bases_include_shared_footer(self):
        for theme in PARAMS:
            with self.subTest(theme=theme):
                base = (TEMPLATES_DIR / 'themes' / theme / 'base.html').read_text(encoding='utf-8')
                self.assertIn('components/footer.html', base)
                self.assertNotIn('themes/%s/components/footer.html' % theme, base)

    def test_privacy_link_kept_in_andesscale(self):
        html = render_to_string('components/footer.html', {'variant': 'stripe', 'client': CASES['vacio']})
        self.assertIn('href="/privacidad/"', html)
