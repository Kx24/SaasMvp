"""
BOLT-37 (CONS-11, parte 2): ramas de views_onboarding.py y métodos de Order.

Sin red ni SMTP: los emails van por transaction.on_commit y aquí no se
ejecutan (o se parchean).
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.orders.models import Order, PaymentLog, Plan
from apps.tenants.models import Client

HOST = {'HTTP_HOST': 'localhost'}


class OnboardingBase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
            available_themes=['default'],
        )

    def _order(self, status='paid', token=True, **kwargs):
        order = Order.objects.create(
            plan=self.plan, email='comprador@test.com', amount=10000,
            status=status, **kwargs,
        )
        if token:
            order.generate_onboarding_token()
        return order

    def _url(self, order):
        return reverse('onboarding', kwargs={'token': order.onboarding_token})


class OnboardingViewStatesTests(OnboardingBase):
    def test_token_inexistente(self):
        import uuid
        response = self.client.get(
            reverse('onboarding', kwargs={'token': uuid.uuid4()}), **HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'token_not_found')

    def test_orden_completada_muestra_resumen(self):
        order = self._order(status='completed')
        response = self.client.get(self._url(order), **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/onboarding_completed.html')

    def test_estado_invalido(self):
        order = self._order(status='failed')
        response = self.client.get(self._url(order), **HOST)
        self.assertEqual(response.context['error'], 'invalid_status')

    def test_token_expirado_marca_orden_expirada(self):
        order = self._order()
        Order.objects.filter(pk=order.pk).update(
            token_expires_at=timezone.now() - timedelta(hours=1),
        )
        url = self._url(order)
        response = self.client.get(url, **HOST)
        self.assertTemplateUsed(response, 'orders/onboarding_expired.html')
        order.refresh_from_db()
        self.assertEqual(order.status, 'expired')
        self.assertIsNone(order.onboarding_token)

    def test_plan_sin_temas_usa_default(self):
        order = self._order()
        with patch.object(Plan, 'get_available_themes_list', return_value=[]):
            response = self.client.get(self._url(order), **HOST)
        self.assertEqual(response.context['available_themes'], ['themes/default'])

    def test_post_invalido_muestra_errores_como_mensajes(self):
        order = self._order()
        response = self.client.post(self._url(order), data={}, **HOST)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        msgs = [str(m) for m in response.context['messages']]
        self.assertTrue(any('company_name' in m for m in msgs))

    def test_post_valido_con_error_de_proceso_muestra_mensaje(self):
        order = self._order()
        form_patch = patch(
            'apps.orders.views_onboarding.ClientOnboardingForm.is_valid',
            return_value=True,
        )
        with form_patch, patch(
            'apps.orders.views_onboarding.ClientOnboardingForm.cleaned_data',
            {}, create=True,
        ), patch(
            'apps.orders.views_onboarding.process_onboarding',
            side_effect=RuntimeError('db caída'),
        ):
            response = self.client.post(self._url(order), data={}, **HOST)
        self.assertEqual(response.status_code, 200)
        msgs = [str(m) for m in response.context['messages']]
        self.assertTrue(any('Ocurrió un error' in m for m in msgs))
        order.refresh_from_db()
        self.assertNotEqual(order.status, 'completed')


class OnboardingSuccessViewTests(OnboardingBase):
    def test_token_inexistente_404(self):
        import uuid
        response = self.client.get(
            reverse('onboarding_success', kwargs={'token': uuid.uuid4()}), **HOST,
        )
        self.assertEqual(response.status_code, 404)

    def test_orden_no_completada_redirige_al_formulario(self):
        order = self._order()
        response = self.client.get(
            reverse('onboarding_success', kwargs={'token': order.onboarding_token}),
            **HOST,
        )
        self.assertRedirects(
            response, self._url(order), fetch_redirect_response=False,
        )

    def test_orden_completada_renderiza(self):
        order = self._order()
        client = Client.objects.create(name='Empresa Ok', slug='empresa-ok')
        order.mark_as_completed(client)
        response = self.client.get(
            reverse('onboarding_success', kwargs={'token': order.onboarding_token}),
            **HOST,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['client'], client)


class OrderModelTests(OnboardingBase):
    def test_str_y_get_absolute_url(self):
        order = self._order(token=False)
        self.assertIn(order.order_number, str(order))
        self.assertIn(str(order.uuid), order.get_absolute_url())

    def test_plan_str_y_url(self):
        self.assertIn('Plan Test', str(self.plan))
        self.assertEqual(self.plan.get_absolute_url(), '/checkout/plan-test/')

    def test_plan_listas_con_valores_invalidos(self):
        self.plan.features = 'texto'
        self.plan.available_themes = None
        self.assertEqual(self.plan.get_features_list(), [])
        self.assertEqual(self.plan.get_available_themes_list(), ['default'])

    def test_is_token_valid_casos(self):
        order = self._order(token=False)
        self.assertFalse(order.is_token_valid())           # sin token
        order.generate_onboarding_token()
        self.assertTrue(order.is_token_valid())
        order.token_expires_at = None
        self.assertFalse(order.is_token_valid())           # sin expiración
        order.token_expires_at = timezone.now() - timedelta(minutes=1)
        self.assertFalse(order.is_token_valid())           # vencido
        order.token_expires_at = timezone.now() + timedelta(hours=1)
        order.status = 'failed'
        self.assertFalse(order.is_token_valid())           # estado inválido

    def test_mark_as_failed_guarda_datos_de_mp(self):
        order = self._order(token=False)
        order.mark_as_failed({'status': 'rejected', 'status_detail': 'cc_x'})
        order.refresh_from_db()
        self.assertEqual(order.status, 'failed')
        self.assertEqual(order.mp_status, 'rejected')
        self.assertEqual(order.mp_status_detail, 'cc_x')
        order.mark_as_failed()
        self.assertEqual(order.status, 'failed')

    def test_mark_as_completed_conserva_token_y_asigna_cliente(self):
        order = self._order()
        client = Client.objects.create(name='Empresa Ok', slug='empresa-ok')
        order.mark_as_completed(client)
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')
        self.assertEqual(order.client, client)
        self.assertIsNotNone(order.completed_at)
        self.assertIsNotNone(order.onboarding_token)
        self.assertTrue(order.is_completed)
        self.assertTrue(order.is_paid)

    def test_mark_as_expired_limpia_token(self):
        order = self._order()
        order.mark_as_expired()
        order.refresh_from_db()
        self.assertEqual(order.status, 'expired')
        self.assertIsNone(order.onboarding_token)
        self.assertIsNone(order.token_expires_at)
        self.assertFalse(order.is_paid)

    def test_start_onboarding_solo_desde_paid(self):
        order = self._order(status='failed')
        order.start_onboarding()
        self.assertEqual(order.status, 'failed')
        order.status = 'paid'
        order.start_onboarding()
        order.refresh_from_db()
        self.assertEqual(order.status, 'onboarding')

    def test_get_onboarding_url(self):
        order = self._order(token=False)
        self.assertIsNone(order.get_onboarding_url())
        order.generate_onboarding_token()
        self.assertTrue(
            order.get_onboarding_url().endswith(f'/onboarding/{order.onboarding_token}/')
        )

    def test_can_start_onboarding_y_dias_restantes(self):
        order = self._order()
        self.assertTrue(order.can_start_onboarding)
        self.assertIn(order.days_until_token_expires, (2, 3))
        order.token_expires_at = None
        self.assertIsNone(order.days_until_token_expires)
        order.token_expires_at = timezone.now() - timedelta(days=2)
        self.assertEqual(order.days_until_token_expires, 0)

    def test_paymentlog_str(self):
        order = self._order(token=False)
        log = PaymentLog.objects.create(order=order, action='payment_attempt')
        self.assertIn(order.order_number, str(log))
        self.assertIn('payment_attempt', str(log))
