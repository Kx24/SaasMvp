"""
CONS-13 (parte 1): cobertura de `audit_cloudinary_assets` y `check_cloudinary`.
Cloudinary está siempre parcheado: ninguna llamada de red.
"""
import csv
import os
import tempfile
from io import StringIO
from unittest.mock import patch

import cloudinary
import cloudinary.api
import cloudinary.exceptions
import cloudinary.uploader
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from apps.tenants.models import Client
from apps.website.models import Service

AUDIT = 'apps.core.management.commands.audit_cloudinary_assets'


def run(name, *args, **kwargs):
    out = StringIO()
    call_command(name, *args, stdout=out, stderr=StringIO(), **kwargs)
    return out.getvalue()


class AuditCloudinaryAssetsTests(TestCase):
    def test_fix_and_dry_run_are_mutually_exclusive(self):
        with self.assertRaises(CommandError):
            run('audit_cloudinary_assets', '--fix', '--dry-run')

    def test_no_flags_defaults_to_dry_run_and_never_destroys(self):
        with patch('cloudinary.api.resources',
                   return_value={'resources': [{'public_id': 'tenants/x/a'}]}), \
                patch('cloudinary.uploader.destroy') as destroy:
            out = run('audit_cloudinary_assets')
        self.assertIn('Ejecutando --dry-run por defecto', out)
        self.assertIn('tenants/x/a', out)
        destroy.assert_not_called()

    def test_dry_run_with_tenant_prefix_and_pagination(self):
        pages = [
            {'resources': [{'public_id': 'tenants/acme/a'}], 'next_cursor': 'c1'},
            {'resources': [{'public_id': 'tenants/acme/b'}]},
        ]
        with patch('cloudinary.api.resources', side_effect=pages) as res:
            out = run('audit_cloudinary_assets', '--dry-run', tenant='acme')
        self.assertEqual(res.call_count, 2)
        self.assertEqual(res.call_args_list[0].kwargs['prefix'], 'tenants/acme/')
        self.assertEqual(res.call_args_list[1].kwargs['next_cursor'], 'c1')
        self.assertIn('Assets en Cloudinary: 2', out)

    def test_no_orphans_message(self):
        with patch('cloudinary.api.resources', return_value={'resources': []}):
            out = run('audit_cloudinary_assets', '--dry-run')
        self.assertIn('No se encontraron assets huérfanos', out)

    def test_listing_error_is_reported_not_raised(self):
        with patch('cloudinary.api.resources', side_effect=RuntimeError('boom')):
            out = run('audit_cloudinary_assets', '--dry-run')
        self.assertIn('Error listando Cloudinary: boom', out)

    def test_db_reference_is_not_orphan(self):
        client = Client.objects.create(name='Acme', slug='acme', company_name='Acme')
        # Un CharField legacy con public_id cuenta como referencia.
        Service.objects.create(client=client, name='tenants/acme/ref')
        with patch('cloudinary.api.resources',
                   return_value={'resources': [{'public_id': 'tenants/acme/ref'},
                                               {'public_id': 'tenants/acme/zzz'}]}):
            out = run('audit_cloudinary_assets', '--dry-run', tenant=client.slug)
        self.assertIn('- tenants/acme/zzz', out)
        self.assertNotIn('- tenants/acme/ref', out)
        self.assertIn('Huérfanos detectados: 1', out)

    def test_fix_purges_orphans_and_collects_errors(self):
        listed = {'resources': [{'public_id': 'o/ok'}, {'public_id': 'o/bad'},
                                {'public_id': 'o/exc'}]}

        def destroy(pid, resource_type):
            if pid == 'o/ok':
                return {'result': 'ok'}
            if pid == 'o/bad':
                return {'result': 'not found'}
            raise RuntimeError('net')

        with patch('cloudinary.api.resources', return_value=listed), \
                patch('cloudinary.uploader.destroy', side_effect=destroy):
            out = run('audit_cloudinary_assets', '--fix')
        self.assertIn('Purgados exitosamente: 1', out)
        self.assertIn('Errores al purgar: 2', out)

    def test_fix_without_orphans(self):
        with patch('cloudinary.api.resources', return_value={'resources': []}), \
                patch('cloudinary.uploader.destroy') as destroy:
            out = run('audit_cloudinary_assets', '--fix')
        self.assertIn('No hay huérfanos que purgar', out)
        destroy.assert_not_called()

    def test_report_writes_csv_with_statuses(self):
        listed = {'resources': [{'public_id': 'o/ok'}, {'public_id': 'o/bad'},
                                {'public_id': 'o/left'}]}

        def destroy(pid, resource_type):
            return {'result': 'ok'} if pid == 'o/ok' else {'result': 'error'}

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'r.csv')
            with patch('cloudinary.api.resources', return_value=listed), \
                    patch('cloudinary.uploader.destroy', side_effect=destroy):
                run('audit_cloudinary_assets', '--fix', '--report', output=path)
            with open(path, encoding='utf-8') as f:
                rows = {r['public_id']: r for r in csv.DictReader(f)}
        self.assertEqual(rows['o/ok']['estado'], 'purgado')
        self.assertEqual(rows['o/bad']['estado'], 'error_purga')

    def test_report_default_path_goes_to_scripts_output(self):
        with tempfile.TemporaryDirectory() as tmp, \
                override_settings(BASE_DIR=tmp), \
                patch('cloudinary.api.resources',
                      return_value={'resources': [{'public_id': 'o/a'}]}):
            out = run('audit_cloudinary_assets', '--report')
            files = os.listdir(os.path.join(tmp, 'scripts', 'output'))
        self.assertEqual(len(files), 1)
        self.assertIn('Reporte CSV:', out)

    def test_report_unwritable_path_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch('cloudinary.api.resources', return_value={'resources': []}):
            out = run('audit_cloudinary_assets', '--report',
                      output=os.path.join(tmp, 'no', 'existe', 'r.csv'))
        self.assertIn('No se pudo escribir CSV', out)


