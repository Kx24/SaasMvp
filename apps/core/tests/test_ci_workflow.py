"""Guardia (SEC-12): el workflow de CI existe y ejecuta los controles del gate."""
from pathlib import Path
from unittest import skipUnless

from django.conf import settings
from django.test import SimpleTestCase

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

WORKFLOW = Path(settings.BASE_DIR) / '.github' / 'workflows' / 'ci.yml'


@skipUnless(yaml, 'pyyaml no instalado')
class CiWorkflowTests(SimpleTestCase):
    def setUp(self):
        self.assertTrue(WORKFLOW.exists(), 'falta .github/workflows/ci.yml')
        self.text = WORKFLOW.read_text(encoding='utf-8')
        self.data = yaml.safe_load(self.text)

    def _triggers(self):
        # PyYAML interpreta la clave `on` como booleano True
        return self.data.get('on', self.data.get(True))

    def _commands(self):
        return '\n'.join(
            step.get('run', '')
            for job in self.data['jobs'].values()
            for step in job['steps']
        )

    def test_triggers_push_and_pull_request(self):
        triggers = self._triggers()
        self.assertIn('push', triggers)
        self.assertIn('pull_request', triggers)

    def test_push_acotado_para_no_duplicar_ejecucion(self):
        push = self._triggers()['push']
        self.assertIsInstance(push, dict, 'push sin filtro duplica la CI con un PR abierto')
        self.assertEqual(push['branches'], ['develop', 'main', 'agent/**'])
        self.assertEqual(self._triggers()['pull_request']['branches'], ['develop', 'main'])

    def test_pip_audit_con_version_fija(self):
        reqs = (Path(settings.BASE_DIR) / 'requirements-dev.txt').read_text(encoding='utf-8')
        self.assertRegex(reqs, r'(?mi)^pip-audit==\d+\.\d+\.\d+\s*$')

    def test_runs_gate_controls(self):
        cmds = self._commands()
        self.assertIn('gatekeeper.py --strict', cmds)
        self.assertIn('tests_isolation', cmds)
        self.assertIn('ruff check', cmds)
        self.assertIn('pip_audit', cmds)

    def test_no_secrets_context(self):
        self.assertNotIn('secrets.', self.text)

    def test_declares_permissions(self):
        self.assertEqual(self.data.get('permissions'), {'contents': 'read'})


class DjangoExtensionsSoloEnDesarrolloTests(SimpleTestCase):
    """TOOL-04: ningún camino de producción depende de django_extensions."""

    def _read(self, rel):
        return (Path(settings.BASE_DIR) / rel).read_text(encoding='utf-8')

    def test_base_y_production_no_lo_incluyen(self):
        from config.settings import base
        self.assertNotIn('django_extensions', base.INSTALLED_APPS)
        self.assertNotIn('django_extensions', self._read('config/settings/production.py'))

    def test_build_y_procfile_no_dependen_de_el(self):
        for rel in ('build.sh', 'Procfile'):
            text = self._read(rel)
            for needle in ('django_extensions', 'django-extensions',
                           'shell_plus', 'runserver_plus', 'requirements-dev'):
                self.assertNotIn(needle, text, f'{rel} usa {needle}')
