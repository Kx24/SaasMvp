"""
Tests de rate limit en el checkout (#MED-05b / BOLT-04).

process_payment_view no tenía límite de intentos por IP: permitía card
testing (probar tarjetas robadas en loop contra MercadoPago). El límite es
por IP+tenant (scope='checkout'), respuesta JSON 429.
"""
import json

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

LIMIT = 4


@override_settings(RATE_LIMIT_CHECKOUT_LIMIT=LIMIT, RATE_LIMIT_CHECKOUT_PERIOD=600)
class CheckoutRateLimitTestCase(TestCase):
    def setUp(self):
        cache.clear()

    def _attempt(self, ip='198.51.100.7'):
        # Payload deliberadamente inválido: cada intento debe contar aunque
        # falle temprano (un atacante no manda payloads válidos de cortesía).
        return self.client.post(
            reverse('orders:checkout_process'),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_HOST='localhost',  # SYSTEM_DOMAIN, mismo patrón que test_emails
            REMOTE_ADDR=ip,
        )

    def test_exceeding_attempts_returns_429(self):
        for _ in range(LIMIT):
            response = self._attempt()
            self.assertEqual(response.status_code, 400)  # bajo el umbral: error normal
        response = self._attempt()
        self.assertEqual(response.status_code, 429)
        self.assertFalse(json.loads(response.content)['success'])

    def test_under_threshold_behaves_as_today(self):
        for _ in range(LIMIT - 1):
            self._attempt()
        response = self._attempt()
        self.assertEqual(response.status_code, 400)

    def test_counter_does_not_cross_ips(self):
        for _ in range(LIMIT + 1):
            self._attempt(ip='198.51.100.7')
        response = self._attempt(ip='203.0.113.99')
        self.assertEqual(response.status_code, 400)
