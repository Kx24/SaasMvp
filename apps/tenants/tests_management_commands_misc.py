"""
CONS-13 (parte 1): cobertura de `setup_cloudinary_folders`, `setup_dev_env`
y `create_tenant`. Sin red ni escritura fuera de directorios temporales.
"""
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

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

    def test_is_rerunnable_without_duplicates(self):
        run('setup_dev_env')
        run('setup_dev_env')
        self.assertEqual(User.objects.filter(username='admin').count(), 1)
        servelec = Client.objects.get(slug='servelec-ingenieria')
        self.assertEqual(Service.objects.filter(client=servelec).count(), 2)
        self.assertEqual(Domain.objects.filter(client=servelec).count(), 1)


class CreateTenantTests(TestCase):
    def _create(self, *args, **kwargs):
        with tempfile.TemporaryDirectory() as tmp, override_settings(MEDIA_ROOT=tmp):
            out, _ = run('create_tenant', *args, **kwargs)
            self.media_dirs = sorted(
                p.name for p in (Path(tmp) / 'tenants' / 'mi-empresa').iterdir()
            ) if (Path(tmp) / 'tenants' / 'mi-empresa').exists() else []
        return out

    def test_happy_path(self):
        out = self._create('Mi Empresa', 'Mi.Empresa.cl', '--extra-domain=www.mi.cl',
                           '--color=#ff0000', email='a@mi.cl')
        client = Client.objects.get(slug='mi-empresa')
        self.assertEqual(client.settings.primary_color, '#ff0000')
        self.assertEqual(client.settings.secondary_color, '#b20000')
        domains = set(client.domains.values_list('domain', flat=True))
        self.assertIn('mi.empresa.cl', domains)
        self.assertIn('www.mi.cl', domains)
        self.assertEqual(len(domains), 3)  # + subdominio automático
        user = User.objects.get(username='admin_mi-empresa')
        self.assertEqual((user.profile.client, user.profile.role), (client, 'owner'))
        self.assertEqual(self.media_dirs, ['documents', 'images'])
        self.assertEqual(Section.objects.filter(client=client).count(), 3)
        self.assertEqual(Service.objects.filter(client=client).count(), 3)
        self.assertIn('TENANT CREADO EXITOSAMENTE', out)

    def test_no_content(self):
        self._create('Mi Empresa', 'mi.cl', '--no-content')
        client = Client.objects.get(slug='mi-empresa')
        self.assertFalse(Section.objects.filter(client=client).exists())

    def test_copy_templates(self):
        with tempfile.TemporaryDirectory() as base, tempfile.TemporaryDirectory() as media, \
                override_settings(BASE_DIR=base, MEDIA_ROOT=media):
            src = Path(base) / 'templates' / 'tenants' / '_default'
            src.mkdir(parents=True)
            (src / 'x.html').write_text('x')
            out, _ = run('create_tenant', 'Mi Empresa', 'mi.cl', '--copy-templates')
            self.assertTrue((Path(base) / 'templates' / 'tenants' / 'mi-empresa' / 'x.html').exists())
            self.assertIn('Templates copiados', out)
            # Segundo tenant con carpeta ya existente: se omite.
            (Path(base) / 'templates' / 'tenants' / 'otra').mkdir()
            out, _ = run('create_tenant', 'Otra', 'otra.cl', '--copy-templates')
            self.assertIn('Ya existe carpeta de templates', out)

    def test_copy_templates_without_default(self):
        with tempfile.TemporaryDirectory() as base, tempfile.TemporaryDirectory() as media, \
                override_settings(BASE_DIR=base, MEDIA_ROOT=media):
            out, _ = run('create_tenant', 'Mi Empresa', 'mi.cl', '--copy-templates')
        self.assertIn('No existe _default', out)

    def test_duplicate_validations(self):
        Client.objects.create(name='Mi Empresa', slug='mi-empresa', company_name='x')
        with self.assertRaises(CommandError):
            run('create_tenant', 'Mi Empresa', 'nuevo.cl')

        other = Client.objects.create(name='O', slug='o', company_name='O')
        Domain.objects.create(client=other, domain='usado.cl')
        with self.assertRaises(CommandError):
            run('create_tenant', 'Nueva', 'usado.cl')
        with self.assertRaises(CommandError):
            run('create_tenant', 'Nueva', 'libre.cl', '--extra-domain=usado.cl')

        User.objects.create_user('ya', password='x')
        with self.assertRaises(CommandError):
            run('create_tenant', 'Nueva', 'libre.cl', '--username=ya')
        self.assertFalse(Client.objects.filter(slug='nueva').exists())

    def test_darken_color_fallback(self):
        from apps.tenants.management.commands.create_tenant import Command
        self.assertEqual(Command()._darken_color('nope'), '#1e40af')
        self.assertEqual(Command()._darken_color(None), '#1e40af')
