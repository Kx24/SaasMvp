"""CONS-04: la edición inline pública (htmx) fue eliminada; el dashboard sigue vigente."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import NoReverseMatch, reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain
from apps.website.models import Service

LEGACY_ARGS = {
    'edit_section': [1], 'cancel_edit_section': [1], 'edit_service': [1],
    'cancel_edit_service': [1], 'delete_service': [1], 'add_service': [], 'login_modal': [],
}
HOST = 'legacy.test'


class LegacyRoutesRemovedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Client.objects.create(
            name='Legacy', company_name='Legacy SpA',
            contact_email='l@test.com', contact_phone='+56900000009', is_active=True,
        )
        Domain.objects.create(
            client=cls.tenant, domain=HOST, domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )
        cls.owner = User.objects.create_user(username='legacy_owner', password='pass12345')
        UserProfile.objects.filter(user=cls.owner).update(client=cls.tenant, role='owner')
        cls.service = Service.objects.create(client=cls.tenant, name='Servicio')

    def test_legacy_names_do_not_reverse(self):
        for name, args in LEGACY_ARGS.items():
            with self.subTest(name=name), self.assertRaises(NoReverseMatch):
                reverse(name, args=args)

    def test_legacy_paths_return_404(self):
        self.client.force_login(self.owner)
        for path in ['/section/1/edit/', '/service/1/edit/', '/service/add/', '/login-modal/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path, HTTP_HOST=HOST).status_code, 404)

    def test_dashboard_routes_still_resolve(self):
        for name in ['edit_section_dashboard', 'edit_service_dashboard', 'delete_service_dashboard']:
            with self.subTest(name=name):
                self.assertTrue(reverse(name, args=[1]))

    def test_delete_service_dashboard_get_renders(self):
        self.client.force_login(self.owner)
        url = reverse('delete_service_dashboard', args=[self.service.id])
        self.assertEqual(self.client.get(url, HTTP_HOST=HOST).status_code, 200)
