"""
BOLT-34 (LEY-01, art. 12): captura y prueba del consentimiento en el contacto.

Sin `accept_privacy` no se guarda nada; con él queda fecha, versión de la
política e IP. El user-agent ya no se captura.
"""
import re

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import FieldDoesNotExist
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.tenants.models import Client, Domain
from apps.website.models import ContactSubmission

HOST = 'consent.test'

BASE_DATA = {
    'name': 'Juan Pérez',
    'email': 'juan@test.com',
    'message': 'Hola, quisiera más información.',
    'intent': 'general',
    'form_source': 'page',
}


class ContactConsentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = Client.objects.create(
            name='Consent Test', contact_email='contacto@consent.test',
        )
        Domain.objects.create(
            client=cls.client_obj, domain=HOST, domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

    def _post(self, data, **extra):
        return self.client.post(
            reverse('contact_submit'), data=data, HTTP_HOST=HOST,
            REMOTE_ADDR='198.51.100.23', **extra,
        )

    def test_post_without_consent_json_is_validation_error(self):
        response = self._post(BASE_DATA, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body['ok'])
        self.assertIn('accept_privacy', body['errors'])
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_post_without_consent_classic_is_validation_error(self):
        response = self._post(BASE_DATA)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContactSubmission.objects.count(), 0)

    @override_settings(PRIVACY_POLICY_VERSION='2099-01-01')
    def test_post_with_consent_stores_proof(self):
        before = timezone.now()
        response = self._post({**BASE_DATA, 'accept_privacy': 'on'})
        self.assertEqual(response.status_code, 302)
        sub = ContactSubmission.objects.get()
        self.assertIsNotNone(sub.consent_at)
        self.assertGreaterEqual(sub.consent_at, before)
        self.assertLessEqual((timezone.now() - sub.consent_at).total_seconds(), 60)
        self.assertEqual(sub.consent_policy_version, '2099-01-01')
        self.assertEqual(sub.ip_address, '198.51.100.23')

    def test_default_version_is_current_policy_version(self):
        self._post({**BASE_DATA, 'accept_privacy': 'on'})
        sub = ContactSubmission.objects.get()
        self.assertEqual(sub.consent_policy_version, settings.PRIVACY_POLICY_VERSION)

    def test_user_agent_field_removed(self):
        with self.assertRaises(FieldDoesNotExist):
            ContactSubmission._meta.get_field('user_agent')
        model_admin = admin.site._registry[ContactSubmission]
        request = RequestFactory().get('/')
        listed = set(model_admin.readonly_fields)
        for _, opts in model_admin.fieldsets:
            listed.update(opts['fields'])
        self.assertNotIn('user_agent', listed)
        self.assertIn('consent_at', listed)
        self.assertIn('consent_policy_version', listed)
        self.assertIsNotNone(request)


class ContactFormsRenderCheckboxTestCase(TestCase):
    """Cada variante del formulario trae el checkbox sin pre-marcar."""

    TEMPLATES = [
        'partials/contact_form.html',
        'partials/contact_form_dynamic.html',
        'components/contact_multistep.html',
    ]

    def _assert_checkbox(self, html, name):
        self.assertIn('type="checkbox" name="accept_privacy"', html, name)
        tag = re.search(r'<input[^>]*name="accept_privacy"[^>]*>', html, re.S)
        self.assertIsNotNone(tag, name)
        self.assertNotRegex(tag.group(0), r'\bchecked\b', name)
        self.assertIn('/privacidad/', html, name)

    def test_each_contact_form_has_unchecked_consent_checkbox(self):
        for name in self.TEMPLATES:
            with self.subTest(template=name):
                html = render_to_string(name, {'source': 'page'})
                self._assert_checkbox(html, name)

    def test_landing_home_form_has_consent_checkbox(self):
        html = render_to_string('landing/home.html', {})
        self._assert_checkbox(html, 'landing/home.html')
