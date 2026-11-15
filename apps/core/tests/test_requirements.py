"""SEC-10: higiene de dependencias (lee archivos, no instala nada)."""
import re
from pathlib import Path

import yaml
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]

# Último parche 5.2.x publicado en PyPI al 2026-11-15.
DJANGO_MIN_PATCH = 19

DEV_ONLY = [
    'djangorestframework', 'django-extensions', 'ipython', 'asttokens', 'decorator',
    'executing', 'ipython-pygments-lexers', 'jedi', 'matplotlib-inline', 'parso',
    'prompt-toolkit', 'pure-eval', 'pygments', 'stack-data', 'traitlets', 'wcwidth',
    'colorama',
]


def _lines(name):
    out = []
    for raw in (ROOT / name).read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if line and not line.startswith('#') and not line.startswith('-r'):
            out.append(line)
    return out


def _names(name):
    return {
        re.split(r'[=<>!~\[ ]', ln, maxsplit=1)[0].lower().replace('_', '-')
        for ln in _lines(name)
    }


class RequirementsTests(SimpleTestCase):
    def test_produccion_sin_herramientas_de_desarrollo_ni_drf(self):
        names = _names('requirements.txt')
        for pkg in DEV_ONLY:
            self.assertNotIn(pkg, names)

    def test_dev_tiene_pip_audit_extensions_ipython(self):
        names = _names('requirements-dev.txt')
        for pkg in ('pip-audit', 'django-extensions', 'ipython'):
            self.assertIn(pkg, names)

    def test_django_ultimo_parche(self):
        matches = [
            re.fullmatch(r'Django==5\.2\.(\d+)', ln)
            for ln in _lines('requirements.txt')
            if ln.lower().startswith('django==')
        ]
        self.assertEqual(len(matches), 1)
        self.assertIsNotNone(matches[0], 'Django debe ser 5.2.x')
        self.assertGreaterEqual(int(matches[0].group(1)), DJANGO_MIN_PATCH)

    def test_todo_fijado_con_igual_igual(self):
        for ln in _lines('requirements.txt'):
            self.assertRegex(ln, r'^[A-Za-z0-9_.\-]+==[^=\s]+$')

    def test_python_version_consistente(self):
        render = yaml.safe_load((ROOT / 'render.yaml').read_text(encoding='utf-8'))
        versions = []
        for svc in render['services']:
            for env in svc.get('envVars', []):
                if env.get('key') == 'PYTHON_VERSION':
                    versions.append(str(env['value']))
        self.assertEqual(len(versions), 3)
        self.assertEqual(len(set(versions)), 1)
        ci = yaml.safe_load((ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8'))
        ci_versions = set()
        for job in ci['jobs'].values():
            for step in job.get('steps', []):
                v = (step.get('with') or {}).get('python-version')
                if v:
                    ci_versions.add(str(v))
        major_minor = '.'.join(versions[0].split('.')[:2])
        self.assertEqual(ci_versions, {major_minor})
