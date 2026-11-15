"""
SEC-06 / BOLT-22: smtp_password y api_key de ClientEmailSettings cifradas en reposo.

Los chequeos de "lo que hay en la base" usan SQL directo (connection.cursor()),
no el ORM, porque el ORM descifra al leer.
"""
import importlib
from unittest import mock

from cryptography.fernet import Fernet
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.tenants.models import Client, ClientEmailSettings

KEY_A = Fernet.generate_key().decode()
KEY_B = Fernet.generate_key().decode()
KEY_C = Fernet.generate_key().decode()

PASSWORD = 'smtp-pass-ñ-12345'
API_KEY = 'SG.api-key-67890'


def raw_values(pk):
    with connection.cursor() as cur:
        cur.execute(
            'SELECT smtp_password, api_key FROM tenants_clientemailsettings WHERE id = %s', [pk]
        )
        return cur.fetchone()


def raw_write(pk, smtp_password, api_key):
    with connection.cursor() as cur:
        cur.execute(
            'UPDATE tenants_clientemailsettings SET smtp_password = %s, api_key = %s WHERE id = %s',
            [smtp_password, api_key, pk],
        )


@override_settings(FIELD_ENCRYPTION_KEYS=[KEY_A])
class EncryptedFieldTests(TestCase):
    def setUp(self):
        self.tenant = Client.objects.create(
            name='Enc', company_name='Enc', contact_email='e@e.cl', contact_phone='+56911111111',
        )
        self.es, _ = ClientEmailSettings.objects.get_or_create(client=self.tenant)

    def test_raw_db_value_is_encrypted_for_both_fields(self):
        self.es.smtp_password = PASSWORD
        self.es.api_key = API_KEY
        self.es.save()

        smtp_raw, api_raw = raw_values(self.es.pk)
        self.assertTrue(smtp_raw.startswith('fernet:'))
        self.assertTrue(api_raw.startswith('fernet:'))
        self.assertNotIn(PASSWORD, smtp_raw)
        self.assertNotIn(API_KEY, api_raw)

    def test_orm_roundtrip_returns_plaintext(self):
        self.es.smtp_password = PASSWORD
        self.es.api_key = API_KEY
        self.es.save()

        fresh = ClientEmailSettings.objects.get(pk=self.es.pk)
        self.assertEqual(fresh.smtp_password, PASSWORD)
        self.assertEqual(fresh.api_key, API_KEY)

    def test_empty_values_stay_empty(self):
        self.es.save()
        self.assertEqual(raw_values(self.es.pk), ('', ''))

    def test_legacy_plaintext_row_is_read_as_is(self):
        raw_write(self.es.pk, 'plain-old', 'plain-key')

        fresh = ClientEmailSettings.objects.get(pk=self.es.pk)
        self.assertEqual(fresh.smtp_password, 'plain-old')
        self.assertEqual(fresh.api_key, 'plain-key')

    def test_rotation_reads_old_key_and_resaves_with_new_one(self):
        self.es.smtp_password = PASSWORD
        self.es.save()

        with override_settings(FIELD_ENCRYPTION_KEYS=[KEY_B, KEY_A]):
            rotated = ClientEmailSettings.objects.get(pk=self.es.pk)
            self.assertEqual(rotated.smtp_password, PASSWORD)
            # El valor cifrado con A llega al save ya descifrado: se re-cifra con B.
            rotated.save()

        with override_settings(FIELD_ENCRYPTION_KEYS=[KEY_B]):
            only_b = ClientEmailSettings.objects.get(pk=self.es.pk)
            self.assertEqual(only_b.smtp_password, PASSWORD)

    def test_wrong_key_raises_clear_error(self):
        self.es.smtp_password = PASSWORD
        self.es.save()

        with override_settings(FIELD_ENCRYPTION_KEYS=[KEY_C]):
            with self.assertRaises(ImproperlyConfigured) as ctx:
                ClientEmailSettings.objects.get(pk=self.es.pk)
        self.assertIn('FIELD_ENCRYPTION_KEY', str(ctx.exception))


