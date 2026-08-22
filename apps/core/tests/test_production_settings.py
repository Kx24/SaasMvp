"""
Tests de configuración de email en producción.

#AUD-07: sin EMAIL_HOST_USER, production.py caía en silencio a
console.EmailBackend -- correos "enviados" que nunca salen, sin error
visible en logs ni en el arranque del proceso. Ahora falla al importar
el módulo de settings (mismo patrón que SECRET_KEY), para que un deploy
sin credenciales SMTP no arranque en vez de perder correos en silencio.

Se verifica vía subprocess (no import directo) porque el módulo de
settings solo se evalúa una vez por proceso; necesitamos observar el
fallo de importación con variables de entorno controladas.
"""
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

REQUIRED_BASE_ENV = {
    'SECRET_KEY': 'test-secret-key-for-settings-check',
    'DATABASE_URL': 'postgres://user:pass@localhost:5432/db',
}


def _check_production_settings(extra_env: dict) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith('EMAIL_')}
    env.update(REQUIRED_BASE_ENV)
    env.update(extra_env)
    return subprocess.run(
        [sys.executable, '-c', 'import django; django.setup()'],
        cwd=BASE_DIR,
        env={**env, 'DJANGO_SETTINGS_MODULE': 'config.settings.production'},
        capture_output=True,
        text=True,
        timeout=30,
    )


class ProductionEmailConfigTestCase(SimpleTestCase):
    def test_missing_email_credentials_fails_to_start(self):
        result = _check_production_settings({})

        self.assertNotEqual(result.returncode, 0, result.stderr)
        self.assertIn('EMAIL_HOST_USER', result.stderr)

    def test_with_email_credentials_starts_cleanly(self):
        result = _check_production_settings({
            'EMAIL_HOST_USER': 'no-reply@andesscale.cl',
            'EMAIL_HOST_PASSWORD': 'super-secret',
        })

        self.assertEqual(result.returncode, 0, result.stderr)


REQUIRED_EMAIL_ENV = {
    'EMAIL_HOST_USER': 'no-reply@andesscale.cl',
    'EMAIL_HOST_PASSWORD': 'super-secret',
}


def _get_production_debug_value(extra_env: dict) -> subprocess.CompletedProcess:
    env = {
        k: v for k, v in os.environ.items()
        if not k.startswith('EMAIL_') and k != 'DEBUG_PRODUCTION'
    }
    env.update(REQUIRED_BASE_ENV)
    env.update(REQUIRED_EMAIL_ENV)
    env.update(extra_env)
    return subprocess.run(
        [
            sys.executable, '-c',
            'import django; django.setup(); '
            'from django.conf import settings; print(settings.DEBUG)',
        ],
        cwd=BASE_DIR,
        env={**env, 'DJANGO_SETTINGS_MODULE': 'config.settings.production'},
        capture_output=True,
        text=True,
        timeout=30,
    )


class ProductionDebugConfigTestCase(SimpleTestCase):
    """
    #AUD-12: DEBUG_PRODUCTION=true encendía DEBUG en producción --
    páginas de error con traceback completo, variables de entorno y
    rutas del sistema expuestas a cualquier visitante que provoque un
    error 500. Producción debe correr siempre con DEBUG=False, sin
    ningún override por variable de entorno.
    """

    def test_debug_production_override_no_longer_enables_debug(self):
        result = _get_production_debug_value({'DEBUG_PRODUCTION': 'true'})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'False')

    def test_debug_is_false_without_any_override(self):
        result = _get_production_debug_value({})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'False')
