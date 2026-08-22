"""
Tests de estructura de render.yaml.

#AUD-04: el cron `contact-digest` estaba insertado en medio de la lista
de `services`, y `buildCommand`/`startCommand`/`healthCheckPath`/`envVars`
quedaron anidados bajo el cron en vez de bajo el servicio web -- el web
service (saasmvp) quedaba sin ninguno de esos campos. Si Render
re-sincronizaba el blueprint, el deploy quedaba sin build/start command
ni variables de entorno.
"""
from pathlib import Path

import yaml
from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
RENDER_YAML_PATH = BASE_DIR / 'render.yaml'

REQUIRED_WEB_ENV_KEYS = {
    'PYTHON_VERSION',
    'DJANGO_SETTINGS_MODULE',
    'SECRET_KEY',
    'DEBUG',
    'DATABASE_URL',
    'BASE_DOMAIN',
    'DEFAULT_TENANT_SLUG',
    'EXTRA_DOMAINS',
    'EMAIL_HOST',
    'EMAIL_PORT',
    'EMAIL_USE_TLS',
}


class RenderYamlStructureTestCase(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(RENDER_YAML_PATH, encoding='utf-8') as f:
            cls.config = yaml.safe_load(f)

    def _service(self, service_type):
        matches = [s for s in self.config['services'] if s.get('type') == service_type]
        self.assertEqual(
            len(matches), 1,
            f"Se esperaba exactamente 1 servicio type={service_type!r}, "
            f"se encontraron {len(matches)}",
        )
        return matches[0]

    def test_web_service_has_build_and_start_commands(self):
        web = self._service('web')
        self.assertEqual(web.get('name'), 'saasmvp')
        self.assertTrue(web.get('buildCommand'), "web service sin buildCommand")
        self.assertTrue(web.get('startCommand'), "web service sin startCommand")
        self.assertTrue(web.get('healthCheckPath'), "web service sin healthCheckPath")

    def test_web_service_has_all_required_env_vars(self):
        web = self._service('web')
        env_keys = {var['key'] for var in web.get('envVars', [])}
        missing = REQUIRED_WEB_ENV_KEYS - env_keys
        self.assertFalse(missing, f"web service sin envVars: {missing}")

    def test_cron_service_is_self_contained(self):
        cron = self._service('cron')
        self.assertEqual(cron.get('name'), 'contact-digest')
        self.assertTrue(cron.get('schedule'), "cron sin schedule")
        self.assertTrue(cron.get('command'), "cron sin command")
        self.assertTrue(cron.get('runtime'), "cron sin runtime propio")
        self.assertTrue(cron.get('buildCommand'), "cron sin buildCommand propio")

        env_keys = {var['key'] for var in cron.get('envVars', [])}
        required_for_cron = {
            'DJANGO_SETTINGS_MODULE', 'SECRET_KEY', 'DATABASE_URL',
        }
        missing = required_for_cron - env_keys
        self.assertFalse(missing, f"cron sin envVars necesarias: {missing}")

    def test_database_service_declared(self):
        self.assertTrue(self.config.get('databases'), "sin bloque databases")
        self.assertEqual(self.config['databases'][0]['name'], 'saasmvp-db')
