"""CONS-13 (parte 2): vistas de onboarding y lista de tenants (solo superuser)."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.tenants.models import Client, Domain
from apps.website.models import Section


def _payload(**over):
    data = {
        'name': 'Nuevo Cliente', 'slug': 'nuevo-cliente', 'domain': 'nuevo.test',
        'template': 'themes/default', 'primary_color': '#112233',
        'secondary_color': '#445566', 'contact_email': 'hola@nuevo.test',
        'whatsapp_number': '+56911112222',
    }
    data.update(over)
    return data


class TenantViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = User.objects.create_superuser(username='tv_root', password='x', email='r@x.test')
        cls.staff = User.objects.create_user(username='tv_staff', password='x', is_staff=True)
        cls.existing = Client.objects.create(name='Existente', slug='existente', company_name='E')

    def test_anonymous_and_staff_are_denied(self):
        for url in (reverse('superadmin_onboarding'), reverse('tenant_list')):
            self.assertEqual(self.client.get(url, HTTP_HOST='localhost').status_code, 302)
        self.client.force_login(self.staff)
        for url in (reverse('superadmin_onboarding'), reverse('tenant_list')):
            self.assertEqual(self.client.get(url, HTTP_HOST='localhost').status_code, 302)

    def test_superuser_sees_form_and_list(self):
        self.client.force_login(self.root)
        self.assertEqual(self.client.get(reverse('superadmin_onboarding'), HTTP_HOST='localhost').status_code, 200)
        resp = self.client.get(reverse('tenant_list'), HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.existing, resp.context['clients'])

    def test_post_valid_creates_tenant_domain_settings_and_hero(self):
        self.client.force_login(self.root)
        resp = self.client.post(reverse('superadmin_onboarding'), _payload(), HTTP_HOST='localhost')
        self.assertRedirects(resp, '/tenants/', fetch_redirect_response=False)
        client = Client.objects.get(slug='nuevo-cliente')
        self.assertEqual(client.template, 'themes/default')
        self.assertTrue(Domain.objects.filter(client=client, domain='nuevo.test', is_primary=True).exists())
        self.assertEqual(client.settings.primary_color, '#112233')
        self.assertEqual(client.settings.whatsapp_number, '+56911112222')
        self.assertTrue(Section.objects.filter(client=client, section_type='hero').exists())

    def test_post_invalid_shows_errors_and_creates_nothing(self):
        self.client.force_login(self.root)
        resp = self.client.post(reverse('superadmin_onboarding'), _payload(template='themes/inexistente'), HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Client.objects.filter(slug='nuevo-cliente').exists())
        self.assertTrue(any('template' in str(m) for m in resp.context['messages']))

    def test_post_duplicate_slug_rolls_back_and_reports_error(self):
        self.client.force_login(self.root)
        resp = self.client.post(reverse('superadmin_onboarding'), _payload(slug='existente'), HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Domain.objects.filter(domain='nuevo.test').exists())
        self.assertEqual(Client.objects.filter(slug='existente').count(), 1)
