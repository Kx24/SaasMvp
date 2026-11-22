"""
BOLT-34 (LEY-01, art. 12): consentimiento en el checkout.

Sin `accept_privacy: true` el checkout responde 400 MISSING_CONSENT antes de
tocar el plan o MercadoPago. Con él, la Order guarda fecha, versión e IP.
"""
import json
import re
from unittest.mock import patch

from django.core.cache import cache
from django.core.exceptions import FieldDoesNotExist
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import Order, Plan


class CheckoutConsentTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
            available_themes=['themes/default'],
        )

    def _post(self, **overrides):
        payload = {
            'token': 'tok-1',
            'payment_method_id': 'visa',
            'installments': 1,
            'email': 'comprador@test.com',
            'plan_slug': self.plan.slug,
            'payer_name': 'Comprador',
        }
        payload.update(overrides)
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post(
            reverse('orders:checkout_process'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_HOST='localhost',
            REMOTE_ADDR='198.51.100.9',
        )

    @patch('apps.orders.views.MercadoPagoService.process_payment')
    def test_missing_consent_returns_400_and_does_nothing(self, mock_pay):
        for value in (None, False):
            response = self._post(accept_privacy=value)
            self.assertEqual(response.status_code, 400)
            body = response.json()
            self.assertFalse(body['success'])
            self.assertEqual(body['code'], 'MISSING_CONSENT')
            self.assertEqual(body['error'], 'Debes aceptar la política de privacidad')
        self.assertEqual(Order.objects.count(), 0)
        mock_pay.assert_not_called()

    @override_settings(PRIVACY_POLICY_VERSION='2099-01-01')
    @patch('apps.orders.views.MercadoPagoService.process_payment')
    def test_consent_is_stored_on_order(self, mock_pay):
        mock_pay.return_value = {
            'success': True, 'payment_id': 'mp-1', 'status': 'approved',
            'status_detail': 'accredited', 'raw_response': {}, 'message': 'OK',
        }
        before = timezone.now()
        response = self._post(accept_privacy=True)
        self.assertEqual(response.status_code, 200, response.content)
        order = Order.objects.get()
        self.assertIsNotNone(order.consent_at)
        self.assertGreaterEqual(order.consent_at, before)
        self.assertEqual(order.consent_policy_version, '2099-01-01')
        self.assertEqual(order.ip_address, '198.51.100.9')

    def test_order_has_no_user_agent_field(self):
        with self.assertRaises(FieldDoesNotExist):
            Order._meta.get_field('user_agent')

    def test_checkout_html_has_unchecked_consent_checkbox(self):
        response = self.client.get(
            reverse('orders:checkout', kwargs={'plan_slug': self.plan.slug}),
            HTTP_HOST='localhost',
        )
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('type="checkbox" name="accept_privacy"', html)
        tag = re.search(r'<input[^>]*name="accept_privacy"[^>]*>', html, re.S)
        self.assertIsNotNone(tag)
        self.assertNotRegex(tag.group(0), r'\bchecked\b')
        self.assertIn('/privacidad/', html)
