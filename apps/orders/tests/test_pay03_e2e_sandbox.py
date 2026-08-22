"""
#PAY-03: E2E sandbox de pago -> provisioning.

El kanban describe esta card como "verificación manual guiada en sandbox"
(tarjeta de prueba real de Mercado Pago, servidor corriendo, browser) --
eso requiere credenciales MP_ACCESS_TOKEN/MP_PUBLIC_KEY de test que no
viven en el repo, así que no es automatizable tal cual.

Este test cubre la parte que sí se puede congelar en CI: la cadena
checkout -> webhook/respuesta directa de MP -> onboarding -> tenant,
con MercadoPagoService mockeado (sin red, sin credenciales reales). No
reemplaza probar contra la API real de MP, pero adelanta cualquier
regresión en el contrato entre pasos sin depender de un browser.
"""
import json
from unittest.mock import patch

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.orders.models import Order, Plan
from apps.tenants.models import Client, Domain
from apps.website.models import Section


class PaymentToProvisioningE2ETestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
            available_themes=['default'],
        )

    def _checkout(self, mock_process_payment, mp_result):
        mock_process_payment.return_value = mp_result
        body = json.dumps({
            'token': 'tok-1',
            'payment_method_id': 'visa',
            'installments': 1,
            'email': 'comprador@test.com',
            'plan_slug': self.plan.slug,
            'payer_name': 'Comprador Test',
        })
        return self.client.post(
            reverse('orders:checkout_process'),
            data=body,
            content_type='application/json',
            HTTP_HOST='localhost',
        )

    @patch('apps.orders.views.MercadoPagoService.process_payment')
    def test_approved_card_completes_full_provisioning(self, mock_process_payment):
        # 1. Pago aprobado (tarjeta de prueba) -> orden 'paid' + token + email
        with self.captureOnCommitCallbacks(execute=True):
            checkout_response = self._checkout(mock_process_payment, {
                'success': True,
                'payment_id': 'mp-approved-1',
                'status': 'approved',
                'status_detail': 'accredited',
                'raw_response': {},
                'message': 'OK',
            })

        self.assertEqual(checkout_response.status_code, 200)
        order = Order.objects.get(
            order_number=checkout_response.json()['order_number']
        )
        self.assertEqual(order.status, 'paid')
        self.assertTrue(order.onboarding_token)
        self.assertEqual(len(mail.outbox), 1, "esperado: email de pago exitoso")

        onboarding_token = order.onboarding_token

        # 2. GET del formulario de onboarding con el token del email
        onboarding_url = reverse('onboarding', kwargs={'token': onboarding_token})
        form_response = self.client.get(onboarding_url, HTTP_HOST='localhost')
        self.assertEqual(form_response.status_code, 200)

        # 3. POST del formulario -> crea Client+Domain+User+Sections
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            post_response = self.client.post(
                onboarding_url,
                data={
                    'company_name': 'Rancho Sandbox',
                    'slug': 'rancho-sandbox',
                    'primary_color': '#2563eb',
                    'secondary_color': '#1e40af',
                    'template': 'default',
                    'contact_phone': '',
                    'whatsapp_number': '',
                    'tagline': 'Turismo rural',
                    'about_text': 'Descripción de prueba',
                },
                HTTP_HOST='localhost',
                follow=True,
            )

        # La redirección post-onboarding debe llegar a la página de éxito,
        # no a un 404 (el token de onboarding se limpia al completar la
        # orden, y esa página se busca justamente por ese token).
        self.assertEqual(post_response.status_code, 200)
        success_url = reverse('onboarding_success', kwargs={'token': onboarding_token})
        self.assertIn(
            (success_url, 302),
            post_response.redirect_chain,
            f"no redirigió a la página de éxito; cadena: {post_response.redirect_chain}",
        )

        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')
        self.assertIsNotNone(order.client)

        client = order.client
        self.assertEqual(client.slug, 'rancho-sandbox')
        self.assertTrue(
            Domain.objects.filter(client=client, is_primary=True, is_active=True).exists()
        )

        profile = UserProfile.objects.get(client=client)
        self.assertEqual(profile.role, 'owner')

        self.assertTrue(Section.objects.filter(client=client, section_type='hero').exists())
        self.assertTrue(Section.objects.filter(client=client, section_type='contact').exists())

        # welcome + site_ready
        self.assertEqual(len(mail.outbox), 2)

    @patch('apps.orders.views.MercadoPagoService.process_payment')
    def test_rejected_card_leaves_order_failed_without_tenant(self, mock_process_payment):
        response = self._checkout(mock_process_payment, {
            'success': False,
            'payment_id': 'mp-rejected-1',
            'status': 'rejected',
            'status_detail': 'cc_rejected_insufficient_amount',
            'raw_response': {},
            'message': 'Pago rechazado',
        })

        self.assertEqual(response.status_code, 400)
        order = Order.objects.get(email='comprador@test.com')
        self.assertEqual(order.status, 'failed')
        self.assertIsNone(order.client)
        self.assertFalse(Client.objects.filter(slug='rancho-sandbox').exists())
