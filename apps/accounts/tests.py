"""
Hallazgo incidental de BOLT-12 (2026-11-12): `apps/accounts/views.py`
llamaba `UserProfile.generate_invitation_token()`, `is_invitation_valid()` y
`clear_invitation()`, que no existían. En producción:

- `/auth/set-password/<token>/` (enlace del correo de bienvenida tras el
  onboarding pagado) respondía 500 para todo token existente.
- `/auth/forgot-password/` respondía 500 para todo email registrado y 302
  para uno inexistente: además de romper la recuperación, delataba qué
  emails tienen cuenta.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain

HOST = 'cuentas.test'


class InvitationMethodsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', email='u1@cuentas.test', password='x')
        self.profile = self.user.profile

    def test_generate_sets_token_expiry_and_returns_it(self):
        token = self.profile.generate_invitation_token(days=1)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.invitation_token, token)
        self.assertIsNotNone(self.profile.invited_at)
        delta = self.profile.invitation_expires_at - timezone.now()
        self.assertTrue(timedelta(hours=23) < delta <= timedelta(days=1))

    def test_each_call_generates_a_different_token(self):
        self.assertNotEqual(self.profile.generate_invitation_token(), self.profile.generate_invitation_token())

    def test_validity(self):
        self.assertFalse(self.profile.is_invitation_valid())  # sin token
        self.profile.generate_invitation_token(days=1)
        self.assertTrue(self.profile.is_invitation_valid())
        self.profile.invitation_expires_at = timezone.now() - timedelta(minutes=1)
        self.assertFalse(self.profile.is_invitation_valid())  # expirado

    def test_clear_invalidates(self):
        self.profile.generate_invitation_token()
        self.profile.clear_invitation()
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.invitation_token)
        self.assertFalse(self.profile.is_invitation_valid())


class PasswordFlowsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(name='Cuentas', slug='cuentas', contact_email='c@cuentas.test')
        Domain.objects.create(client=cls.tenant, domain=HOST, domain_type='custom',
                              is_primary=True, is_active=True, is_verified=True)

    def setUp(self):
        self.user = User.objects.create_user(username='dueno', email='dueno@cuentas.test', password='Vieja-123456')
        UserProfile.objects.update_or_create(user=self.user, defaults={'client': self.tenant, 'role': 'owner'})
        self.user.refresh_from_db()

    def test_set_password_link_from_welcome_email_works(self):
        token = self.user.profile.generate_invitation_token(days=7)
        url = reverse('accounts:set_password', args=[token])
        self.assertEqual(self.client.get(url, HTTP_HOST=HOST).status_code, 200)

        response = self.client.post(url, {'password': 'Nueva-Clave-789!', 'password_confirm': 'Nueva-Clave-789!'},
                                    HTTP_HOST=HOST)
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Nueva-Clave-789!'))
        self.assertIsNone(self.user.profile.invitation_token)  # un solo uso
        # Redirige al dashboard real (antes: NoReverseMatch 'dashboard:home' -> 500).
        self.assertEqual(response['Location'], reverse('dashboard'))

    def test_authenticated_user_on_forgot_password_goes_to_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:forgot_password'), HTTP_HOST=HOST)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard'))

    def test_expired_link_shows_expired_page(self):
        token = self.user.profile.generate_invitation_token(days=1)
        UserProfile.objects.filter(pk=self.user.profile.pk).update(
            invitation_expires_at=timezone.now() - timedelta(hours=1))
        response = self.client.get(reverse('accounts:set_password', args=[token]), HTTP_HOST=HOST)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/set_password_expired.html')

    def test_forgot_password_existing_and_unknown_respond_the_same(self):
        existing = self.client.post(reverse('accounts:forgot_password'), {'email': 'dueno@cuentas.test'},
                                    HTTP_HOST=HOST)
        unknown = self.client.post(reverse('accounts:forgot_password'), {'email': 'nadie@cuentas.test'},
                                   HTTP_HOST=HOST)
        self.assertEqual(existing.status_code, 302)
        self.assertEqual(unknown.status_code, existing.status_code)
        self.assertEqual(existing['Location'], unknown['Location'])
        self.assertEqual(len(mail.outbox), 1)  # solo al email que existe
        self.assertEqual(mail.outbox[0].to, ['dueno@cuentas.test'])
