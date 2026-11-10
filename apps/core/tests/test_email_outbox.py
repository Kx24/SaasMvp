"""
Tests de EmailOutbox y del comando send_pending_emails (#MED-01).

Contexto: SMTP bloquea el hilo HTTP (~1-3s en Zoho). transaction.on_commit
(#AUD-06) ya evita que el email salga DENTRO de la transacción de DB,
pero el request sigue esperando el handshake SMTP después de comitear.
Con EMAIL_ASYNC=True, EmailService encola en EmailOutbox (un INSERT
local, rápido) en vez de abrir la conexión SMTP; un comando de
management -- corrido por cron cada 5 min -- hace el envío real, con
reintentos acotados.
"""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.core.models import EmailOutbox
from apps.orders.models import Order, Plan
from apps.orders.services.email_service import EmailService, send_set_password_email


class EmailServiceAsyncQueueingTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
        )
        self.order = Order.objects.create(
            plan=self.plan, email='comprador@test.com', amount=10000,
            status='paid',
        )
        self.order.generate_onboarding_token()

    def test_send_email_is_synchronous_by_default(self):
        EmailService().send_payment_success(self.order)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(EmailOutbox.objects.count(), 0)

    @override_settings(EMAIL_ASYNC=True)
    def test_send_email_queues_instead_of_sending_when_async(self):
        EmailService().send_payment_success(self.order)

        self.assertEqual(len(mail.outbox), 0)
        outbox_email = EmailOutbox.objects.get()
        self.assertEqual(outbox_email.status, 'pending')
        self.assertEqual(outbox_email.to_email, 'comprador@test.com')
        self.assertIn(self.order.order_number, outbox_email.html_content)

    @override_settings(EMAIL_ASYNC=True)
    def test_urgent_password_email_is_always_synchronous(self):
        """
        set_password (configurar/recuperar contraseña) fuerza envío
        síncrono aunque EMAIL_ASYNC esté activo -- no tiene sentido que
        alguien esperando resetear su contraseña dependa de que corra el
        próximo cron.
        """
        user = User.objects.create_user(username='owner', email='owner@test.com')

        send_set_password_email(user, 'sometoken')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(EmailOutbox.objects.count(), 0)


class SendPendingEmailsCommandTestCase(TestCase):
    def _make_outbox(self, **overrides):
        defaults = dict(
            to_email='destino@test.com',
            from_email='no-reply@andesscale.cl',
            subject='Asunto de prueba',
            html_content='<p>Hola</p>',
            text_content='Hola',
        )
        defaults.update(overrides)
        return EmailOutbox.objects.create(**defaults)

    def test_sends_pending_email_and_marks_sent(self):
        outbox_email = self._make_outbox()

        call_command('send_pending_emails')

        self.assertEqual(len(mail.outbox), 1)
        outbox_email.refresh_from_db()
        self.assertEqual(outbox_email.status, 'sent')
        self.assertIsNotNone(outbox_email.sent_at)

    def test_does_not_resend_already_sent_email(self):
        self._make_outbox(status='sent', sent_at=timezone.now())

        call_command('send_pending_emails')

        self.assertEqual(len(mail.outbox), 0)

    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_failure_increments_attempts_and_stays_pending_below_max(self, mock_send):
        mock_send.side_effect = RuntimeError("SMTP caído")
        outbox_email = self._make_outbox(attempts=0, max_attempts=3)

        call_command('send_pending_emails')

        outbox_email.refresh_from_db()
        self.assertEqual(outbox_email.status, 'pending')
        self.assertEqual(outbox_email.attempts, 1)
        self.assertIn('SMTP caído', outbox_email.last_error)

    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_failure_marks_failed_after_max_attempts(self, mock_send):
        mock_send.side_effect = RuntimeError("SMTP caído")
        outbox_email = self._make_outbox(attempts=2, max_attempts=3)

        call_command('send_pending_emails')

        outbox_email.refresh_from_db()
        self.assertEqual(outbox_email.status, 'failed')
        self.assertEqual(outbox_email.attempts, 3)
        self.assertIsNotNone(outbox_email.failed_at)
