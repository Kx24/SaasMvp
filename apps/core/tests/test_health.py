"""#OPS-05 (parte): endpoint /health/ para el Health Check Path de Render."""
from unittest import mock

from django.db import connection
from django.test import TestCase

from apps.tenants.models import Client, Domain

OK = {'status': 'ok', 'database': 'ok'}


class HealthEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(
            name='Health Co', contact_email='contacto@health.test',
        )
        Domain.objects.create(
            client=cls.tenant, domain='health.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

    def test_ok_with_tenant_host(self):
        response = self.client.get('/health/', HTTP_HOST='health.test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), OK)

    def test_ok_with_unknown_host(self):
        response = self.client.get('/health/', HTTP_HOST='servicio.onrender.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), OK)

    def test_ok_with_arbitrary_unregistered_host(self):
        response = self.client.get('/health/', HTTP_HOST='desconocido.example.org')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), OK)

    def test_ok_with_localhost(self):
        response = self.client.get('/health/', HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), OK)

    def test_ok_when_tenant_under_construction(self):
        self.tenant.mode_under_construction = True
        self.tenant.save()
        response = self.client.get('/health/', HTTP_HOST='health.test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), OK)

    def test_head_allowed(self):
        response = self.client.head('/health/', HTTP_HOST='servicio.onrender.com')
        self.assertEqual(response.status_code, 200)

    def test_database_failure_returns_503_without_leaking(self):
        secret = 'boom-secreto-de-conexion'
        with mock.patch.object(connection, 'cursor', side_effect=Exception(secret)):
            response = self.client.get('/health/', HTTP_HOST='servicio.onrender.com')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'error', 'database': 'error'})
        self.assertNotIn(secret, response.content.decode())

    def test_post_not_allowed(self):
        response = self.client.post('/health/', HTTP_HOST='health.test')
        self.assertEqual(response.status_code, 405)

    def test_no_login_required(self):
        response = self.client.get('/health/', HTTP_HOST='health.test')
        self.assertEqual(response.status_code, 200)

    def test_not_cached(self):
        response = self.client.get('/health/', HTTP_HOST='health.test')
        self.assertIn('no-cache', response.headers['Cache-Control'])

    def test_other_paths_still_blocked_on_unknown_host(self):
        response = self.client.get('/health/x', HTTP_HOST='desconocido.example.org')
        self.assertEqual(response.status_code, 404)
