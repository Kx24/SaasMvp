"""
SEC-08: un solo login y `next` validado.

`client_login` respeta `next` solo si es una URL interna; un `next` externo
o protocol-relative (`//host`) se descarta. Las vistas duplicadas de
`apps.accounts` (login/logout) ya no existen.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import NoReverseMatch, resolve, reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain

HOST = 'login-next.test'


class LoginNextTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(
            name='Next Tenant', company_name='Next Tenant SpA',
            contact_email='n@test.com', contact_phone='+56900000003',
            is_active=True,
        )
        Domain.objects.create(
            client=cls.tenant, domain=HOST,
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )
        cls.owner = User.objects.create_user(username='owner_next', password='pass12345')
        UserProfile.objects.filter(user=cls.owner).update(client=cls.tenant, role='owner')

    def _login(self, query='', extra=None):
        data = {'username': 'owner_next', 'password': 'pass12345'}
        data.update(extra or {})
        return self.client.post(reverse('client_login') + query, data, HTTP_HOST=HOST)

    def test_internal_next_is_respected(self):
        response = self._login('?next=/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/dashboard/')

    def test_internal_next_from_post_is_respected(self):
        response = self._login(extra={'next': '/dashboard/'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/dashboard/')

    def test_external_next_is_discarded(self):
        response = self._login('?next=https://evil.example/x')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_protocol_relative_next_is_discarded(self):
        response = self._login('?next=//evil.example/x')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_no_next_goes_home(self):
        response = self._login()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_login_form_preserves_next(self):
        response = self.client.get(reverse('client_login') + '?next=/dashboard/', HTTP_HOST=HOST)
        self.assertContains(response, 'name="next"')
        self.assertContains(response, 'value="/dashboard/"')

    def test_forgot_password_links_to_auth_login(self):
        response = self.client.get(reverse('accounts:forgot_password'), HTTP_HOST=HOST)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/auth/login/"')


class SingleLoginTestCase(TestCase):
    def test_accounts_login_logout_do_not_exist(self):
        with self.assertRaises(NoReverseMatch):
            reverse('accounts:login')
        with self.assertRaises(NoReverseMatch):
            reverse('accounts:logout')

    def test_auth_login_resolves_to_client_login(self):
        from apps.website.auth_views import client_login
        self.assertIs(resolve('/auth/login/').func, client_login)
