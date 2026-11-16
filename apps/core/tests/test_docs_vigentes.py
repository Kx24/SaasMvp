import re
from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Fuera de alcance: lo histórico, los docs del agente y dependencias/entornos.
EXCLUIDOS = {
    'historico', 'docs', '.claude', '.git', '.idea', 'env', 'venv',
    'node_modules', 'htmlcov', 'staticfiles',
}
PROHIBIDOS = ('OrderProcessor', 'cloudinary_settings', 'supabase')


def _md_vigentes():
    for path in BASE_DIR.rglob('*.md'):
        rel = path.relative_to(BASE_DIR)
        if set(rel.parts[:-1]) & EXCLUIDOS:
            continue
        yield rel, path


class DocsVigentesTestCase(SimpleTestCase):
    """#DOC-01: la documentación vigente describe el código que existe hoy."""

    def test_ningun_md_vigente_menciona_codigo_borrado_ni_supabase(self):
        revisados = 0
        for rel, path in _md_vigentes():
            revisados += 1
            text = path.read_text(encoding='utf-8').lower()
            for needle in PROHIBIDOS:
                with self.subTest(archivo=str(rel), needle=needle):
                    self.assertNotIn(needle.lower(), text)
        self.assertGreater(revisados, 3)

    def test_enlaces_relativos_del_index_existen(self):
        index = BASE_DIR / 'Documentacion' / 'INDEX.md'
        text = index.read_text(encoding='utf-8')
        enlaces = re.findall(r'\]\(([^)\s]+)\)', text)
        self.assertTrue(enlaces)
        for enlace in enlaces:
            if enlace.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            with self.subTest(enlace=enlace):
                destino = (index.parent / enlace.split('#')[0]).resolve()
                self.assertTrue(destino.exists(), f'{enlace} no existe')
