"""
Tests de autorización cross-tenant en el login.

#AUD-03: `client_login` autenticaba (y logueaba) a cualquier usuario válido
sin verificar que perteneciera al tenant del dominio visitado. Un owner
del tenant A podía loguearse en el dominio de B usando sus propias
credenciales (válidas) y quedar con sesión activa en B.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain


class LoginTenantAuthorizationTestCase(TestCase):
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

        cls.superuser = User.objects.create_superuser(
            username='root', password='pass12345', email='root@test.com'
        )

    def _login(self, username, password, host):
        return self.client.post(
            reverse('client_login'),
            {'username': username, 'password': password},
            HTTP_HOST=host,
        )

    def test_owner_logs_into_own_domain(self):
        response = self._login('owner_b', 'pass12345', 'tenant-b.test')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.wsgi_request.user, self.owner_b)
        # Sesión activa: una request autenticada subsiguiente debe verse logueada.
        session_response = self.client.get(reverse('dashboard'), HTTP_HOST='tenant-b.test')
        self.assertEqual(session_response.status_code, 200)

    def test_owner_a_cannot_login_via_domain_b(self):
        """Credenciales válidas de A, pero en el dominio de B: debe
        rechazarse con el mismo mensaje genérico que credenciales
        inválidas (no revelar que el usuario existe en otro tenant)."""
        response = self._login('owner_a', 'pass12345', 'tenant-b.test')

        self.assertEqual(response.status_code, 200)  # re-renderiza el form, no redirect
        self.assertContains(response, 'Usuario o contraseña incorrectos.')
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_wrong_password_shows_same_generic_message(self):
        """El mensaje de rechazo cross-tenant debe ser indistinguible del
        de credenciales inválidas."""
        response = self._login('owner_b', 'wrong-password', 'tenant-b.test')
        self.assertContains(response, 'Usuario o contraseña incorrectos.')

    def test_superuser_logs_into_any_domain(self):
        response = self._login('root', 'pass12345', 'tenant-b.test')
        self.assertEqual(response.status_code, 302)
