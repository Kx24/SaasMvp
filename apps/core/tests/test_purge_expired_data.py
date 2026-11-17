"""LEY-03 (resto): plazos de Order, PaymentLog y EmailOutbox."""
from datetime import timedelta
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import EmailOutbox
from apps.orders.models import Order, PaymentLog, Plan
from apps.tenants.models import Client, Domain


def _outbox(status, days):
    o = EmailOutbox.objects.create(
        to_email='x@titular.test', from_email='a@b.cl', subject='s',
        html_content='h', text_content='t', status=status,
    )
    EmailOutbox.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(days=days))
    return o


def _run(*args):
    call_command('purge_expired_data', *args, stdout=StringIO())


class PurgeExpiredDataTests(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(name='P', slug='p-purge', price=1000)

    def _order(self, days, client=None):
        o = Order.objects.create(plan=self.plan, email='c@titular.test', amount=1000, client=client)
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(days=days))
        PaymentLog.objects.create(order=o, action='create')
        return o

    def test_outbox_boundaries(self):
        old_sent, new_sent = _outbox('sent', 91), _outbox('sent', 89)
        old_failed, old_pending = _outbox('failed', 91), _outbox('pending', 200)
        _run()
        alive = set(EmailOutbox.objects.values_list('pk', flat=True))
        self.assertEqual(alive, {new_sent.pk, old_pending.pk})
        self.assertNotIn(old_sent.pk, alive)
        self.assertNotIn(old_failed.pk, alive)

    def test_orders_boundaries_and_payment_logs(self):
        old, recent = self._order(2191), self._order(365 * 5)
        _run()
        self.assertFalse(Order.objects.filter(pk=old.pk).exists())
        self.assertFalse(PaymentLog.objects.filter(order_id=old.pk).exists())
        self.assertTrue(Order.objects.filter(pk=recent.pk).exists())
        self.assertEqual(PaymentLog.objects.filter(order=recent).count(), 1)

    def test_client_survives_order_deletion(self):
        client = Client.objects.create(name='Viva', slug='viva-purge', contact_email='v@x.test')
        self._order(2200, client=client)
        _run()
        self.assertEqual(Order.objects.count(), 0)
        self.assertTrue(Client.objects.filter(pk=client.pk).exists())

    def test_dry_run_deletes_nothing(self):
        _outbox('sent', 200)
        self._order(3000)
        _run('--dry-run')
        self.assertEqual(EmailOutbox.objects.count(), 1)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(PaymentLog.objects.count(), 1)


class DigestInvokesPurgeTests(TestCase):
    PATH = 'apps.tenants.management.commands.send_contact_digest.purge_expired_data'

    def test_digest_calls_purge(self):
        with mock.patch(self.PATH) as m:
            call_command('send_contact_digest', stdout=StringIO(), stderr=StringIO())
        m.assert_called_once_with(dry_run=False)

    def test_digest_respects_dry_run(self):
        with mock.patch(self.PATH) as m:
            call_command('send_contact_digest', '--dry-run', stdout=StringIO(), stderr=StringIO())
        m.assert_called_once_with(dry_run=True)

    def test_digest_continues_if_purge_raises(self):
        out = StringIO()
        with mock.patch(self.PATH, side_effect=RuntimeError('boom')):
            call_command('send_contact_digest', stdout=out, stderr=StringIO())
        self.assertIn('No hay tenants con digest configurado', out.getvalue())


class PolicyMentionsRetentionTests(TestCase):
    def test_rendered_policy_mentions_new_terms(self):
        client = Client.objects.create(name='Pol', slug='pol-purge', contact_email='p@x.test')
        Domain.objects.create(client=client, domain='pol-purge.test', domain_type='custom',
                              is_primary=True, is_active=True, is_verified=True)
        response = self.client.get(reverse('privacy_policy'), HTTP_HOST='pol-purge.test')
        self.assertContains(response, '6 años')
        self.assertContains(response, '90 días')
