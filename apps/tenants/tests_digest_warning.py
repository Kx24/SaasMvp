"""
LEY-08 / BOLT-45: el digest avisa antes de que un mensaje `new` (sin leer)
alcance el tope legal de retención y sea purgado.
"""
from datetime import timedelta
from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.tenants.models import Client
from apps.website.models import ContactSubmission


def _tenant(slug='aviso'):
    client = Client.objects.create(name=slug, slug=slug, contact_email=f'{slug}@aviso.test')
    s = client.settings
    s.digest_enabled = True
    s.digest_frequency = 'daily'
    s.auto_purge_enabled = False
    s.save()
    return client


def _contact(client, *, status='new', age_days=0, name='Remitente Secreto'):
    c = ContactSubmission.objects.create(client=client, name=name, email='secreto@titular.test',
                                         message='hola', status=status)
    ContactSubmission.objects.filter(pk=c.pk).update(created_at=timezone.now() - timedelta(days=age_days))
    return c


def _run(*args):
    out = StringIO()
    call_command('send_contact_digest', *args, stdout=out, stderr=StringIO())
    return out.getvalue()


class DigestPurgeWarningTests(TestCase):
    def setUp(self):
        self.tenant = _tenant()

    def test_new_message_near_cap_includes_warning(self):
        _contact(self.tenant, status='new', age_days=340)
        _run()
        self.assertEqual(len(mail.outbox), 1)
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('data-purge-warning', html)
        self.assertIn('1 mensaje sin leer', html)
        self.assertIn('/dashboard/contacts/', html)
        self.assertNotIn('Remitente Secreto', html)
        self.assertNotIn('secreto@titular.test', html)

    def test_new_message_far_from_cap_has_no_warning(self):
        _contact(self.tenant, status='new', age_days=100)
        _contact(self.tenant, status='new', age_days=0, name='reciente')
        _run()
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn('data-purge-warning', mail.outbox[0].alternatives[0][0])

    def test_read_message_near_cap_has_no_warning(self):
        _contact(self.tenant, status='read', age_days=340)
        _contact(self.tenant, status='new', age_days=0, name='reciente')
        _run()
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn('data-purge-warning', mail.outbox[0].alternatives[0][0])

    def test_digest_sent_when_only_expiring_message(self):
        _contact(self.tenant, status='new', age_days=340)
        _run()
        self.assertEqual(len(mail.outbox), 1)

    def test_no_digest_without_messages_or_expiring(self):
        _contact(self.tenant, status='new', age_days=100)
        _run()
        self.assertEqual(len(mail.outbox), 0)

    def test_dry_run_sends_nothing(self):
        _contact(self.tenant, status='new', age_days=340)
        _run('--dry-run')
        self.assertEqual(len(mail.outbox), 0)
