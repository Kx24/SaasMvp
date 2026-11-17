"""
BOLT-37 (CONS-11, parte 2): ramas del checkout y del webhook sin cubrir.

MercadoPagoService se parchea siempre: ningún test llama a Mercado Pago ni
envía correos reales.
"""
import json
import uuid
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.orders.models import Order, PaymentLog, Plan
from apps.orders.services.mercadopago_service import MercadoPagoError

SERVICE = 'apps.orders.views.MercadoPagoService'
EMAIL = 'apps.orders.views.send_payment_success_email'


class CheckoutProcessTests(TestCase):
    def setUp(self):
        cache.clear()
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
            available_themes=['default'],
        )

    def _post(self, raw=None, **overrides):
        payload = {
            'token': 'tok-1', 'payment_method_id': 'visa', 'installments': 1,
            'email': ' Comprador@Test.com ', 'plan_slug': self.plan.slug,
            'payer_name': 'Comprador', 'accept_privacy': True,
        }
        payload.update(overrides)
        body = raw if raw is not None else json.dumps(payload)
        return self.client.post(
            reverse('orders:checkout_process'), data=body,
            content_type='application/json', HTTP_HOST='localhost',
            REMOTE_ADDR='198.51.100.20',
        )

    def test_json_invalido(self):
        response = self._post(raw='{no es json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], 'INVALID_JSON')
        self.assertEqual(Order.objects.count(), 0)

    def test_campos_obligatorios(self):
        for overrides, code in (
            (dict(token=''), 'MISSING_TOKEN'),
            (dict(email=''), 'MISSING_EMAIL'),
            (dict(plan_slug=''), 'MISSING_PLAN'),
        ):
            response = self._post(**overrides)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()['code'], code)
        self.assertEqual(Order.objects.count(), 0)

    def test_plan_inexistente_o_inactivo(self):
        self.assertEqual(self._post(plan_slug='no-existe').json()['code'], 'INVALID_PLAN')
        Plan.objects.filter(pk=self.plan.pk).update(is_active=False)
        response = self._post()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], 'INVALID_PLAN')
        self.assertEqual(Order.objects.count(), 0)

    @patch(EMAIL)
    @patch(SERVICE)
    def test_pago_aprobado_marca_orden_pagada(self, mock_cls, mock_email):
        mock_cls.return_value.process_payment.return_value = {
            'success': True, 'payment_id': '555', 'status': 'approved',
            'status_detail': 'accredited', 'message': '¡Pago aprobado!',
            'raw_response': {'status': 'approved', 'payment_method_id': 'visa'},
        }
        with self.captureOnCommitCallbacks(execute=True):
            response = self._post()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        order = Order.objects.get()
        self.assertEqual(body['order_uuid'], str(order.uuid))
        self.assertEqual(body['redirect_url'], f'/checkout/success/{order.uuid}/')
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.mp_payment_id, '555')
        self.assertEqual(order.email, 'comprador@test.com')
        self.assertTrue(order.onboarding_token)
        self.assertEqual(
            list(order.payment_logs.values_list('action', flat=True).order_by('id')),
            ['payment_attempt', 'status_change_paid', 'payment_approved'],
        )
        mock_email.assert_called_once()

    @patch(EMAIL)
    @patch(SERVICE)
    def test_email_que_falla_no_rompe_el_checkout(self, mock_cls, mock_email):
        mock_cls.return_value.process_payment.return_value = {
            'success': True, 'payment_id': '1', 'status': 'approved',
            'status_detail': '', 'message': 'ok', 'raw_response': {},
        }
        mock_email.side_effect = RuntimeError('smtp caído')
        with self.captureOnCommitCallbacks(execute=True):
            response = self._post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.get().status, 'paid')

    @patch(SERVICE)
    def test_pago_rechazado_deja_orden_failed(self, mock_cls):
        mock_cls.return_value.process_payment.return_value = {
            'success': False, 'payment_id': '556', 'status': 'rejected',
            'status_detail': 'cc_rejected_insufficient_amount',
            'message': 'Fondos insuficientes', 'raw_response': {'status': 'rejected'},
        }
        response = self._post()
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body['success'])
        self.assertEqual(body['error'], 'Fondos insuficientes')
        self.assertEqual(body['code'], 'cc_rejected_insufficient_amount')
        order = Order.objects.get()
        self.assertEqual(order.status, 'failed')
        self.assertEqual(order.mp_status, 'rejected')
        self.assertTrue(order.payment_logs.filter(action='payment_rejected').exists())

    @patch(SERVICE)
    def test_pago_pendiente_deja_orden_pending(self, mock_cls):
        mock_cls.return_value.process_payment.return_value = {
            'success': False, 'payment_id': '557', 'status': 'pending',
            'status_detail': 'pending_contingency', 'message': 'Pendiente',
            'raw_response': {},
        }
        response = self._post()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'pending')
        self.assertEqual(Order.objects.get().status, 'pending')

    @patch(SERVICE)
    def test_error_de_mercadopago_deja_orden_failed(self, mock_cls):
        mock_cls.return_value.process_payment.side_effect = MercadoPagoError(
            'token inválido', code='400', status=400,
        )
        response = self._post()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], '400')
        order = Order.objects.get()
        self.assertEqual(order.status, 'failed')
        self.assertIn('token inválido', order.notes)
        log = order.payment_logs.get(action='payment_error')
        self.assertEqual(log.status_detail, '400')

    @patch(SERVICE)
    def test_error_inesperado_responde_500(self, mock_cls):
        mock_cls.side_effect = RuntimeError('boom')
        response = self._post()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['code'], 'UNEXPECTED_ERROR')


