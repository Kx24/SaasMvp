"""
Tests del gatekeeper determinista (docs/kanban_agente.md, PILOT-01).

Los gates de verificación (ruff, suite, migraciones) hoy se corren a mano,
comando por comando, con salida de texto libre. El orquestador agéntico
(PILOT-03) necesita un veredicto parseable: un único JSON a stdout con
`passed: bool` y exit code 0 solo cuando `passed` es `True`.

Se verifica vía subprocess porque el script corre `manage.py test apps`
como paso interno -- no se puede importar y llamar en el mismo proceso
sin interferir con el test runner que ya está corriendo estos tests.

IMPORTANTE -- guarda anti-recursión: este archivo vive dentro de `apps`,
que es justo lo que el gate de tests del propio gatekeeper ejecuta
(`manage.py test apps`). Sin la guarda de abajo, correr el gatekeeper
dispara: gatekeeper.py -> manage.py test apps -> descubre este archivo
-> vuelve a invocar gatekeeper.py -> ... recursión sin límite (bomba de
fork real, confirmada en vivo: +150 procesos python.exe en ~3 minutos
antes de diagnosticarlo). `scripts/gatekeeper.py` propaga la env var
`GATEKEEPER_TEST_RUN=1` al subproceso de `manage.py test`; estos tests
se saltan a sí mismos cuando la ven, así que solo corren cuando un
desarrollador los invoca directamente (`manage.py test
apps.core.tests.test_gatekeeper`), sin esa env var seteada.
"""
import json
import os
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
GATEKEEPER_PATH = BASE_DIR / 'scripts' / 'gatekeeper.py'

_RUNNING_INSIDE_GATEKEEPER = os.environ.get('GATEKEEPER_TEST_RUN') == '1'


def _run_gatekeeper(timeout=120):
    return subprocess.run(
        [sys.executable, str(GATEKEEPER_PATH)],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@unittest.skipIf(
    _RUNNING_INSIDE_GATEKEEPER,
    "evita recursión: el propio gatekeeper ya está corriendo este archivo",
)
class GatekeeperHealthyRepoTestCase(SimpleTestCase):
    def test_passes_and_exits_zero_on_healthy_repo(self):
        result = _run_gatekeeper()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        payload = json.loads(result.stdout)
        self.assertTrue(payload['passed'], payload)
        self.assertIn('gates', payload)
        self.assertIn('ruff', payload['gates'])
        self.assertIn('tests', payload['gates'])
        self.assertIn('migrations', payload['gates'])

    def test_tests_gate_reports_totals_matching_real_suite(self):
        result = _run_gatekeeper()
        payload = json.loads(result.stdout)

        tests_gate = payload['gates']['tests']
        self.assertGreater(tests_gate['total'], 0)
        self.assertEqual(tests_gate['failures'], 0)
        self.assertGreaterEqual(tests_gate['skipped'], 0)

    def test_output_is_a_single_json_object_on_stdout(self):
        result = _run_gatekeeper()

        # Un solo objeto JSON en toda la salida -- json.loads falla si hay
        # texto extra antes/después (logging de settings, prints sueltos).
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)


@unittest.skipIf(
    _RUNNING_INSIDE_GATEKEEPER,
    "evita recursión: el propio gatekeeper ya está corriendo este archivo",
)
class GatekeeperBrokenTestTestCase(SimpleTestCase):
    """
    Inyecta un test que falla de verdad en apps/core/tests/ (descubierto
    por el test runner de Django igual que cualquier otro test*.py) para
    confirmar que el gatekeeper detecta el rojo real, no solo el feliz.
    """

    def setUp(self):
        self.injected_path = (
            BASE_DIR / 'apps' / 'core' / 'tests' / 'test_zz_gatekeeper_injected_failure.py'
        )
        self.injected_path.write_text(
            textwrap.dedent(
                """
                from django.test import SimpleTestCase


                class InjectedFailureTestCase(SimpleTestCase):
                    def test_this_always_fails(self):
                        self.assertEqual(1, 2, "fallo inyectado a propósito por test_gatekeeper.py")
                """
            ),
            encoding='utf-8',
        )
        self.addCleanup(self._remove_injected_file)

    def _remove_injected_file(self):
        if self.injected_path.exists():
            self.injected_path.unlink()

    def test_fails_and_exits_nonzero_with_failure_counted(self):
        result = _run_gatekeeper()

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

        payload = json.loads(result.stdout)
        self.assertFalse(payload['passed'], payload)
        self.assertGreaterEqual(payload['gates']['tests']['failures'], 1)
