"""OPS-04: alerta por correo cuando los créditos de Cloudinary cruzan los umbrales."""
import logging
from io import StringIO
from unittest.mock import patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings

API = 'cloudinary.api.usage'


def usage(percent, limit=25):
    return {'credits': {'used': limit * percent / 100, 'limit': limit}}


def run_usage(*args):
    out, err = StringIO(), StringIO()
    call_command('cloudinary_usage', *args, stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


@override_settings(
    PLATFORM_ALERT_EMAIL='ops@example.com',
    CLOUDINARY_ALERT_THRESHOLDS={'warning': 70, 'critical': 90},
)
class CloudinaryUsageAlertTests(TestCase):

    def test_bajo_el_aviso_no_envia(self):
        with patch(API, return_value=usage(50)):
            run_usage('--alert')
        self.assertEqual(len(mail.outbox), 0)

    def test_sin_flag_alert_no_envia(self):
        with patch(API, return_value=usage(95)):
            run_usage()
        self.assertEqual(len(mail.outbox), 0)

    def test_75_envia_aviso(self):
        with patch(API, return_value=usage(75)):
            run_usage('--alert')
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['ops@example.com'])
        self.assertIn('aviso', msg.subject.lower())
        self.assertIn('75', msg.body)

    def test_93_envia_alerta(self):
        with patch(API, return_value=usage(93)):
            run_usage('--alert')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('alerta', mail.outbox[0].subject.lower())
        self.assertIn('93', mail.outbox[0].body)

    def test_sin_destino_no_envia_y_no_falla(self):
        with override_settings(PLATFORM_ALERT_EMAIL=''):
            with self.assertLogs('apps.core.management.commands.cloudinary_usage',
                                 level=logging.WARNING):
                with patch(API, return_value=usage(95)):
                    run_usage('--alert')
        self.assertEqual(len(mail.outbox), 0)

    def test_error_de_api_da_mensaje_claro_sin_excepcion(self):
        with patch(API, side_effect=RuntimeError('boom')):
            out, err = run_usage('--alert')
        self.assertIn('Error obteniendo uso', err)
        self.assertEqual(len(mail.outbox), 0)

    def test_umbrales_salen_del_setting(self):
        with override_settings(CLOUDINARY_ALERT_THRESHOLDS={'warning': 40, 'critical': 60}):
            with patch(API, return_value=usage(50)):
                run_usage('--alert')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('aviso', mail.outbox[0].subject.lower())

        mail.outbox.clear()
        with override_settings(CLOUDINARY_ALERT_THRESHOLDS={'warning': 40, 'critical': 45}):
            with patch(API, return_value=usage(50)):
                run_usage('--alert')
        self.assertIn('alerta', mail.outbox[0].subject.lower())


@override_settings(
    PLATFORM_ALERT_EMAIL='ops@example.com',
    CLOUDINARY_ALERT_THRESHOLDS={'warning': 70, 'critical': 90},
)
class DigestCloudinaryAlertTests(TestCase):

    def _digest(self, *args):
        call_command('send_contact_digest', *args, stdout=StringIO(), stderr=StringIO())

    def _alerts(self):
        return [m for m in mail.outbox if m.to == ['ops@example.com']]

    def test_digest_envia_la_alerta_una_vez(self):
        with patch(API, return_value=usage(93)):
            self._digest()
        self.assertEqual(len(self._alerts()), 1)

    def test_dry_run_no_envia_la_alerta(self):
        with patch(API, return_value=usage(93)):
            self._digest('--dry-run')
        self.assertEqual(len(self._alerts()), 0)

    def test_error_de_api_no_impide_el_digest(self):
        with patch(API, side_effect=RuntimeError('boom')):
            self._digest()  # no debe lanzar
        self.assertEqual(len(self._alerts()), 0)
