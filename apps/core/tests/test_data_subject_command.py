"""
LEY-02 / BOLT-50: comando `data_subject` (export / erase / block / unblock),
siempre acotado a un tenant.
"""
import json
from datetime import timedelta
from io import StringIO

from django.contrib.auth.models import User
from django.core import mail
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.core.models import EmailOutbox
from apps.orders.models import Order, PaymentLog, Plan
from apps.tenants.models import Client, Domain
from apps.website.models import BlockedSubject, ContactSubmission, DataSubjectRequest

EMAIL = 'Persona@Titular.test'


def _tenant(slug, host):
    client = Client.objects.create(name=slug, slug=slug, contact_email=f'{slug}@t.test', is_active=True)
    Domain.objects.create(client=client, domain=host, domain_type='custom',
                          is_primary=True, is_active=True, is_verified=True)
    s = client.settings
    s.digest_enabled = True
    s.digest_frequency = 'daily'
    s.auto_purge_enabled = False
    s.save()
    return client


def _run(*args):
    out = StringIO()
    call_command('data_subject', *args, stdout=out, stderr=StringIO())
    return out.getvalue()


def _populate(client, plan, tag):
    contact = ContactSubmission.objects.create(
        client=client, name=f'Nombre {tag}', email=EMAIL, phone='+5611111', message=f'msg {tag}')
    order = Order.objects.create(
        plan=plan, client=client, email=EMAIL.lower(), buyer_name=f'Comprador {tag}',
        buyer_phone='+5622222', billing_rut='11.111.111-1', ip_address='10.0.0.1',
        amount=12345, status='paid')
    log = PaymentLog.objects.create(
        order=order, action='approve', mp_payment_id=f'mp-{tag}', status='approved', amount=12345,
        ip_address='10.0.0.2',
        raw_data={'id': f'mp-{tag}', 'status': 'approved', 'transaction_amount': 12345,
                  'payer': {'email': EMAIL.lower(), 'first_name': 'Ana'}})
    outbox = EmailOutbox.objects.create(
        client=client, to_email=EMAIL, from_email='x@y.z', subject=f'Asunto {tag}',
        html_content='<p>hola</p>', text_content='hola')
    return contact, order, log, outbox


class DataSubjectBase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(name='P', slug='p-ds', price=10000, available_themes=['default'])
        self.a = _tenant('ds-a', 'ds-a.test')
        self.b = _tenant('ds-b', 'ds-b.test')
        self.a_objs = _populate(self.a, self.plan, 'A')
        self.b_objs = _populate(self.b, self.plan, 'B')


class ExportTests(DataSubjectBase):
    def test_export_includes_requested_tenant_only(self):
        data = json.loads(_run('export', '--email', EMAIL, '--tenant', 'ds-a'))
        self.assertEqual(data['tenant'], 'ds-a')
        self.assertEqual([c['message'] for c in data['contact_messages']], ['msg A'])
        self.assertEqual(len(data['orders']), 1)
        self.assertEqual(data['orders'][0]['buyer_name'], 'Comprador A')
        self.assertEqual(data['orders'][0]['payment_logs'][0]['mp_payment_id'], 'mp-A')
        self.assertEqual([e['subject'] for e in data['queued_emails']], ['Asunto A'])
        self.assertIn('created_at', data['contact_messages'][0])
        raw = json.dumps(data)
        self.assertNotIn('msg B', raw)
        self.assertNotIn('Comprador B', raw)
        self.assertNotIn('Asunto B', raw)

    def test_export_to_file(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'out.json')
            _run('export', '--email', EMAIL, '--tenant', 'ds-a', '--output', path)
            with open(path, encoding='utf-8') as fh:
                self.assertEqual(json.load(fh)['tenant'], 'ds-a')


class EraseTests(DataSubjectBase):
    def test_erase_deletes_contacts_and_outbox_and_anonymizes_order(self):
        out = _run('erase', '--email', EMAIL, '--tenant', 'ds-a')
        self.assertIn('1 mensajes de contacto', out)
        contact, order, log, outbox = self.a_objs
        self.assertFalse(ContactSubmission.objects.filter(pk=contact.pk).exists())
        self.assertFalse(EmailOutbox.objects.filter(pk=outbox.pk).exists())
        order.refresh_from_db()
        self.assertEqual(order.amount, 12345)
        self.assertEqual(order.status, 'paid')
        self.assertEqual(order.buyer_name, '[suprimido]')
        self.assertEqual(order.buyer_phone, '[suprimido]')
        self.assertEqual(order.billing_rut, '[suprimido]')
        self.assertIsNone(order.ip_address)
        self.assertTrue(order.email.startswith('suprimido-'))
        self.assertTrue(order.email.endswith('@invalid'))
        self.assertNotIn('titular', order.email)
        log.refresh_from_db()
        self.assertEqual(log.amount, 12345)
        self.assertEqual(log.status, 'approved')
        self.assertEqual(log.mp_payment_id, 'mp-A')
        self.assertEqual(log.raw_data['id'], 'mp-A')
        self.assertEqual(log.raw_data['transaction_amount'], 12345)
        self.assertNotIn('Ana', json.dumps(log.raw_data))
        self.assertNotIn('titular', json.dumps(log.raw_data))
        self.assertIsNone(log.ip_address)

    def test_erase_does_not_touch_other_tenant(self):
        _run('erase', '--email', EMAIL, '--tenant', 'ds-a')
        contact, order, log, outbox = self.b_objs
        self.assertTrue(ContactSubmission.objects.filter(pk=contact.pk).exists())
        self.assertTrue(EmailOutbox.objects.filter(pk=outbox.pk).exists())
        order.refresh_from_db()
        log.refresh_from_db()
        self.assertEqual(order.buyer_name, 'Comprador B')
        self.assertEqual(order.email, EMAIL.lower())
        self.assertEqual(log.raw_data['payer']['first_name'], 'Ana')

    def test_dry_run_changes_nothing(self):
        out = _run('erase', '--email', EMAIL, '--tenant', 'ds-a', '--dry-run')
        self.assertIn('DRY RUN', out)
        contact, order, log, outbox = self.a_objs
        self.assertTrue(ContactSubmission.objects.filter(pk=contact.pk).exists())
        self.assertTrue(EmailOutbox.objects.filter(pk=outbox.pk).exists())
        order.refresh_from_db()
        self.assertEqual(order.buyer_name, 'Comprador A')


