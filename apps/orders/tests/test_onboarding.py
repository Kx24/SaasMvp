"""
Tests de la vista de onboarding.

#AUD-09: onboarding_view llamaba order.start_onboarding() (paid ->
onboarding) incondicionalmente, sin importar el método HTTP. Un simple
GET (link preview de un cliente de correo, prefetch del browser, alguien
solo mirando la página) mutaba el estado de la orden sin que el cliente
hubiera hecho nada.
"""
from django.test import TestCase
from django.urls import reverse

from apps.orders.models import Order, Plan


class OnboardingViewGetTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
            available_themes=['default'],
        )
        self.order = Order.objects.create(
            plan=self.plan, email='comprador@test.com', amount=10000,
            status='paid',
        )
        self.order.generate_onboarding_token()

    def test_get_onboarding_form_does_not_mutate_order_status(self):
        url = reverse('onboarding', kwargs={'token': self.order.onboarding_token})

        response = self.client.get(url, HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_post_onboarding_form_still_transitions_to_onboarding_status(self):
        """El POST real (aunque el form sea inválido) sí debe reflejar
        que el cliente empezó a completar el formulario."""
        url = reverse('onboarding', kwargs={'token': self.order.onboarding_token})

        response = self.client.post(url, data={}, HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'onboarding')
