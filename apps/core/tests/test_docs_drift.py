from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def _read(relative):
    return (BASE_DIR / relative).read_text(encoding='utf-8')


class DocsDriftTestCase(SimpleTestCase):
    """Guardia anti-desfase (#BOLT-31, #CONS-02): la documentación de entrada
    no puede volver a hablar de Supabase (la base es Neon) ni del MCP de
    GitHub retirado, y debe enlazar la ejecución agéntica."""

    def test_docs_no_mencionan_supabase(self):
        for path in ('CLAUDE.md', 'README.md', 'Documentacion/README.md'):
            with self.subTest(path=path):
                self.assertNotIn('supabase', _read(path).lower())

    def test_claude_md_sin_rastro_del_mcp_ni_claims_obsoletos(self):
        text = _read('CLAUDE.md')
        for needle in ('github-mcp-server', 'MCP Server', 'corre en cada push'):
            with self.subTest(needle=needle):
                self.assertNotIn(needle, text)

    def test_claude_md_enlaza_ejecucion_agentica(self):
        text = _read('CLAUDE.md')
        self.assertIn('docs/agente/README.md', text)
        self.assertIn('scripts/gatekeeper.py --strict', text)

    def test_gitignore_ignora_coverage(self):
        lines = _read('.gitignore').splitlines()
        self.assertIn('.coverage', [line.strip() for line in lines])
