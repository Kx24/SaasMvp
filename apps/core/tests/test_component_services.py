"""
COMP-01 / BOLT-59: componente `services` compartido.

Un solo `templates/components/services.html`; los archivos de tema son
envoltorios finos o no existen. El HTML que ve el visitante no cambia: cada
render se compara con una fixture capturada antes de generalizar (solo se
toleran diferencias de espacios en blanco, también dentro de `class`, y
comentarios HTML).

`themes/default` tenía un `services.html` que ningún template incluía (su
`home.html` renderiza la sección en línea); se eliminó como código muerto.
"""
import re
from pathlib import Path
from types import SimpleNamespace as NS

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
SHARED = TEMPLATES_DIR / 'components' / 'services.html'
THEME_FILES = {
    theme: TEMPLATES_DIR / 'themes' / theme / 'components' / 'services.html'
    for theme in ('default', 'andesscale', 'servelec')
}
MAX_WRAPPER_LINES = 15
PARAMS = {
    'andesscale': {},
    'servelec': {'variant': 'adaptive',
                 'subtitle': 'Soluciones integrales para darle continuidad a tu proceso.'},
}


def normalize_html(html):
    html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    html = re.sub(r'class="([^"]*)"', lambda m: 'class="%s"' % ' '.join(m.group(1).split()), html)
    html = re.sub(r'\s+', ' ', html)
    return re.sub(r'>\s+<', '><', html).strip()


def svc(i, img, feat):
    return NS(id=i, name='Servicio %s' % i, description='Descripcion %s' % i,
              full_description='Detalle %s' % i, price_text='$%s00' % i, icon='x',
              is_featured=feat,
              image=NS(url='https://img.test/%s.jpg' % i) if img else None)


CASES = {
    'tres': [svc(1, True, True), svc(2, False, False), svc(3, True, False)],
    'cinco': [svc(i, i % 2 == 1, i == 2) for i in range(1, 6)],
    'vacio': [],
}


class ServicesStructureTest(SimpleTestCase):
    def test_shared_component_exists(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/services.html')

    def test_theme_files_are_thin_wrappers(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/services.html')
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue  # borrar el envoltorio también es válido
            with self.subTest(theme=theme):
                text = path.read_text(encoding='utf-8')
                self.assertLessEqual(len(text.strip().splitlines()), MAX_WRAPPER_LINES)
                self.assertIn('components/services.html', text)

    def test_theme_files_do_not_repeat_shared_markup(self):
        self.assertTrue(SHARED.is_file(), 'falta templates/components/services.html')
        shared = {line.strip() for line in SHARED.read_text(encoding='utf-8').splitlines()
                  if len(line.strip()) > 25}
        for theme, path in THEME_FILES.items():
            if not path.exists():
                continue
            with self.subTest(theme=theme):
                own = {line.strip() for line in path.read_text(encoding='utf-8').splitlines()}
                self.assertEqual(shared & own, set())


class ServicesEquivalenceTest(SimpleTestCase):
    def test_render_matches_pre_refactor_fixture(self):
        for theme, params in PARAMS.items():
            for case, services in CASES.items():
                with self.subTest(theme=theme, case=case):
                    # Como lo incluye el home.html de cada tema.
                    html = render_to_string('components/services.html', dict(
                        params, services=services,
                        request=NS(client=NS(slug='x'))))
                    expected = (FIXTURES_DIR / ('services_%s_%s.html' % (theme, case))
                                ).read_text(encoding='utf-8')
                    self.assertEqual(normalize_html(html), normalize_html(expected))
