"""
Tests de validación de firma del webhook de Mercado Pago.

#AUD-02: validate_webhook_signature() estaba comentado en la vista
(mercadopago_webhook_view) -> cualquiera podía llamar al endpoint público
y disparar transiciones de estado en Order sin firma válida. Además,
el servicio devolvía True cuando faltaba el secret ("modo desarrollo"),
lo que en producción sin MP_WEBHOOK_SECRET configurado deja el endpoint
completamente abierto.
"""
import hashlib
import hmac
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.orders.models import Order, Plan

WEBHOOK_SETTINGS = dict(
    MP_ACCESS_TOKEN='test-access-token',
    MP_WEBHOOK_SECRET='test-webhook-secret',
    DEBUG=False,
)


def _sign(secret: str, data_id: str, request_id: str, ts: str) -> str:
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


class MercadoPagoWebhookSignatureTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
        )
        self.order = Order.objects.create(
            plan=self.plan,
            email='comprador@test.com',
            amount=10000,
            status='processing',
            mp_payment_id='mp-123',
        )
        self.url = reverse('mp_webhook')
        self.data_id = 'mp-123'

    def _post(self, headers=None, data_id=None):
        # HTTP_HOST='localhost': TenantMiddleware trata 'testserver' (host
        # por defecto del test client) como dominio desconocido -> 404.
        # 'localhost' está hardcodeado como SYSTEM_DOMAIN, deja pasar sin
        # tenant, que es lo que necesita un endpoint de webhook público.
        merged_headers = {'HTTP_HOST': 'localhost'}
        merged_headers.update(headers or {})
        return self.client.post(
            f"{self.url}?type=payment&data.id={data_id or self.data_id}",
            content_type='application/json',
            **merged_headers,
        )

    @override_settings(**WEBHOOK_SETTINGS)
    @patch('apps.orders.services.mercadopago_service.MercadoPagoService.get_payment')
    def test_webhook_without_signature_header_returns_401(self, mock_get_payment):
        response = self._post()

        self.assertEqual(response.status_code, 401)
        mock_get_payment.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')

    @override_settings(**WEBHOOK_SETTINGS)
    @patch('apps.orders.services.mercadopago_service.MercadoPagoService.get_payment')
    def test_webhook_with_invalid_signature_returns_401(self, mock_get_payment):
        response = self._post(headers={
            'HTTP_X_SIGNATURE': 'ts=1234567890,v1=deadbeef',
            'HTTP_X_REQUEST_ID': 'req-1',
        })

        self.assertEqual(response.status_code, 401)
        mock_get_payment.assert_not_called()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')

    @override_settings(**WEBHOOK_SETTINGS)
    @patch('apps.orders.services.mercadopago_service.MercadoPagoService.get_payment')
    def test_webhook_with_valid_signature_processes_payment(self, mock_get_payment):
        request_id = 'req-42'
        ts = '1700000000'
        signature = _sign(WEBHOOK_SETTINGS['MP_WEBHOOK_SECRET'], self.data_id, request_id, ts)

        mock_get_payment.return_value = {
            'payment_id': self.data_id,
            'status': 'approved',
            'status_detail': 'accredited',
            'amount': 10000,
            'external_reference': self.order.order_number,
            'raw_response': {},
        }

        response = self._post(headers={
            'HTTP_X_SIGNATURE': f'ts={ts},v1={signature}',
            'HTTP_X_REQUEST_ID': request_id,
        })

        self.assertEqual(response.status_code, 200)
        mock_get_payment.assert_called_once()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    @override_settings(MP_ACCESS_TOKEN='test-access-token', MP_WEBHOOK_SECRET='', DEBUG=False)
    @patch('apps.orders.services.mercadopago_service.MercadoPagoService.get_payment')
    def test_webhook_without_secret_in_production_fails_closed(self, mock_get_payment):
        """Sin MP_WEBHOOK_SECRET configurado y fuera de DEBUG, el endpoint
        debe rechazar en vez de procesar sin validar (comportamiento viejo)."""
        response = self._post(headers={
            'HTTP_X_SIGNATURE': 'ts=1700000000,v1=whatever',
            'HTTP_X_REQUEST_ID': 'req-1',
        })

        self.assertEqual(response.status_code, 401)
        mock_get_payment.assert_not_called()
