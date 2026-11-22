"""LEY-02 (1/2): canal y registro de solicitudes de derechos del titular."""
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain
from apps.website.admin import DataSubjectRequestAdmin
from apps.website.models import DataSubjectRequest

HOST_A = 'dsr-a.test'
HOST_B = 'dsr-b.test'


def _mk_client(name, host, email):
    client = Client.objects.create(name=name, company_name=f'{name} SpA', contact_email=email)
    Domain.objects.create(
        client=client, domain=host, domain_type='custom',
        is_primary=True, is_active=True, is_verified=True,
    )
    cs = client.settings
    cs.contact_email = email
    cs.save()
    return client


def _payload(**extra):
    data = {
        'request_type': 'access',
        'name': 'Ana Titular',
        'email': 'ana@example.test',
        'detail': 'Quiero saber qué datos tienen sobre mí.',
        'website': '',
    }
    data.update(extra)
    return data


@override_settings(EMAIL_ASYNC=False)
class DataSubjectRequestFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = _mk_client('Tenant A', HOST_A, 'datos@a.test')
        cls.b = _mk_client('Tenant B', HOST_B, 'datos@b.test')

    def setUp(self):
        cache.clear()
        self.url = reverse('data_subject_request')

    def _post(self, data=None, host=HOST_A, **kwargs):
        return self.client.post(self.url, data or _payload(), HTTP_HOST=host, **kwargs)

    def test_get_shows_form(self):
        response = self.client.get(self.url, HTTP_HOST=HOST_A)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'name="request_type"')

    def test_valid_post_creates_request_for_right_tenant_with_30_day_due(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self._post()
        self.assertEqual(response.status_code, 302)
        dsr = DataSubjectRequest.objects.get()
        self.assertEqual(dsr.client, self.a)
        self.assertEqual(dsr.status, 'received')
        self.assertEqual(dsr.email, 'ana@example.test')
        self.assertEqual(dsr.request_type, 'access')
        self.assertTrue(dsr.ip_address)
        delta = dsr.due_at - dsr.received_at
        self.assertLess(abs(delta - timedelta(days=30)), timedelta(seconds=5))

    def test_success_page_is_the_same_for_any_email(self):
        existing = self._post(_payload(email='known@example.test'))
        other = self._post(_payload(email='nobody@example.test'), REMOTE_ADDR='10.9.9.9')
        self.assertEqual(existing.status_code, other.status_code)
        self.assertEqual(existing['Location'], other['Location'])
        page = self.client.get(existing['Location'], HTTP_HOST=HOST_A)
        self.assertContains(page, 'Recibimos tu solicitud')

    def test_invalid_post_is_400_and_creates_nothing(self):
        response = self._post(_payload(request_type='', email='no-es-correo'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(DataSubjectRequest.objects.count(), 0)

    def test_honeypot_creates_nothing_and_looks_like_success(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self._post(_payload(website='http://spam.test'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DataSubjectRequest.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_rate_limit_per_ip(self):
        for _ in range(3):
            self.assertEqual(self._post().status_code, 302)
        response = self._post()
        self.assertEqual(response.status_code, 429)
        self.assertEqual(DataSubjectRequest.objects.count(), 3)

    def test_system_domain_without_tenant_is_404(self):
        self.assertEqual(self.client.get(self.url, HTTP_HOST='localhost').status_code, 404)
        self.assertEqual(self.client.post(self.url, _payload(), HTTP_HOST='localhost').status_code, 404)
        self.assertEqual(DataSubjectRequest.objects.count(), 0)

    def test_both_emails_go_out_after_commit(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            self._post()
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(len(callbacks), 1)
        for callback in callbacks:
            callback()
        self.assertEqual(len(mail.outbox), 2)
        receipt = next(m for m in mail.outbox if m.to == ['ana@example.test'])
        notice = next(m for m in mail.outbox if m.to == ['datos@a.test'])
        due = DataSubjectRequest.objects.get().due_at
        self.assertIn(timezone.localtime(due).strftime('%d/%m/%Y'), receipt.body)
        self.assertIn('ana@example.test', notice.body)

    def test_no_email_if_transaction_fails(self):
        self.client.raise_request_exception = False
        with mock.patch.object(DataSubjectRequest, 'save', side_effect=RuntimeError('boom')):
            with self.captureOnCommitCallbacks(execute=True):
                response = self._post()
        self.assertEqual(response.status_code, 500)
        self.assertEqual(DataSubjectRequest.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_platform_tenant_notice_goes_to_platform_email(self):
        with override_settings(PLATFORM_TENANT_SLUG=self.b.slug, SUPPORT_EMAIL='plataforma@andes.test'):
            with self.captureOnCommitCallbacks(execute=True):
                self._post(host=HOST_B)
        recipients = {addr for m in mail.outbox for addr in m.to}
        self.assertIn('plataforma@andes.test', recipients)
        self.assertNotIn('datos@b.test', recipients)

    def test_policy_pages_link_to_the_form(self):
        response = self.client.get(reverse('privacy_policy'), HTTP_HOST=HOST_A)
        self.assertContains(response, f'href="{self.url}"')
        with override_settings(PLATFORM_TENANT_SLUG=self.a.slug):
            response = self.client.get(reverse('privacy_policy'), HTTP_HOST=HOST_A)
        self.assertContains(response, f'href="{self.url}"')


class DataSubjectRequestAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = _mk_client('Tenant A', HOST_A, 'datos@a.test')
        cls.b = _mk_client('Tenant B', HOST_B, 'datos@b.test')
        cls.dsr_a = DataSubjectRequest.objects.create(
            client=cls.a, request_type='access', name='A', email='a@x.test', detail='d')
        cls.dsr_b = DataSubjectRequest.objects.create(
            client=cls.b, request_type='erasure', name='B', email='b@x.test', detail='d')
        cls.staff_a = User.objects.create_user('staff_a', password='x', is_staff=True)
        UserProfile.objects.filter(user=cls.staff_a).update(client=cls.a, role='admin')
        cls.root = User.objects.create_superuser('root', 'root@x.test', 'x')

    def test_admin_queryset_is_scoped_by_tenant(self):
        model_admin = DataSubjectRequestAdmin(DataSubjectRequest, admin_site=mock.Mock())
        request = RequestFactory().get('/')
        request.user = User.objects.get(pk=self.staff_a.pk)
        self.assertEqual(list(model_admin.get_queryset(request)), [self.dsr_a])
        request.user = self.root
        self.assertEqual(model_admin.get_queryset(request).count(), 2)

    def test_remaining_days_column(self):
        model_admin = DataSubjectRequestAdmin(DataSubjectRequest, admin_site=mock.Mock())
        self.assertIn('vence en', model_admin.vence_en(self.dsr_a))
        DataSubjectRequest.objects.filter(pk=self.dsr_a.pk).update(
            due_at=timezone.now() - timedelta(days=2))
        self.dsr_a.refresh_from_db()
        self.assertEqual(model_admin.vence_en(self.dsr_a), 'vencida')

    def _change(self, **data):
        self.client.force_login(self.root)
        url = reverse('admin:website_datasubjectrequest_change', args=[self.dsr_a.pk])
        return self.client.post(url, data, HTTP_HOST='localhost')

    def test_resolving_without_notes_is_rejected(self):
        response = self._change(status='resolved', response_notes='  ')
        self.assertEqual(response.status_code, 200)
        self.dsr_a.refresh_from_db()
        self.assertEqual(self.dsr_a.status, 'received')
        self.assertIsNone(self.dsr_a.resolved_at)

    def test_resolving_with_notes_stamps_resolved_at(self):
        response = self._change(status='resolved', response_notes='Enviamos los datos por correo.')
        self.assertEqual(response.status_code, 302)
        self.dsr_a.refresh_from_db()
        self.assertEqual(self.dsr_a.status, 'resolved')
        self.assertIsNotNone(self.dsr_a.resolved_at)

    def test_rejecting_requires_notes_too(self):
        response = self._change(status='rejected', response_notes='')
        self.assertEqual(response.status_code, 200)
        self.dsr_a.refresh_from_db()
        self.assertEqual(self.dsr_a.status, 'received')


class DataSubjectRequestDashboardNoticeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a = _mk_client('Tenant A', HOST_A, 'datos@a.test')
        cls.b = _mk_client('Tenant B', HOST_B, 'datos@b.test')
        for role in ('admin', 'viewer'):
            user = User.objects.create_user(f'{role}_a', password='x')
            UserProfile.objects.filter(user=user).update(client=cls.a, role=role)
        owner_b = User.objects.create_user('owner_b', password='x')
        UserProfile.objects.filter(user=owner_b).update(client=cls.b, role='owner')

    def _dashboard(self, username, host):
        self.client.force_login(User.objects.get(username=username))
        return self.client.get(reverse('dashboard'), HTTP_HOST=host)

    def test_notice_shows_count_and_nearest_due_date(self):
        first = DataSubjectRequest.objects.create(
            client=self.a, request_type='access', name='A1', email='1@x.test', detail='d')
        DataSubjectRequest.objects.create(
            client=self.a, request_type='erasure', name='A2', email='2@x.test', detail='d')
        response = self._dashboard('admin_a', HOST_A)
        self.assertContains(response, 'Tienes 2 solicitudes de datos personales')
        self.assertContains(response, timezone.localtime(first.due_at).strftime('%d/%m/%Y'))

    def test_viewer_does_not_see_notice(self):
        DataSubjectRequest.objects.create(
            client=self.a, request_type='access', name='A1', email='1@x.test', detail='d')
        response = self._dashboard('viewer_a', HOST_A)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'solicitud de datos personales')
        self.assertNotContains(response, 'solicitudes de datos personales')

    def test_other_tenant_requests_are_not_counted(self):
        DataSubjectRequest.objects.create(
            client=self.b, request_type='access', name='B1', email='b@x.test', detail='d')
        response = self._dashboard('admin_a', HOST_A)
        self.assertNotContains(response, 'de datos personales;')
        response_b = self._dashboard('owner_b', HOST_B)
        self.assertContains(response_b, 'Tienes 1 solicitud de datos personales')

    def test_closed_requests_do_not_trigger_notice(self):
        DataSubjectRequest.objects.create(
            client=self.a, request_type='access', name='A1', email='1@x.test', detail='d',
            status='resolved', response_notes='ok')
        response = self._dashboard('admin_a', HOST_A)
        self.assertNotContains(response, 'de datos personales;')
