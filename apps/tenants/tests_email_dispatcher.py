"""BOLT-38 (CONS-11): cobertura de EmailDispatcher — sin red (locmem + mock)."""
from types import SimpleNamespace
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings

from apps.tenants.models import Client, ClientEmailSettings
from apps.tenants.services import email_dispatcher as ed
from apps.tenants.services.email_dispatcher import EmailDispatcher, NotifyResult

LOCMEM = 'django.core.mail.backends.locmem.EmailBackend'


def make_contact(**kw):
    data = dict(id=1, name='Ana', email='ana@cliente.test', phone='', company='',
                subject='Cotización', message='Hola', created_at=None)
    data.update(kw)
    return SimpleNamespace(**data)


@override_settings(EMAIL_BACKEND=LOCMEM)
class DispatcherTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_obj = Client.objects.create(
            name='Acme', slug='acme-mail', contact_email='dueno@acme.test',
            template='themes/default',
        )

    def settings_obj(self, **kw):
        es, _ = ClientEmailSettings.objects.get_or_create(client=self.client_obj)
        for k, v in kw.items():
            setattr(es, k, v)
        es.save()
        return es

    def dispatcher(self):
        return EmailDispatcher(Client.objects.get(pk=self.client_obj.pk))

    # --- email_settings ---
    def test_email_settings_se_crean_si_no_existen(self):
        ClientEmailSettings.objects.filter(client=self.client_obj).delete()
        d = self.dispatcher()
        es = d.email_settings
        self.assertEqual(es.client_id, self.client_obj.pk)
        self.assertIs(d.email_settings, es)  # cacheado

    # --- send_contact_notification ---
    def test_modo_dashboard_se_omite(self):
        self.settings_obj(notify_mode='dashboard', provider='none')
        res = self.dispatcher().send_contact_notification(make_contact())
        self.assertEqual(res.status, NotifyResult.SKIPPED)
        self.assertFalse(res.email_sent)
        self.assertTrue(res.dashboard_logged)
        self.assertEqual(len(mail.outbox), 0)

    def test_modo_email_sin_provider_configurado_se_omite(self):
        self.settings_obj(notify_mode='email', provider='smtp', smtp_host='')
        res = self.dispatcher().send_contact_notification(make_contact())
        self.assertEqual(res.status, NotifyResult.SKIPPED)

    def test_test_mode_no_envia(self):
        self.settings_obj(notify_mode='both', provider='sendgrid', api_key='k', test_mode=True)
        res = self.dispatcher().send_contact_notification(make_contact())
        self.assertEqual(res.status, NotifyResult.TEST_MODE)
        self.assertFalse(res.email_sent)
        self.assertEqual(len(mail.outbox), 0)

    def test_envio_exitoso_con_config_smtp_del_tenant(self):
        self.settings_obj(
            notify_mode='both', provider='smtp', smtp_host='smtp.acme.test',
            smtp_username='u', smtp_password='p', from_email='web@acme.test',
            notify_emails='a@acme.test\n\n b@acme.test ',
        )
        with mock.patch.object(ed, 'get_connection',
                               return_value=mail.get_connection(LOCMEM)) as gc:
            res = self.dispatcher().send_contact_notification(make_contact())
        self.assertEqual(res.status, NotifyResult.SUCCESS)
        self.assertTrue(res.email_sent)
        gc.assert_called_once_with(
            host='smtp.acme.test', port=587, username='u', password='p',
            use_tls=True, use_ssl=False,
        )
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['a@acme.test', 'b@acme.test'])
        self.assertEqual(msg.subject, 'Nuevo contacto de Ana')
        self.assertIn('web@acme.test', msg.from_email)
        self.assertEqual(msg.reply_to, ['ana@cliente.test'])
        self.assertIn('Ana', msg.body)
        self.assertEqual(msg.alternatives[0][1], 'text/html')

    def test_destinatario_cae_a_contact_email_del_cliente_y_reply_to_propio(self):
        self.settings_obj(notify_mode='email', provider='sendgrid', api_key='k',
                          reply_to='resp@acme.test', email_subject_template='{subject} / {email}')
        res = self.dispatcher().send_contact_notification(make_contact(subject=''))
        self.assertEqual(res.status, NotifyResult.SUCCESS)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ['dueno@acme.test'])
        self.assertEqual(msg.reply_to, ['resp@acme.test'])
        self.assertEqual(msg.subject, 'Nuevo contacto / ana@cliente.test')

    def test_copia_al_remitente(self):
        self.settings_obj(notify_mode='both', provider='resend', api_key='k',
                          send_copy_to_sender=True)
        res = self.dispatcher().send_contact_notification(make_contact())
        self.assertEqual(res.status, NotifyResult.SUCCESS)
        self.assertEqual(len(mail.outbox), 2)
        copia = mail.outbox[1]
        self.assertEqual(copia.to, ['ana@cliente.test'])
        self.assertIn('Hemos recibido tu mensaje - Acme', copia.subject)

    def test_copia_al_remitente_con_error_no_rompe_el_envio(self):
        self.settings_obj(notify_mode='both', provider='resend', api_key='k',
                          send_copy_to_sender=True)
        d = self.dispatcher()
        with mock.patch.object(ed, 'render_to_string',
                               side_effect=[ 'h', 't', RuntimeError('tpl')]):
            res = d.send_contact_notification(make_contact())
        self.assertEqual(res.status, NotifyResult.SUCCESS)
        self.assertEqual(len(mail.outbox), 1)

    def test_error_de_conexion_devuelve_failed(self):
        self.settings_obj(notify_mode='email', provider='smtp', smtp_host='h',
                          smtp_username='u')
        boom = mock.Mock()
        boom.send_messages.side_effect = ConnectionRefusedError('smtp caído')
        with mock.patch.object(ed, 'get_connection', return_value=boom):
            with self.assertLogs(ed.logger, level='ERROR'):
                res = self.dispatcher().send_contact_notification(make_contact())
        self.assertEqual(res.status, NotifyResult.FAILED)
        self.assertFalse(res.email_sent)
        self.assertTrue(res.dashboard_logged)
        self.assertIn('smtp caído', res.error)

    def test_sin_destinatarios_devuelve_failed(self):
        Client.objects.filter(pk=self.client_obj.pk).update(contact_email='')
        self.settings_obj(notify_mode='email', provider='sendgrid', api_key='k')
        with self.assertLogs(ed.logger, level='ERROR'):
            res = self.dispatcher().send_contact_notification(make_contact())
        self.assertEqual(res.status, NotifyResult.FAILED)
        self.assertIn('destinatarios', res.error)
        self.assertEqual(len(mail.outbox), 0)

    # --- _get_email_connection ---
    def test_conexion_por_provider(self):
        casos = {
            'sendgrid': dict(host='smtp.sendgrid.net', port=587, username='apikey',
                             password='key', use_tls=True),
            'resend': dict(host='smtp.resend.com', port=465, username='resend',
                           password='key', use_ssl=True),
            'mailgun': dict(host='smtp.mailgun.org', port=587,
                            username='postmaster@acme.test', password='key', use_tls=True),
        }
        for provider, esperado in casos.items():
            with self.subTest(provider=provider):
                self.settings_obj(provider=provider, api_key='key', from_email='x@acme.test')
                with mock.patch.object(ed, 'get_connection') as gc:
                    self.dispatcher()._get_email_connection()
                gc.assert_called_once_with(**esperado)

    def test_mailgun_usa_smtp_username_si_existe(self):
        self.settings_obj(provider='mailgun', api_key='key', smtp_username='custom')
        with mock.patch.object(ed, 'get_connection') as gc:
            self.dispatcher()._get_email_connection()
        self.assertEqual(gc.call_args.kwargs['username'], 'custom')

    def test_provider_sin_conexion_propia_usa_default_de_django(self):
        self.settings_obj(provider='ses')
        with mock.patch.object(ed, 'get_connection') as gc:
            self.dispatcher()._get_email_connection()
        gc.assert_called_once_with()

    # --- test_connection ---
    def test_test_connection_sin_configurar(self):
        self.settings_obj(provider='none', notify_mode='dashboard')
        out = self.dispatcher().test_connection()
        self.assertFalse(out['success'])
        self.assertIn('no configurado', out['error'])

    def test_test_connection_ok_actualiza_estado(self):
        self.settings_obj(provider='sendgrid', notify_mode='email', api_key='k',
                          last_test_error='viejo')
        with mock.patch.object(ed, 'get_connection') as gc:
            out = self.dispatcher().test_connection()
        self.assertTrue(out['success'])
        gc.return_value.open.assert_called_once_with()
        gc.return_value.close.assert_called_once_with()
        es = ClientEmailSettings.objects.get(client=self.client_obj)
        self.assertTrue(es.last_test_success)
        self.assertEqual(es.last_test_error, '')
        self.assertIsNotNone(es.last_test_at)

    def test_test_connection_error_guarda_el_mensaje(self):
        self.settings_obj(provider='sendgrid', notify_mode='email', api_key='k')
        with mock.patch.object(ed, 'get_connection') as gc:
            gc.return_value.open.side_effect = OSError('sin ruta')
            out = self.dispatcher().test_connection()
        self.assertEqual(out, {'success': False, 'error': 'sin ruta'})
        es = ClientEmailSettings.objects.get(client=self.client_obj)
        self.assertFalse(es.last_test_success)
        self.assertEqual(es.last_test_error, 'sin ruta')
