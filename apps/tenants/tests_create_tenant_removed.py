"""DEUDA-15: `create_tenant` fue eliminado; `provision_tenant` es el comando vigente."""
from django.core.management import get_commands
from django.test import SimpleTestCase


class CreateTenantRemovedTests(SimpleTestCase):
    def test_create_tenant_is_not_registered(self):
        self.assertNotIn('create_tenant', get_commands())

    def test_provision_tenant_is_registered(self):
        self.assertIn('provision_tenant', get_commands())
