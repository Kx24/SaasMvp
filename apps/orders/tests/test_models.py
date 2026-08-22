"""
Tests de generación de order_number.

#AUD-05: _generate_order_number() usaba Order.objects.filter(...).count()+1.
Bajo concurrencia real, dos requests que leen el mismo count() antes de que
cualquiera haga INSERT calculan el mismo order_number -> IntegrityError en
el segundo save() (el campo es unique=True), con el pago ya cobrado en MP
pero sin orden persistida.
"""
import re
from unittest.mock import patch

from django.test import TestCase

from apps.orders.models import Order, Plan

ORDER_NUMBER_RE = re.compile(r'^ORD-\d{4}-[0-9A-F]{6}$')


class OrderNumberGenerationTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name='Plan Test', slug='plan-test', price=10000,
        )

    def _make_order(self, email):
        return Order(plan=self.plan, email=email, amount=10000)

    def test_order_number_format(self):
        order = self._make_order('comprador@test.com')
        order.save()

        self.assertTrue(
            ORDER_NUMBER_RE.match(order.order_number),
            f"'{order.order_number}' no matchea ORD-YYYY-XXXXXX",
        )

    def test_order_number_independent_of_concurrent_count(self):
        """
        Simula la ventana de carrera: dos órdenes distintas calculan
        order_number con el mismo Order.objects.filter(...).count() (como
        pasaría si ambos requests leen antes de que cualquiera inserte).

        Con count()+1, ambas órdenes obtendrían el mismo order_number y la
        segunda .save() lanzaría IntegrityError. La generación no debe
        depender de ese conteo compartido.
        """
        order_a = self._make_order('compradora@test.com')
        order_b = self._make_order('comprador-b@test.com')

        with patch(
            'apps.orders.models.Order.objects.filter'
        ) as mock_filter:
            mock_filter.return_value.count.return_value = 5
            order_a.save()
            order_b.save()

        self.assertNotEqual(order_a.order_number, order_b.order_number)
        self.assertTrue(ORDER_NUMBER_RE.match(order_a.order_number))
        self.assertTrue(ORDER_NUMBER_RE.match(order_b.order_number))

    def test_existing_order_number_not_regenerated_on_resave(self):
        order = self._make_order('comprador@test.com')
        order.save()
        original_number = order.order_number

        order.status = 'paid'
        order.save()

        self.assertEqual(order.order_number, original_number)
