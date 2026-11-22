"""
Tests de TOOL-08: test_gatekeeper sin falsos rojos por tiempo.

No lanzan el gate real (parchean `subprocess.run`), así que no se saltan
con GATEKEEPER_TEST_RUN=1. La lógica bajo prueba vive en
`apps/core/gatekeeper_runner.py` (no es un archivo de test).
"""
import io
import json
import os
import subprocess
import unittest
from unittest import mock

from django.test import SimpleTestCase

_FAKE_PAYLOAD = {
    'passed': True,
    'gates': {
        'ruff': {'passed': True},
        'tests': {'passed': True, 'total': 10, 'failures': 0, 'skipped': 0},
        'migrations': {'passed': True},
    },
}


class GatekeeperTimeoutConfigTestCase(SimpleTestCase):
    def test_default_timeout_is_at_least_600(self):
        from apps.core import gatekeeper_runner

        with mock.patch.dict(os.environ):
            os.environ.pop('GATEKEEPER_TEST_TIMEOUT_S', None)
            self.assertGreaterEqual(gatekeeper_runner.resolve_timeout(), 600)

    def test_env_var_overrides_timeout(self):
        from apps.core import gatekeeper_runner

        with mock.patch.dict(os.environ, {'GATEKEEPER_TEST_TIMEOUT_S': '1234'}):
            self.assertEqual(gatekeeper_runner.resolve_timeout(), 1234)

    def test_timeout_expired_fails_with_helpful_message(self):
        from apps.core import gatekeeper_runner

        timeout_error = subprocess.TimeoutExpired(cmd='gatekeeper', timeout=7)
        with mock.patch.object(subprocess, 'run', side_effect=timeout_error):
            with self.assertRaises(AssertionError) as ctx:
                gatekeeper_runner.run_gatekeeper(timeout=7)
        message = str(ctx.exception)
        self.assertIn('7', message)
        self.assertIn('GATEKEEPER_TEST_TIMEOUT_S', message)


class GatekeeperHealthyRunsOnceTestCase(SimpleTestCase):
    def test_healthy_class_runs_gate_exactly_once_for_its_three_tests(self):
        from apps.core.tests import test_gatekeeper as tg

        fake = subprocess.CompletedProcess(
            args=['gatekeeper'], returncode=0, stdout=json.dumps(_FAKE_PAYLOAD), stderr='',
        )
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(tg.GatekeeperHealthyRepoTestCase)
        with mock.patch.object(tg, '_RUNNING_INSIDE_GATEKEEPER', False), \
                mock.patch.object(subprocess, 'run', return_value=fake) as run:
            result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)

        self.assertEqual(result.testsRun, 3)
        self.assertTrue(result.wasSuccessful(), result.failures + result.errors)
        self.assertEqual(run.call_count, 1)
