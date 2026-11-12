"""
LEY-03 (parcial) / BOLT-14: la purga de mensajes de contacto no puede
depender del digest.

Antes, `_purge_old_contacts` solo corría dentro del envío del digest: un
tenant con `auto_purge_enabled=True` pero sin digest (o sin mensajes en el
período, o sin email destino, o en un día que no le tocaba) nunca purgaba.
Y los mensajes marcados como spam no se borraban nunca. Ley 21.719: los
datos personales no deben conservarse más de lo necesario (art. 14 d).

Decisión pendiente del usuario (NO cambiada aquí): los mensajes en estado
`new` (sin leer) más antiguos que la retención se conservan.
"""
from datetime import timedelta
from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.tenants.models import Client
from apps.website.models import ContactSubmission

RETENTION = 30


def _tenant(slug, *, purge=True, digest=False):
    client = Client.objects.create(name=slug, slug=slug, contact_email=f'{slug}@purga.test')
    s = client.settings
    s.auto_purge_enabled = purge
    s.digest_enabled = digest
    s.digest_frequency = 'daily'
    s.inbox_retention_days = RETENTION
    s.save()
    return client


def _contact(client, *, status='read', spam=False, age_days=0, name='x'):
    c = ContactSubmission.objects.create(client=client, name=name, email=f'{name}@titular.test',
                                         message='hola', status=status, is_spam=spam)
    ContactSubmission.objects.filter(pk=c.pk).update(created_at=timezone.now() - timedelta(days=age_days))
    return c


def _run(*args):
    call_command('send_contact_digest', *args, stdout=StringIO(), stderr=StringIO())


def _alive(*contacts):
    return set(ContactSubmission.objects.filter(pk__in=[c.pk for c in contacts]).values_list('name', flat=True))


class ContactPurgeTests(TestCase):
    def setUp(self):
        self.tenant = _tenant('purga-sin-digest', purge=True, digest=False)
        old = RETENTION + 5
        self.old_read = _contact(self.tenant, status='read', age_days=old, name='old_read')
        self.old_replied = _contact(self.tenant, status='replied', age_days=old, name='old_replied')
        self.old_spam = _contact(self.tenant, status='new', spam=True, age_days=old, name='old_spam')
        self.old_new = _contact(self.tenant, status='new', age_days=old, name='old_new')
        self.recent_read = _contact(self.tenant, status='read', age_days=2, name='recent_read')
        self.recent_spam = _contact(self.tenant, status='new', spam=True, age_days=2, name='recent_spam')
        self.everyone = (self.old_read, self.old_replied, self.old_spam, self.old_new,
                         self.recent_read, self.recent_spam)

    def test_purges_without_digest(self):
        _run()
        self.assertNotIn('old_read', _alive(*self.everyone))
        self.assertNotIn('old_replied', _alive(*self.everyone))

    def test_purges_old_spam(self):
        _run()
        self.assertNotIn('old_spam', _alive(*self.everyone))

    def test_keeps_recent_and_unread(self):
        _run()
        # `new` antiguo: comportamiento actual conservado (decisión pendiente, LEY-03).
        self.assertEqual(_alive(*self.everyone), {'old_new', 'recent_read', 'recent_spam'})

    def test_dry_run_deletes_nothing(self):
        _run('--dry-run')
        self.assertEqual(len(_alive(*self.everyone)), len(self.everyone))

    def test_tenant_without_auto_purge_keeps_everything(self):
        other = _tenant('sin-purga', purge=False, digest=False)
        kept = [_contact(other, status='read', age_days=RETENTION + 5, name='keep_read'),
                _contact(other, status='new', spam=True, age_days=RETENTION + 5, name='keep_spam')]
        _run()
        self.assertEqual(_alive(*kept), {'keep_read', 'keep_spam'})

    def test_only_target_tenant_with_tenant_flag(self):
        other = _tenant('otro-con-purga', purge=True, digest=False)
        other_old = _contact(other, status='read', age_days=RETENTION + 5, name='other_old')
        _run('--tenant', self.tenant.slug)
        self.assertNotIn('old_read', _alive(*self.everyone))
        self.assertEqual(_alive(other_old), {'other_old'})

    def test_retention_floor_of_seven_days(self):
        s = self.tenant.settings
        s.inbox_retention_days = 1
        s.save(update_fields=['inbox_retention_days'])
        three_days = _contact(self.tenant, status='read', age_days=3, name='three_days')
        _run()
        self.assertEqual(_alive(three_days), {'three_days'})


class DigestStillReportsPurgeTests(TestCase):
    """Con digest activo, el correo sigue informando la purga (comportamiento previo)."""

    def test_digest_email_mentions_purge(self):
        tenant = _tenant('purga-con-digest', purge=True, digest=True)
        _contact(tenant, status='read', age_days=RETENTION + 5, name='viejo')
        _contact(tenant, status='new', age_days=0, name='nuevo')  # para que haya digest
        _run('--force')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Se eliminaron 1 mensaje', mail.outbox[0].alternatives[0][0])
        self.assertFalse(ContactSubmission.objects.filter(client=tenant, name='viejo').exists())
