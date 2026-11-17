"""
DASH-05: `seed_e2e_tenants` crea el usuario owner de la suite Playwright del
dashboard y se niega a correr fuera de desarrollo (el usuario tiene una
contraseña conocida: no puede existir en producción).
"""
import io

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.accounts.models import UserProfile
from apps.tenants.management.commands.seed_e2e_tenants import DASHBOARD_OWNER
from apps.tenants.models import Client


class SeedE2ETenantsTests(TestCase):
    @override_settings(DEBUG=False)
    def test_refuses_to_run_with_debug_off(self):
        with self.assertRaises(CommandError):
            call_command('seed_e2e_tenants', stdout=io.StringIO())
        self.assertFalse(User.objects.filter(username=DASHBOARD_OWNER['username']).exists())
        self.assertFalse(Client.objects.filter(slug='dash-e2e').exists())

    @override_settings(DEBUG=True)
    def test_creates_owner_of_the_dashboard_tenant(self):
        call_command('seed_e2e_tenants', stdout=io.StringIO())
        user = User.objects.get(username=DASHBOARD_OWNER['username'])
        self.assertTrue(user.check_password(DASHBOARD_OWNER['password']))
        profile = UserProfile.objects.get(user=user)
        self.assertEqual((profile.client.slug, profile.role), ('dash-e2e', 'owner'))
        self.assertTrue(profile.client.settings.enable_gallery)

    @override_settings(DEBUG=True)
    def test_is_idempotent(self):
        call_command('seed_e2e_tenants', stdout=io.StringIO())
        call_command('seed_e2e_tenants', stdout=io.StringIO())
        self.assertEqual(User.objects.filter(username=DASHBOARD_OWNER['username']).count(), 1)
        self.assertEqual(Client.objects.filter(slug='dash-e2e').count(), 1)
