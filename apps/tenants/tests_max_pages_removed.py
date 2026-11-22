from django.core.exceptions import FieldDoesNotExist
from django.test import SimpleTestCase

from apps.orders.models import Plan
from apps.tenants.models import Client


class MaxPagesRemovedTests(SimpleTestCase):
    """DEUDA-11: max_pages no existe ni en Client ni en Plan."""

    def test_client_has_no_max_pages(self):
        with self.assertRaises(FieldDoesNotExist):
            Client._meta.get_field('max_pages')

    def test_plan_has_no_max_pages(self):
        with self.assertRaises(FieldDoesNotExist):
            Plan._meta.get_field('max_pages')
