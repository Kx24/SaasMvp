"""DASH-05: mensajes del dashboard -- listar, marcar leído y respondido; contador de no leídos."""
from django.urls import reverse

from apps.website.models import ContactSubmission

from .test_support_dashboard import DashboardTestCase


def _msg(tenant, name, **kwargs):
    return ContactSubmission.objects.create(
        client=tenant, name=name, email=f'{name.lower()}@ejemplo.test', message=f'Hola de {name}',
        **kwargs)


class DashboardContactsTests(DashboardTestCase):
    slug = 'dash-msg'

    def setUp(self):
        super().setUp()
        self.ana = _msg(self.tenant, 'Ana')
        self.beto = _msg(self.tenant, 'Beto')
        self.spam = _msg(self.tenant, 'Spammer', is_spam=True, status='spam')
        self.ajeno = _msg(self.other, 'Ajeno')

    def _unread(self, response):
        return response.context['unread_contacts']

    def test_list_shows_only_own_non_spam_messages(self):
        response = self.get(reverse('dashboard_contacts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hola de Ana')
        self.assertContains(response, 'Hola de Beto')
        self.assertNotContains(response, 'Hola de Ajeno')
        self.assertNotContains(response, 'Hola de Spammer')

    def test_status_filter(self):
        ContactSubmission.objects.filter(pk=self.beto.pk).update(status='read')
        response = self.get(reverse('dashboard_contacts') + '?status=new')
        self.assertEqual(list(response.context['contacts']), [self.ana])
        response = self.get(reverse('dashboard_contacts') + '?status=read')
        self.assertEqual(list(response.context['contacts']), [self.beto])

    def test_mark_read_updates_status(self):
        response = self.post(reverse('mark_contact_read', args=[self.ana.id]), follow=True)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.status, 'read')
        self.assertTrue(any('leído' in t for t in self.message_texts(response)))

    def test_mark_replied_updates_status(self):
        response = self.post(reverse('mark_contact_replied', args=[self.ana.id]), follow=True)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.status, 'replied')
        self.assertTrue(any('respondido' in t for t in self.message_texts(response)))

    def test_actions_via_get_change_nothing(self):
        self.get(reverse('mark_contact_read', args=[self.ana.id]))
        self.get(reverse('mark_contact_replied', args=[self.ana.id]))
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.status, 'new')

    def test_cannot_mark_another_tenants_message(self):
        for name in ('mark_contact_read', 'mark_contact_replied'):
            with self.subTest(name):
                self.assertEqual(self.post(reverse(name, args=[self.ajeno.id])).status_code, 404)
        self.ajeno.refresh_from_db()
        self.assertEqual(self.ajeno.status, 'new')

    def test_dashboard_home_metrics_exclude_spam(self):
        response = self.get(reverse('dashboard'))
        self.assertEqual(response.context['total_contacts'], 2)
        self.assertEqual([c.name for c in response.context['recent_contacts']], ['Beto', 'Ana'])

    def test_unread_counter_drops_when_marked_read_and_replied(self):
        page = self.get(reverse('dashboard_contacts'))
        self.assertEqual(self._unread(page), 2)  # Ana y Beto; ni spam ni el de otro tenant
        self.assertContains(page, 'rounded-full badge-primary')

        self.post(reverse('mark_contact_read', args=[self.ana.id]))
        self.assertEqual(self._unread(self.get(reverse('dashboard_contacts'))), 1)

        self.post(reverse('mark_contact_replied', args=[self.beto.id]))
        page = self.get(reverse('dashboard_contacts'))
        self.assertEqual(self._unread(page), 0)
        self.assertNotContains(page, 'rounded-full badge-primary')
