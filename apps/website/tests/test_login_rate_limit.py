"""
Tests de rate limit en el login (#MED-05b / BOLT-04).

client_login no tenía ningún límite de intentos: un atacante podía probar
contraseñas sin freno (con la IP ya confiable gracias a BOLT-03). El límite
es por IP+username+tenant (scope='login'), con respuesta 429 cuyo mensaje
es EL MISMO genérico de credenciales inválidas (#AUD-03: no filtrar si el
bloqueo existe ni si el usuario existe).
"""
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain

LIMIT = 5
GENERIC_ERROR = 'Usuario o contraseña incorrectos.'


@override_settings(RATE_LIMIT_LOGIN_LIMIT=LIMIT, RATE_LIMIT_LOGIN_PERIOD=300)
class LoginRateLimitTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_a = Client.objects.create(
            name='Tenant A', company_name='Tenant A SpA',
            contact_email='a@test.com', contact_phone='+56900000001',
            is_active=True,
        )
        Domain.objects.create(
            client=cls.client_a, domain='tenant-a.test',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )

        cls.client_b = Client.objects.create(
            name='Tenant B', company_name='Tenant B SpA',
            contact_email='b@test.com', contact_phone='+56900000002',
            is_active=True,
        )
        Domain.objects.create(
            client=cls.client_b, domain='tenant-b.test',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )

        cls.owner_a = User.objects.create_user(username='owner_a', password='pass12345')
        UserProfile.objects.filter(user=cls.owner_a).update(client=cls.client_a, role='owner')

        cls.owner_b = User.objects.create_user(username='owner_b', password='pass12345')
        UserProfile.objects.filter(user=cls.owner_b).update(client=cls.client_b, role='owner')

    def setUp(self):
        cache.clear()  # LocMem persiste entre tests del mismo proceso

    def _login(self, username, password, host='tenant-a.test', ip='198.51.100.7'):
        return self.client.post(
            reverse('client_login'),
            {'username': username, 'password': password},
            HTTP_HOST=host,
            REMOTE_ADDR=ip,
        )

    def _exhaust(self, username='owner_a', host='tenant-a.test', ip='198.51.100.7'):
        for _ in range(LIMIT):
            response = self._login(username, 'wrong-password', host=host, ip=ip)
            self.assertEqual(response.status_code, 200)

    def test_exceeding_failed_logins_returns_429(self):
        self._exhaust()
        response = self._login('owner_a', 'wrong-password')
        self.assertEqual(response.status_code, 429)

    def test_429_message_is_indistinguishable_from_bad_credentials(self):
        """#AUD-03: el bloqueo no debe filtrar información — mismo texto
        genérico que credenciales inválidas, sin mención de límites."""
        self._exhaust()
        response = self._login('owner_a', 'pass12345')
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, GENERIC_ERROR, status_code=429)
        self.assertNotContains(response, 'intentos', status_code=429)

    def test_correct_password_blocked_once_limit_reached(self):
        """Alcanzado el límite, ni la contraseña correcta entra (si entrara,
        el atacante confirmaría credenciales a pesar del bloqueo)."""
        self._exhaust()
        response = self._login('owner_a', 'pass12345')
        self.assertEqual(response.status_code, 429)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_legit_login_under_threshold_unaffected(self):
        for _ in range(LIMIT - 1):
            self._login('owner_a', 'wrong-password')
        response = self._login('owner_a', 'pass12345')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.wsgi_request.user, self.owner_a)

    def test_counter_does_not_cross_ips(self):
        self._exhaust(ip='198.51.100.7')
        response = self._login('owner_a', 'pass12345', ip='203.0.113.99')
        self.assertEqual(response.status_code, 302)

    def test_counter_does_not_cross_usernames(self):
        self._exhaust(username='owner_a')
        # Mismo IP, otro username del mismo tenant: no hereda el contador
        response = self._login('nadie', 'wrong-password')
        self.assertEqual(response.status_code, 200)

    def test_counter_does_not_cross_tenants(self):
        self._exhaust(username='owner_b', host='tenant-a.test')
        # Mismo username e IP, pero en SU tenant: contador independiente
        response = self._login('owner_b', 'pass12345', host='tenant-b.test')
        self.assertEqual(response.status_code, 302)