@override_settings(FIELD_ENCRYPTION_KEYS=[KEY_A])
class DataMigrationTests(TestCase):
    def setUp(self):
        self.migration = importlib.import_module(
            'apps.tenants.migrations.0029_encrypt_email_credentials_data'
        )
        tenant = Client.objects.create(
            name='Mig', company_name='Mig', contact_email='m@m.cl', contact_phone='+56922222222',
        )
        self.es, _ = ClientEmailSettings.objects.get_or_create(client=tenant)

    def test_forward_encrypts_plaintext_rows(self):
        raw_write(self.es.pk, 'plain-pass', 'plain-key')

        self.migration.encrypt_existing(django_apps, None)

        smtp_raw, api_raw = raw_values(self.es.pk)
        self.assertTrue(smtp_raw.startswith('fernet:'))
        self.assertTrue(api_raw.startswith('fernet:'))
        self.assertNotIn('plain-pass', smtp_raw)
        fresh = ClientEmailSettings.objects.get(pk=self.es.pk)
        self.assertEqual((fresh.smtp_password, fresh.api_key), ('plain-pass', 'plain-key'))

    def test_reverse_decrypts_back_to_plaintext(self):
        self.es.smtp_password = 'plain-pass'
        self.es.api_key = 'plain-key'
        self.es.save()
        self.assertTrue(raw_values(self.es.pk)[0].startswith('fernet:'))

        self.migration.decrypt_existing(django_apps, None)

        self.assertEqual(raw_values(self.es.pk), ('plain-pass', 'plain-key'))


@override_settings(FIELD_ENCRYPTION_KEYS=[KEY_A])
class AdminTests(TestCase):
    def setUp(self):
        self.tenant = Client.objects.create(
            name='Adm', company_name='Adm', contact_email='a@a.cl', contact_phone='+56933333333',
        )
        self.es, _ = ClientEmailSettings.objects.get_or_create(client=self.tenant)
        self.es.provider = 'smtp'
        self.es.smtp_password = PASSWORD
        self.es.api_key = API_KEY
        self.es.save()
        user = get_user_model().objects.create_superuser('root', 'root@x.cl', 'pw-12345-xyz')
        self.client.force_login(user)
        self.url = reverse('admin:tenants_clientemailsettings_change', args=[self.es.pk])

    def test_change_form_does_not_render_stored_secrets(self):
        response = self.client.get(self.url, HTTP_HOST='localhost')

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertNotIn(PASSWORD, html)
        self.assertNotIn(API_KEY, html)
        self.assertNotIn('fernet:', html)

    def _post(self, **overrides):
        data = {
            'client': self.tenant.pk,
            'provider': 'smtp',
            'notify_mode': 'dashboard',
            'is_active': 'on',
            'smtp_host': 'smtp.example.com',
            'smtp_port': '587',
            'smtp_username': 'user',
            'smtp_password': '',
            'api_key': '',
            'smtp_use_tls': 'on',
            'email_subject_template': 'Nuevo contacto de {name}',
        }
        data.update(overrides)
        return self.client.post(self.url, data, HTTP_HOST='localhost')

    def test_empty_post_keeps_stored_credentials(self):
        response = self._post(smtp_host='smtp.changed.com')

        self.assertEqual(response.status_code, 302, getattr(response, 'context', None) and
                         response.context['adminform'].form.errors)
        fresh = ClientEmailSettings.objects.get(pk=self.es.pk)
        self.assertEqual(fresh.smtp_host, 'smtp.changed.com')
        self.assertEqual(fresh.smtp_password, PASSWORD)
        self.assertEqual(fresh.api_key, API_KEY)

    def test_new_value_replaces_stored_credential(self):
        response = self._post(smtp_password='nueva-clave')

        self.assertEqual(response.status_code, 302)
        fresh = ClientEmailSettings.objects.get(pk=self.es.pk)
        self.assertEqual(fresh.smtp_password, 'nueva-clave')
        self.assertEqual(fresh.api_key, API_KEY)
        self.assertTrue(raw_values(self.es.pk)[0].startswith('fernet:'))


@override_settings(FIELD_ENCRYPTION_KEYS=[KEY_A])
class DispatcherReceivesPlaintextTests(TestCase):
    def test_smtp_connection_gets_decrypted_password(self):
        from apps.tenants.services.email_dispatcher import EmailDispatcher

        tenant = Client.objects.create(
            name='Disp', company_name='Disp', contact_email='d@d.cl', contact_phone='+56944444444',
        )
        es, _ = ClientEmailSettings.objects.get_or_create(client=tenant)
        es.provider = 'smtp'
        es.smtp_host = 'smtp.example.com'
        es.smtp_password = PASSWORD
        es.save()
        self.assertNotIn(PASSWORD, raw_values(es.pk)[0])

        dispatcher = EmailDispatcher(Client.objects.get(pk=tenant.pk))
        with mock.patch('apps.tenants.services.email_dispatcher.get_connection') as gc:
            dispatcher._get_email_connection()

        self.assertEqual(gc.call_args.kwargs['password'], PASSWORD)
