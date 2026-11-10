"""
#BUG-01: Django's template tag_re (`{%.*?%}|{{.*?}}|{#.*?#}`) is compiled
SIN re.DOTALL -- confirmado leyendo django.template.base.tag_re.flags.
Un comentario `{# ... #}` que abarca más de una línea nunca matchea como
tag: Django lo deja como texto literal, que termina renderizado en la
página (se vio en vivo en servelec-e2e: el head se corta a mitad de un
comentario, el navegador abre <body> antes de tiempo y el layout entero
se rompe). Ningún `{# ... #}` puede cruzar un salto de línea.
"""
import re
from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / 'templates'

MULTILINE_COMMENT_RE = re.compile(r'\{#(.*?)#\}', re.DOTALL)


class NoMultilineDjangoCommentsTestCase(SimpleTestCase):
    def test_no_django_comment_spans_multiple_lines(self):
        offenders = []
        for path in sorted(TEMPLATES_DIR.rglob('*.html')):
            text = path.read_text(encoding='utf-8')
            for match in MULTILINE_COMMENT_RE.finditer(text):
                if '\n' in match.group(0):
                    lineno = text[:match.start()].count('\n') + 1
                    offenders.append(f"{path.relative_to(BASE_DIR)}:{lineno}")

        self.assertFalse(
            offenders,
            "Comentarios Django {# #} multilínea (se renderizan como texto "
            "literal -- Django no usa re.DOTALL en tag_re): " + ", ".join(offenders),
        )