class CheckoutPagesTests(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
            available_themes=['default'],
        )

    def test_checkout_view_plan_inexistente_404(self):
        response = self.client.get('/checkout/no-existe/', HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 404)

    @override_settings(MP_PUBLIC_KEY='pk-test')
    def test_checkout_view_renderiza_plan(self):
        response = self.client.get(
            reverse('orders:checkout', kwargs={'plan_slug': 'plan-test'}),
            HTTP_HOST='localhost',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['plan'], self.plan)
        self.assertEqual(response.context['mp_public_key'], 'pk-test')

    def test_success_con_uuid_inexistente_404(self):
        response = self.client.get(
            reverse('orders:checkout_success', kwargs={'order_uuid': uuid.uuid4()}),
            HTTP_HOST='localhost',
        )
        self.assertEqual(response.status_code, 404)

    def test_success_con_orden_no_pagada_redirige_a_error(self):
        order = Order.objects.create(
            plan=self.plan, email='a@b.cl', amount=10000, status='failed',
        )
        response = self.client.get(
            reverse('orders:checkout_success', kwargs={'order_uuid': order.uuid}),
            HTTP_HOST='localhost',
        )
        self.assertRedirects(
            response, reverse('orders:checkout_error'),
            fetch_redirect_response=False,
        )

    def test_success_con_orden_pagada_renderiza(self):
        order = Order.objects.create(
            plan=self.plan, email='a@b.cl', amount=10000, status='processing',
        )
        order.mark_as_paid('77')
        response = self.client.get(
            reverse('orders:checkout_success', kwargs={'order_uuid': order.uuid}),
            HTTP_HOST='localhost',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['order'], order)
        self.assertIn(str(order.onboarding_token), response.context['onboarding_url'])

    def test_error_page_pasa_codigo_y_mensaje(self):
        response = self.client.get(
            reverse('orders:checkout_error') + '?code=X1&message=hola',
            HTTP_HOST='localhost',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error_code'], 'X1')
        self.assertEqual(response.context['error_message'], 'hola')


@override_settings(MP_ACCESS_TOKEN='tok', MP_WEBHOOK_SECRET='s', DEBUG=False)
class WebhookBranchTests(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(name='P', slug='p', price=10000)
        self.order = Order.objects.create(
            plan=self.plan, email='a@b.cl', amount=10000, status='processing',
        )
        self.url = reverse('mp_webhook')

    def _post(self, query='type=payment&data.id=42'):
        return self.client.post(f'{self.url}?{query}', HTTP_HOST='localhost')

    def _payment(self, status='approved', ref=None, **extra):
        data = {
            'payment_id': '42', 'status': status, 'status_detail': 'd',
            'amount': 10000,
            'external_reference': ref if ref is not None else self.order.order_number,
            'raw_response': {'status': status},
        }
        data.update(extra)
        return data

    def _run(self, payment, valid=True, query='type=payment&data.id=42'):
        with patch('apps.orders.views.MercadoPagoService') as mock_cls:
            service = mock_cls.return_value
            service.validate_webhook_signature.return_value = valid
            service.get_payment.return_value = payment
            return self._post(query)

    def test_firma_invalida_responde_401(self):
        response = self._run(self._payment(), valid=False)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(PaymentLog.objects.count(), 0)

    def test_get_de_verificacion_responde_ok(self):
        response = self.client.get(reverse('mp_webhook_verify'), HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'OK')

    def test_tipo_distinto_de_payment_se_ignora(self):
        response = self._post('type=merchant_order&data.id=42')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentLog.objects.count(), 0)

    def test_sin_data_id_se_ignora(self):
        response = self._post('type=payment')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentLog.objects.count(), 0)

    def test_pago_no_encontrado_en_mp(self):
        response = self._run(None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentLog.objects.count(), 0)

    def test_orden_inexistente_por_referencia(self):
        response = self._run(self._payment(ref='ORD-NOPE'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentLog.objects.count(), 0)

    def test_sin_referencia_busca_por_mp_payment_id(self):
        Order.objects.filter(pk=self.order.pk).update(mp_payment_id='42')
        response = self._run(self._payment('rejected', ref=''))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'failed')

    def test_sin_referencia_ni_orden_con_ese_pago(self):
        response = self._run(self._payment(ref=''))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentLog.objects.count(), 0)

    def test_orden_finalizada_no_se_modifica(self):
        Order.objects.filter(pk=self.order.pk).update(status='completed')
        response = self._run(self._payment('rejected'))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')
        self.assertEqual(PaymentLog.objects.count(), 0)

    def test_reembolso_marca_orden_refunded(self):
        response = self._run(self._payment('refunded'))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'refunded')
        self.assertTrue(self.order.payment_logs.filter(action='webhook_refunded').exists())

    @patch(EMAIL)
    def test_aprobado_marca_pagada_y_envia_email_tras_commit(self, mock_email):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self._run(self._payment('approved'))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        self.assertEqual(len(callbacks), 1)
        mock_email.assert_called_once()

    @patch(EMAIL)
    def test_aprobado_con_email_que_falla_responde_200(self, mock_email):
        mock_email.side_effect = RuntimeError('smtp')
        with self.captureOnCommitCallbacks(execute=True):
            response = self._run(self._payment('approved'))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_aprobado_en_orden_ya_pagada_no_reenvia(self):
        self.order.mark_as_paid('42')
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self._run(self._payment('approved'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(callbacks, [])

    def test_excepcion_inesperada_responde_500_para_que_mp_reintente(self):
        with patch('apps.orders.views.MercadoPagoService', side_effect=RuntimeError('x')):
            response = self._post()
        self.assertEqual(response.status_code, 500)
