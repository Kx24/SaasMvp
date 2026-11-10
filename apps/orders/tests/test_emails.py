"""
Tests de envío de emails transaccionales fuera de la transacción.

#AUD-06: los envíos de email vivían dentro de bloques @transaction.atomic
(checkout, webhook, process_onboarding). django.core.mail.send() no es
transaccional: si algo falla después de enviar el correo y la transacción
hace rollback, el email ya salió describiendo un estado (pago confirmado,
sitio listo) que nunca llegó a persistirse. Además SMTP bloquea el hilo
mientras la transacción de DB sigue abierta.

Fix: encolar los envíos con transaction.on_commit(), que Django descarta
automáticamente si la transacción (o el savepoint que lo registró) hace
rollback.
"""
import hashlib
import hmac
import json
from unittest.mock import patch

from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order, Plan
from apps.orders.views_onboarding import process_onboarding


def _sign(secret: str, data_id: str, request_id: str, ts: str) -> str:
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


class CheckoutEmailOnCommitTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
        )

    @patch('apps.orders.views.MercadoPagoService.process_payment')
    def test_payment_success_email_deferred_to_commit(self, mock_process_payment):
        mock_process_payment.return_value = {
            'success': True,
            'payment_id': 'mp-1',
            'status': 'approved',
            'status_detail': 'accredited',
            'raw_response': {},
            'message': 'OK',
        }
        body = json.dumps({
            'token': 'tok-1',
            'payment_method_id': 'visa',
            'installments': 1,
            'email': 'comprador@test.com',
            'plan_slug': self.plan.slug,
            'payer_name': 'Comprador',
        })

        with self.captureOnCommitCallbacks() as callbacks:
            response = self.client.post(
                reverse('orders:checkout_process'),
                data=body,
                content_type='application/json',
                HTTP_HOST='localhost',
            )

        self.assertEqual(response.status_code, 200)
        # El request ya terminó, pero el email no debe haber salido todavía:
        # está diferido a que la transacción de la orden confirme.
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(len(callbacks), 1)

        for callback in callbacks:
            callback()

        self.assertEqual(len(mail.outbox), 1)


class WebhookEmailOnCommitTestCase(TestCase):
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

    @patch(
        'apps.orders.services.mercadopago_service.MercadoPagoService.get_payment'
    )
    def test_webhook_approved_email_deferred_to_commit(self, mock_get_payment):
        secret = 'test-webhook-secret'
        request_id = 'req-1'
        ts = '1700000000'
        signature = _sign(secret, 'mp-123', request_id, ts)

        mock_get_payment.return_value = {
            'payment_id': 'mp-123',
            'status': 'approved',
            'status_detail': 'accredited',
            'amount': 10000,
            'external_reference': self.order.order_number,
            'raw_response': {},
        }

        with self.settings(
            MP_ACCESS_TOKEN='test-access-token',
            MP_WEBHOOK_SECRET=secret,
            DEBUG=False,
        ):
            with self.captureOnCommitCallbacks() as callbacks:
                response = self.client.post(
                    f"{self.url}?type=payment&data.id=mp-123",
                    content_type='application/json',
                    HTTP_HOST='localhost',
                    HTTP_X_SIGNATURE=f'ts={ts},v1={signature}',
                    HTTP_X_REQUEST_ID=request_id,
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(len(callbacks), 1)

        for callback in callbacks:
            callback()

        self.assertEqual(len(mail.outbox), 1)


class OnboardingEmailTransactionTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
        )
        self.order = Order.objects.create(
            plan=self.plan, email='comprador@test.com', amount=10000,
            status='paid',
        )
        self.onboarding_data = {
            'company_name': 'Empresa Test',
            'slug': 'empresa-test',
            'template': 'default',
        }

    def test_rollback_after_onboarding_sends_no_email(self):
        """
        Si algo revierte la transacción después de process_onboarding, los
        emails de bienvenida no deben haber salido: con un send directo
        (implementación vieja) el SMTP ya se dispara antes del rollback,
        aunque Client/User terminen sin persistirse.
        """
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                process_onboarding(self.order, self.onboarding_data)
                raise IntegrityError("forzado para simular rollback")

        self.assertEqual(len(mail.outbox), 0)

    def test_successful_onboarding_sends_welcome_emails_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            process_onboarding(self.order, self.onboarding_data)

        self.assertEqual(len(mail.outbox), 2)