class CheckCloudinaryTests(TestCase):
    cfg = dict(CLOUDINARY_CLOUD_NAME='demo', CLOUDINARY_API_KEY='1234567890',
               CLOUDINARY_API_SECRET='s3cret',
               CLOUDINARY_PRESETS={'hero': {}, 'logo': {}})

    def _run(self, usage=None, ping=None, verbose=False):
        with patch('cloudinary.api.ping', **(ping or {'return_value': {'status': 'ok'}})), \
                patch('cloudinary.api.usage',
                      **(usage or {'return_value': {'credits': {'used': 1, 'limit': 25}}})), \
                patch('cloudinary.config', return_value=type('C', (), {'cloud_name': 'demo'})()):
            out = StringIO()
            result = call_command('check_cloudinary', verbose=verbose, stdout=out)
        return out.getvalue(), result

    @override_settings(**cfg)
    def test_happy_path(self):
        out, result = self._run()
        self.assertIsNone(result)
        self.assertIn('CLOUDINARY CONFIGURADO CORRECTAMENTE', out)
        self.assertIn('1234...7890', out)
        self.assertIn('2 presets configurados', out)
        self.assertNotIn('s3cret', out)

    @override_settings(**cfg)
    def test_verbose_prints_usage_details(self):
        out, _ = self._run(verbose=True)
        self.assertIn('Detalles de uso', out)

    @override_settings(**cfg)
    def test_usage_levels(self):
        out, _ = self._run(usage={'return_value': {'credits': {'used': 20, 'limit': 25}}})
        self.assertIn('Atención', out)
        out, _ = self._run(usage={'return_value': {'credits': {'used': 24, 'limit': 25}}})
        self.assertIn('CRÍTICO', out)

    @override_settings(**cfg)
    def test_usage_failure_is_a_warning(self):
        out, result = self._run(usage={'side_effect': RuntimeError('x')})
        self.assertIn('No se pudo obtener uso', out)
        self.assertIsNone(result)

    @override_settings(**{**cfg, 'CLOUDINARY_PRESETS': {}})
    def test_no_presets_warns(self):
        out, _ = self._run()
        self.assertIn('No hay presets configurados', out)

    @override_settings(**cfg)
    def test_auth_error_fails_the_check(self):
        out, result = self._run(
            ping={'side_effect': cloudinary.exceptions.AuthorizationRequired('nope')})
        self.assertIn('Error de autenticación', out)
        self.assertEqual(result, 'Configuration error')

    @override_settings(**cfg)
    def test_connection_error_fails_the_check(self):
        out, result = self._run(ping={'side_effect': RuntimeError('down')})
        self.assertIn('Error de conexión', out)
        self.assertEqual(result, 'Configuration error')

    @override_settings(CLOUDINARY_CLOUD_NAME='', CLOUDINARY_API_KEY='abc',
                       CLOUDINARY_API_SECRET='', CLOUDINARY_PRESETS={})
    def test_missing_settings_reported(self):
        with patch('cloudinary.api.ping', side_effect=RuntimeError('x')), \
                patch('cloudinary.config', return_value=type('C', (), {'cloud_name': ''})()):
            out = StringIO()
            result = call_command('check_cloudinary', stdout=out)
        text = out.getvalue()
        self.assertIn('CLOUDINARY_CLOUD_NAME: No configurado', text)
        self.assertIn('CLOUDINARY_API_SECRET: No configurado', text)
        self.assertIn('****', text)
        self.assertIn('SDK no configurado', text)
        self.assertEqual(result, 'Configuration error')
