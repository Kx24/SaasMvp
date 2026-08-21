"""
Tests de resolución de URLs para el módulo de checkout.

#AUD-01: `<slug:plan_slug>/` estaba declarado antes que `process/`,
`success/<uuid>/` y `error/` en apps/orders/urls.py, así que Django
capturaba /checkout/process/ como checkout_view(plan_slug='process')
en vez de process_payment_view -> 404 real, pago nunca procesable.
"""
from django.test import SimpleTestCase
from django.urls import resolve, reverse

from apps.orders import views


class CheckoutUrlResolutionTestCase(SimpleTestCase):
    """Cada ruta de checkout debe resolver a su vista específica,
    no ser capturada por el patrón genérico <slug:plan_slug>/."""

    def test_process_resolves_to_process_payment_view(self):
        match = resolve('/checkout/process/')
        self.assertIs(match.func, views.process_payment_view)

    def test_success_resolves_to_checkout_success_view(self):
        match = resolve(
            '/checkout/success/12345678-1234-5678-1234-567812345678/'
        )
        self.assertIs(match.func, views.checkout_success_view)

    def test_error_resolves_to_checkout_error_view(self):
        match = resolve('/checkout/error/')
        self.assertIs(match.func, views.checkout_error_view)

    def test_arbitrary_plan_slug_resolves_to_checkout_view(self):
        match = resolve('/checkout/plan-pro/')
        self.assertIs(match.func, views.checkout_view)
        self.assertEqual(match.kwargs, {'plan_slug': 'plan-pro'})

    def test_reverse_checkout_process(self):
        self.assertEqual(
            reverse('orders:checkout_process'),
            '/checkout/process/',
        )

    def test_reverse_checkout_error(self):
        self.assertEqual(
            reverse('orders:checkout_error'),
            '/checkout/error/',
        )
