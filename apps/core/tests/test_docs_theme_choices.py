import re
from pathlib import Path

from django.test import SimpleTestCase

from apps.tenants.models import Client

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

THEME_CHOICES_CITATION_RE = re.compile(
    r"`THEME_CHOICES`:\s*((?:`'[^']+'`,?\s*)+)\)"
)
QUOTED_VALUE_RE = re.compile(r"'([^']+)'")


def _cited_theme_values(text):
    """Extrae los valores citados en la primera cita literal de THEME_CHOICES."""
    match = THEME_CHOICES_CITATION_RE.search(text)
    if not match:
        return None
    return set(QUOTED_VALUE_RE.findall(match.group(1)))


class DocsThemeChoicesTestCase(SimpleTestCase):
    """Guardia anti-drift (#BOLT-10): docs que citan Client.THEME_CHOICES no
    pueden quedar desactualizadas en silencio cuando el modelo cambia
    (ocurrió con #DEUDA-03: 'servelec'/'ranchocachimba' quedaron citados
    después de que dejaron de ser valores válidos en esta rama)."""

    def setUp(self):
        self.actual_choices = {value for value, _label in Client.THEME_CHOICES}

    def test_claude_md_theme_choices_citation_matches_model(self):
        text = (BASE_DIR / "CLAUDE.md").read_text(encoding="utf-8")
        cited = _cited_theme_values(text)
        self.assertIsNotNone(
            cited, "CLAUDE.md no tiene ninguna cita literal de `THEME_CHOICES`"
        )
        self.assertEqual(
            cited,
            self.actual_choices,
            "CLAUDE.md cita valores de THEME_CHOICES que no coinciden con "
            "Client.THEME_CHOICES real en esta rama",
        )

    def test_skill_md_theme_choices_citation_matches_model(self):
        text = (
            BASE_DIR / ".claude" / "skills" / "andesscale-saas" / "SKILL.md"
        ).read_text(encoding="utf-8")
        cited = _cited_theme_values(text)
        self.assertIsNotNone(
            cited,
            "SKILL.md (andesscale-saas) no tiene ninguna cita literal de "
            "`THEME_CHOICES`",
        )
        self.assertEqual(
            cited,
            self.actual_choices,
            "SKILL.md cita valores de THEME_CHOICES que no coinciden con "
            "Client.THEME_CHOICES real en esta rama",
        )