class BlockTests(DataSubjectBase):
    def setUp(self):
        super().setUp()
        self.owner = User.objects.create_user(username='ds_owner', password='pass12345')
        UserProfile.objects.filter(user=self.owner).update(client=self.a, role='owner')
        self.contact = self.a_objs[0]

    def _dashboard_contacts(self):
        self.client.login(username='ds_owner', password='pass12345')
        return self.client.get('/dashboard/contacts/', HTTP_HOST='ds-a.test')

    def test_block_hides_from_dashboard_counters_and_list(self):
        self.assertIn(self.contact, self._dashboard_contacts().context['contacts'])
        _run('block', '--email', EMAIL, '--tenant', 'ds-a')
        self.assertTrue(BlockedSubject.objects.filter(client=self.a, email=EMAIL.lower()).exists())
        self.assertNotIn(self.contact, self._dashboard_contacts().context['contacts'])
        home = self.client.get('/dashboard/', HTTP_HOST='ds-a.test')
        self.assertEqual(home.status_code, 200)
        self.assertEqual(home.context['total_contacts'], 0)
        self.assertEqual(list(home.context['recent_contacts']), [])

    def test_block_hides_from_digest(self):
        _run('block', '--email', EMAIL, '--tenant', 'ds-a')
        call_command('send_contact_digest', stdout=StringIO(), stderr=StringIO())
        bodies = ' '.join(m.alternatives[0][0] for m in mail.outbox if m.alternatives)
        self.assertNotIn('msg A', bodies)
        self.assertNotIn('Nombre A', bodies)

    def test_digest_includes_unblocked_message(self):
        call_command('send_contact_digest', stdout=StringIO(), stderr=StringIO())
        self.assertTrue(any(m.alternatives for m in mail.outbox))

    def test_block_survives_365_day_purge_and_unblock_restores(self):
        old = timezone.now() - timedelta(days=400)
        ContactSubmission.objects.filter(pk=self.contact.pk).update(created_at=old)
        _run('block', '--email', EMAIL, '--tenant', 'ds-a')
        call_command('send_contact_digest', stdout=StringIO(), stderr=StringIO())
        self.assertTrue(ContactSubmission.objects.filter(pk=self.contact.pk).exists())
        _run('unblock', '--email', EMAIL, '--tenant', 'ds-a')
        self.assertFalse(BlockedSubject.objects.filter(client=self.a).exists())
        self.assertIn(self.contact, self._dashboard_contacts().context['contacts'])
        call_command('send_contact_digest', stdout=StringIO(), stderr=StringIO())
        self.assertFalse(ContactSubmission.objects.filter(pk=self.contact.pk).exists())

    def test_block_is_per_tenant(self):
        _run('block', '--email', EMAIL, '--tenant', 'ds-a')
        self.assertFalse(BlockedSubject.objects.filter(client=self.b).exists())

    def test_block_twice_is_idempotent(self):
        _run('block', '--email', EMAIL, '--tenant', 'ds-a')
        _run('block', '--email', EMAIL.upper(), '--tenant', 'ds-a')
        self.assertEqual(BlockedSubject.objects.filter(client=self.a).count(), 1)


class ArgumentTests(DataSubjectBase):
    def test_tenant_is_required(self):
        with self.assertRaises(CommandError):
            _run('export', '--email', EMAIL)

    def test_unknown_tenant_fails(self):
        with self.assertRaises(CommandError):
            _run('export', '--email', EMAIL, '--tenant', 'no-existe')

    def test_request_id_from_other_tenant_is_rejected(self):
        dsr_b = DataSubjectRequest.objects.create(
            client=self.b, request_type='access', name='X', email=EMAIL, detail='d')
        with self.assertRaises(CommandError):
            _run('erase', '--email', EMAIL, '--tenant', 'ds-a', '--request-id', str(dsr_b.pk))
        self.assertTrue(ContactSubmission.objects.filter(pk=self.a_objs[0].pk).exists())

    def test_request_id_records_note_without_changing_status(self):
        dsr = DataSubjectRequest.objects.create(
            client=self.a, request_type='erasure', name='X', email=EMAIL, detail='d')
        _run('erase', '--email', EMAIL, '--tenant', 'ds-a', '--request-id', str(dsr.pk))
        dsr.refresh_from_db()
        self.assertEqual(dsr.status, 'received')
        self.assertIn('data_subject erase', dsr.response_notes)
        self.assertIn('1 mensajes', dsr.response_notes)
