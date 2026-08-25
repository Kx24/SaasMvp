"""
#SEC-03: setup_production ya no crea el superusuario de /superadmin/ con
una contraseña hardcodeada ('admin123456') cuando falta
DJANGO_SUPERUSER_PASSWORD -- en un primer deploy sin esa env var seteada
en Render, la cuenta admin/admin@example.com quedaba con esa clave
publica (visible en este mismo archivo). Mismo patron de fail-fast que
SECRET_KEY/EMAIL_HOST_USER (#AUD-07/#AUD-12).
"""
import io
import os
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class SetupProductionSuperuserTestCase(TestCase):

    @mock.patch.dict(os.environ, {}, clear=False)
    def test_fails_without_password_env_var(self):
        os.environ.pop('DJANGO_SUPERUSER_PASSWORD', None)
        with self.assertRaises(CommandError):
            call_command('setup_production', stdout=io.StringIO())
        self.assertFalse(User.objects.filter(is_superuser=True).exists())

    @mock.patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': 'un-password-real-de-verdad'})
    def test_creates_superuser_with_env_password(self):
        call_command('setup_production', stdout=io.StringIO())
        superuser = User.objects.get(is_superuser=True)
        self.assertEqual(superuser.username, 'admin')
        self.assertTrue(superuser.check_password('un-password-real-de-verdad'))
        # La clave hardcodeada vieja no debe funcionar bajo ningun escenario.
        self.assertFalse(superuser.check_password('admin123456'))

    @mock.patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': 'otra-clave'})
    def test_idempotent_does_not_touch_existing_superuser(self):
        User.objects.create_superuser(
            username='ya-existe', email='ya@existe.cl', password='clave-original'
        )
        call_command('setup_production', stdout=io.StringIO())
        self.assertEqual(User.objects.filter(is_superuser=True).count(), 1)
        existing = User.objects.get(is_superuser=True)
        self.assertEqual(existing.username, 'ya-existe')
        self.assertTrue(existing.check_password('clave-original'))
