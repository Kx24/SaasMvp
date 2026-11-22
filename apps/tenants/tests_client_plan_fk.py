"""BIZ-04: `Client.plan` es una FK a `orders.Plan` (antes un CharField con slug)."""
from django.db import models
from django.test import TestCase

from apps.orders.models import Order, Plan
from apps.orders.views_onboarding import process_onboarding
from apps.tenants.models import Client


class ClientPlanFieldTests(TestCase):
    def test_plan_is_nullable_fk_to_orders_plan(self):
        field = Client._meta.get_field('plan')
        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.related_model, Plan)
        self.assertTrue(field.null)
        self.assertTrue(field.blank)
        self.assertEqual(field.remote_field.on_delete, models.PROTECT)

    def test_client_without_plan_is_valid(self):
        client = Client.objects.create(name='Sin plan', slug='sin-plan')
        self.assertIsNone(client.plan)


class OnboardingAssignsPlanTests(TestCase):
    def test_onboarding_client_gets_order_plan_object(self):
        plan = Plan.objects.create(
            name='Plan FK', slug='plan-fk', price=10000,
            available_themes=['themes/default'],
        )
        order = Order.objects.create(
            plan=plan, email='comprador@fk.test', amount=10000, status='paid',
        )
        with self.captureOnCommitCallbacks(execute=True):
            client, _user = process_onboarding(order, {
                'company_name': 'Empresa FK', 'slug': 'empresa-fk',
                'template': 'themes/default',
            })
        client.refresh_from_db()
        self.assertEqual(client.plan, plan)
        self.assertEqual(client.plan.slug, order.plan.slug)
