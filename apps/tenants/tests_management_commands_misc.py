"""
CONS-13 (parte 1): cobertura de `setup_cloudinary_folders`, `setup_dev_env`.
Sin red ni escritura fuera de directorios temporales.
"""
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

from apps.orders.models import Plan
from apps.tenants.models import Client, Domain
from apps.website.models import Section, Service

User = get_user_model()


def run(name, *args, **kwargs):
    out, err = StringIO(), StringIO()
    call_command(name, *args, stdout=out, stderr=err, **kwargs)
    return out.getvalue(), err.getvalue()


class SetupCloudinaryFoldersTests(TestCase):
    def setUp(self):
        Client.objects.create(name='Acme', slug='acme', company_name='Acme')
        Client.objects.create(name='Off', slug='off', company_name='Off', is_active=False)

    def test_dry_run_does_not_call_cloudinary(self):
        with patch('cloudinary.api.resources') as res:
            out, _ = run('setup_cloudinary_folders', '--dry-run')
        res.assert_not_called()
        self.assertIn('[DRY-RUN] Crearía: acme/sections/', out)
        self.assertNotIn('off/', out)

    def test_existing_and_empty_folders(self):
        responses = [{'resources': [{'public_id': 'x'}]}, {'resources': []},
                     {'resources': []}, {'resources': []}]
        with patch('cloudinary.api.resources', side_effect=responses):
            out, _ = run('setup_cloudinary_folders')
        self.assertIn('acme/sections/ (ya existe)', out)
        self.assertIn('acme/services/ (vacía', out)

    def test_cloudinary_error_is_warning(self):
        with patch('cloudinary.api.resources', side_effect=RuntimeError('boom')):
            out, _ = run('setup_cloudinary_folders', tenant='acme')
        self.assertIn('boom', out)
        self.assertIn('Proceso completado', out)

    def test_unknown_or_inactive_tenant(self):
        for slug in ('nope', 'off'):
            _, err = run('setup_cloudinary_folders', tenant=slug)
            self.assertIn('no encontrado o inactivo', err)


class SetupDevEnvTests(TestCase):
    def setUp(self):
        for slug in ('pro', 'enterprise'):
            Plan.objects.create(name=slug.title(), slug=slug, price=1000)

    def test_missing_plan_gives_clear_error(self):
        Plan.objects.filter(slug='enterprise').delete()
        with self.assertRaisesMessage(CommandError, 'setup_plans'):
            run('setup_dev_env')

    def test_creates_two_tenants_and_admin(self):
        run('setup_dev_env')
        self.assertTrue(User.objects.filter(username='admin', is_superuser=True).exists())
        servelec = Client.objects.get(slug='servelec-ingenieria')
        self.assertEqual(servelec.template, 'themes/servelec')
        self.assertTrue(Domain.objects.filter(client=servelec, domain='servelec.localhost').exists())
        self.assertEqual(Service.objects.filter(client=servelec).count(), 2)
        self.assertEqual(Section.objects.filter(client=servelec).count(), 3)
        self.assertEqual(servelec.settings.primary_color, '#16a34a')
        self.assertTrue(Client.objects.filter(slug='andesscale').exists())
        self.assertEqual(servelec.plan.slug, 'pro')

    def test_is_rerunnable_without_duplicates(self):
        run('setup_dev_env')
        run('setup_dev_env')
        self.assertEqual(User.objects.filter(username='admin').count(), 1)
        servelec = Client.objects.get(slug='servelec-ingenieria')
        self.assertEqual(Service.objects.filter(client=servelec).count(), 2)
        self.assertEqual(Domain.objects.filter(client=servelec).count(), 1)

