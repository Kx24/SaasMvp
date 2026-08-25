"""
Guardia del contrato de tokens CSS (docs/design-system.md §1) — BOLT-06.

Clase de bug: un template consume var(--primary) pero el :root del tema
solo define --color-primary. CSS inválido no lanza error — la propiedad
se descarta en silencio y el componente pierde el color de marca (114
usos rotos encontrados al auditar el hero de Rancho Cachimba). Nada lo
verificaba: este test estático (sobre el código fuente, sin runtime —
mismo patrón que el guard de CLOUDINARY_PRESETS de #AUD-10) exige que
todo var(--x) consumido SIN fallback esté definido en el tema.

Reglas del contrato:
- var(--x, fallback) NO es violación: su comportamiento está definido
  aunque --x no exista (patrón legítimo de slots opcionales, p. ej.
  --hero-bg en components/media_item.html).
- --tw-* (variables generadas por Tailwind) están whitelisteadas.
- templates/components/ compartidos se validan contra la INTERSECCIÓN
  de los contratos de todos los temas (deben funcionar en cualquiera).
"""
import re
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

TEMPLATES_DIR = Path(settings.BASE_DIR) / 'templates'

THEME_DIRS = {
    'andesscale': TEMPLATES_DIR / 'andesscale',
    'servelec': TEMPLATES_DIR / 'servelec',
    'themes/default': TEMPLATES_DIR / 'themes' / 'default',
    'themes/electricidad': TEMPLATES_DIR / 'themes' / 'electricidad',
}
SHARED_COMPONENTS_DIR = TEMPLATES_DIR / 'components'

DEFINITION_RE = re.compile(r'(--[a-zA-Z0-9_-]+)\s*:')
# var(--x) — captura el nombre y si viene o no con fallback (coma)
CONSUMPTION_RE = re.compile(r'var\(\s*(--[a-zA-Z0-9_-]+)\s*(,)?')
WHITELIST_PREFIXES = ('--tw-',)


def collect_defined_tokens(theme_dir):
    """Custom properties definidas (`--x:`) en cualquier .html del tema."""
    defined = set()
    for html in Path(theme_dir).rglob('*.html'):
        defined.update(DEFINITION_RE.findall(html.read_text(encoding='utf-8')))
    return defined


def collect_violations(scan_dir, defined_tokens):
    """
    var(--x) consumidos SIN fallback cuyo token no está definido ni
    whitelisteado. Devuelve [(ruta_relativa, token), ...].
    """
    violations = []
    scan_dir = Path(scan_dir)
    for html in sorted(scan_dir.rglob('*.html')):
        content = html.read_text(encoding='utf-8')
        try:
            label = str(html.relative_to(TEMPLATES_DIR))
        except ValueError:  # fixture sintético fuera de templates/
            label = str(html.relative_to(scan_dir))
        for token, has_fallback in CONSUMPTION_RE.findall(content):
            if has_fallback:
                continue
            if token.startswith(WHITELIST_PREFIXES):
                continue
            if token not in defined_tokens:
                violations.append((label, token))
    return violations


class ThemeTokenContractTestCase(SimpleTestCase):
    def test_every_theme_consumes_only_defined_tokens(self):
        for theme_name, theme_dir in THEME_DIRS.items():
            with self.subTest(theme=theme_name):
                self.assertTrue(theme_dir.is_dir(), f'{theme_dir} no existe')
                defined = collect_defined_tokens(theme_dir)
                violations = collect_violations(theme_dir, defined)
                self.assertEqual(
                    violations, [],
                    f'Tokens consumidos sin definición en el tema {theme_name} '
                    f'(CSS inválido silencioso): {violations}',
                )

    def test_shared_components_respect_contract_intersection(self):
        """Los componentes compartidos corren bajo cualquier tema: solo
        pueden consumir (sin fallback) tokens que TODOS los temas definan."""
        contracts = [collect_defined_tokens(d) for d in THEME_DIRS.values()]
        intersection = set.intersection(*contracts)
        violations = collect_violations(SHARED_COMPONENTS_DIR, intersection)
        self.assertEqual(
            violations, [],
            'Tokens fuera de la intersección de contratos en components/ '
            f'compartidos: {violations}',
        )

    def test_harness_detects_synthetic_violation(self):
        """Rojo del arnés con fixture inválido (no rompiendo un tema real):
        un tema que define --color-primary pero consume var(--primary)."""
        with tempfile.TemporaryDirectory() as tmp:
            fake_theme = Path(tmp) / 'fake-theme'
            fake_theme.mkdir()
            (fake_theme / 'base.html').write_text(
                '<style>:root { --color-primary: #123456; }</style>',
                encoding='utf-8',
            )
            (fake_theme / 'hero.html').write_text(
                '<div style="color: var(--primary);">'
                '<span style="background: var(--color-primary);"></span>'
                '<span style="border-color: var(--accent, #fff);"></span>'
                '<span style="opacity: var(--tw-bg-opacity);"></span>'
                '</div>',
                encoding='utf-8',
            )

            defined = collect_defined_tokens(fake_theme)
            violations = collect_violations(fake_theme, defined)

            # Solo var(--primary) es violación: --color-primary está definido,
            # --accent lleva fallback y --tw-* está whitelisteado.
            self.assertEqual(violations, [('hero.html', '--primary')])
