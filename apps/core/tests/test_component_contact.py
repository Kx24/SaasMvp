"""
COMP-01 / BOLT-60: componente `contact` compartido.

Un solo `templates/components/contact.html`; los archivos de tema son
envoltorios finos o no existen. El HTML que ve el visitante no cambia: cada
render se compara con una fixture capturada antes de generalizar (solo se
toleran diferencias de espacios en blanco, también dentro de `class`, y
comentarios HTML).

`themes/default` no tiene componente de contacto (su `home.html` renderiza la
sección en línea), así que solo andesscale y servelec tienen fixture.
"""
import re
from pathlib import Path
from types import SimpleNamespace as NS

from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
SHARED = TEMPLATES_DIR / 'components' / 'contact.html'
THEME_FILES = {
    theme: TEMPLATES_DIR / 'themes' / theme / 'components' / 'contact.html'
    for theme in ('default', 'andesscale', 'servelec')
}
MAX_WRAPPER_LINES = 15
PARAMS = {
    'andesscale': {},
    'servelec': {'variant': 'servelec'},
}
CASES = {
    'completo': NS(contact_email='a@b.cl', contact_phone='+5611',
                   whatsapp_number='5691', address='Calle 1'),
    'vacio': NS(contact_email='', contact_phone='', whatsapp_number='', address=''),
}


def normalize_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'class="([^"]*)"', lambda m: 'class="%s"' % ' '.join(m.group(1).split()), html)
    html = re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]*', r'\1TOKEN', html)
    html = re.sub(r"(csrfToken:\s*')[^']*", r'\1TOKEN', html)
    html = re.sub(r'\s+', ' ', html)
    return re.sub(r'>\s+<', '><', html).strip()


class ContactStructureTest(SimpleTestCase):
    def test_shared_component_exists(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/contact.html')

    def test_theme_files_are_thin_wrappers(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/contact.html')
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue  # borrar el envoltorio también es válido
            with self.subTest(theme=theme):
                text = path.read_text(encoding='utf-8')
                self.assertLessEqual(len(text.strip().splitlines()), MAX_WRAPPER_LINES)
                self.assertIn('components/contact.html', text)

    def test_theme_files_do_not_repeat_shared_markup(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/contact.html')
        shared = {line.strip() for line in SHARED.read_text(encoding='utf-8').splitlines()
                  if len(line.strip()) > 25}
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue
            with self.subTest(theme=theme):
                own = {line.strip() for line in path.read_text(encoding='utf-8').splitlines()}
                self.assertEqual(shared & own, set())


class ContactEquivalenceTest(TestCase):
    def test_render_matches_pre_refactor_fixture(self):
        for theme, params in PARAMS.items():
            for case, client_settings in CASES.items():
                with self.subTest(theme=theme, case=case):
                    request = RequestFactory().get('/')
                    request.client = None
                    client = NS(slug='x', settings=client_settings, name='X', id=1)
                    html = render_to_string(
                        'components/contact.html', dict(params, client=client), request=request)
                    expected = (FIXTURES_DIR / ('contact_%s_%s.html' % (theme, case))
                                ).read_text(encoding='utf-8')
                    self.assertEqual(normalize_html(html), normalize_html(expected))
