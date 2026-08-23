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


def _get_production_email_async_value(extra_env: dict) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith('EMAIL_')}
    env.update(REQUIRED_BASE_ENV)
    env.update(REQUIRED_EMAIL_ENV)
    env.update(extra_env)
    return subprocess.run(
        [
            sys.executable, '-c',
            'import django; django.setup(); '
            'from django.conf import settings; print(settings.EMAIL_ASYNC)',
        ],
        cwd=BASE_DIR,
        env={**env, 'DJANGO_SETTINGS_MODULE': 'config.settings.production'},
        capture_output=True,
        text=True,
        timeout=30,
    )


class ProductionEmailAsyncConfigTestCase(SimpleTestCase):
    """
    #MED-01: SMTP real bloquea el hilo del request 1-3s por envío. En
    producción, EMAIL_ASYNC debe estar activo por defecto (encolar en
    EmailOutbox en vez de abrir la conexión SMTP dentro del request).
    """

    def test_email_async_is_true_by_default_in_production(self):
        result = _get_production_email_async_value({})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'True')

    def test_email_async_can_be_disabled_explicitly(self):
        result = _get_production_email_async_value({'EMAIL_ASYNC': 'false'})

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'False')


def _get_production_middleware_json(extra_env: dict) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith('EMAIL_')}
    env.update(REQUIRED_BASE_ENV)
    env.update(REQUIRED_EMAIL_ENV)
    env.update(extra_env)
    return subprocess.run(
        [
            sys.executable, '-c',
            'import django; django.setup(); '
            'import json; from django.conf import settings; '
            'print(json.dumps({'
            '"middleware": settings.MIDDLEWARE, '
            '"has_csp_dict": hasattr(settings, "CONTENT_SECURITY_POLICY"), '
            '"has_permissions_policy_dict": hasattr(settings, "PERMISSIONS_POLICY"), '
            '}))',
        ],
        cwd=BASE_DIR,
        env={**env, 'DJANGO_SETTINGS_MODULE': 'config.settings.production'},
        capture_output=True,
        text=True,
        timeout=30,
    )


class ProductionSecurityHeadersConfigTestCase(SimpleTestCase):
    """
    #SEC-02: los diccionarios reales viven en config/settings/
    security_headers.py (testeados sin subprocess ahí, no dependen de
    env vars) -- esto solo confirma que production.py los conecta:
    middleware presente, en orden correcto, y los settings expuestos.
    """

    def test_csp_and_permissions_policy_middleware_present_and_ordered(self):
        result = _get_production_middleware_json({})
        self.assertEqual(result.returncode, 0, result.stderr)

        import json
        data = json.loads(result.stdout.strip())
        middleware = data['middleware']

        self.assertIn('csp.middleware.CSPMiddleware', middleware)
        self.assertIn('django_permissions_policy.PermissionsPolicyMiddleware', middleware)

        # Ambas deben ir después de XFrameOptionsMiddleware (mismo punto
        # donde ya se decide frame-ancestors/X-Frame-Options).
        xframe_idx = middleware.index('django.middleware.clickjacking.XFrameOptionsMiddleware')
        csp_idx = middleware.index('csp.middleware.CSPMiddleware')
        pp_idx = middleware.index('django_permissions_policy.PermissionsPolicyMiddleware')
        self.assertGreater(csp_idx, xframe_idx)
        self.assertGreater(pp_idx, xframe_idx)

        self.assertTrue(data['has_csp_dict'])
        self.assertTrue(data['has_permissions_policy_dict'])
