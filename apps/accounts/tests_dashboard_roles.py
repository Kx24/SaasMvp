"""
DASH-04: los roles de ``UserProfile`` tienen efecto en el dashboard.

Matriz en ``apps.accounts.permissions.DASHBOARD_PERMISSIONS``; cada vista la
aplica con ``tenant_permission_required``.
"""
import json

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import get_resolver, reverse

from apps.accounts.models import UserProfile
from apps.accounts.permissions import DASHBOARD_PERMISSIONS, has_dashboard_permission
from apps.tenants.models import Client, ClientSettings, Domain
from apps.website import urls as website_urls
from apps.website.models import ContactSubmission, GalleryItem, Section, Service

ROLES = [code for code, _ in UserProfile.ROLE_CHOICES]

# acción -> nombres de URL (cada vista de la acción se prueba con cada rol)
ACTION_VIEWS = {
    'view_dashboard': ['dashboard', 'dashboard_sections', 'dashboard_gallery'],
    'view_contacts': ['dashboard_contacts'],
    'edit_content': [
        'edit_section_dashboard', 'create_service', 'edit_service_dashboard',
        'toggle_service_active', 'toggle_service_featured', 'reorder_services',
        'gallery_item_add', 'gallery_item_edit', 'gallery_item_toggle',
        'dashboard_portada',
    ],
    'manage_contacts': ['mark_contact_read', 'mark_contact_replied'],
    'delete_content': ['delete_service_dashboard', 'gallery_item_delete'],
    'manage_branding': ['dashboard_branding'],
}

# Vistas de dashboard enrutadas que NO usan tenant_permission_required.
VIEW_EXCEPTIONS = set()


def _mk_client(name, domain):
    c = Client.objects.create(
        name=name, company_name=f'{name} SpA', contact_email=f'{domain}@test.com',
        contact_phone='+56900000001', is_active=True,
    )
    Domain.objects.create(
        client=c, domain=domain, domain_type='custom',
        is_primary=True, is_active=True, is_verified=True,
    )
    return c


class DashboardRolesBase(TestCase):
    HOST_A = 'roles-a.test'
    HOST_B = 'roles-b.test'

    @classmethod
    def setUpTestData(cls):
        cls.client_a = _mk_client('Roles A', cls.HOST_A)
        cls.client_b = _mk_client('Roles B', cls.HOST_B)
        for c in (cls.client_a, cls.client_b):
            ClientSettings.objects.filter(client=c).update(enable_gallery=True)
        cls.users = {}
        for role in ROLES:
            u = User.objects.create_user(username=f'u_{role}', password='pass12345')
            UserProfile.objects.filter(user=u).update(client=cls.client_a, role=role)
            cls.users[role] = u
        cls.owner_b = User.objects.create_user(username='owner_b', password='pass12345')
        UserProfile.objects.filter(user=cls.owner_b).update(client=cls.client_b, role='owner')
        cls.superuser = User.objects.create_superuser(
            username='root', password='pass12345', email='root@test.com')

    def setUp(self):
        self.seed()

    def seed(self):
        """Datos reales del tenant A; se recrean (hay POST que borran)."""
        for model in (GalleryItem, Section, Service, ContactSubmission):
            model.objects.filter(client=self.client_a).delete()
        self.section = Section.objects.create(
            client=self.client_a, section_type='gallery', title='Galería', order=1)
        self.service = Service.objects.create(client=self.client_a, name='Servicio')
        self.item = GalleryItem.objects.create(
            client=self.client_a, section=self.section, title='Img')
        self.contact = ContactSubmission.objects.create(
            client=self.client_a, name='Ana', email='ana@test.com', message='Hola')

    def request_view(self, url_name, host=None):
        """Hace la petición adecuada a la vista. Devuelve la respuesta."""
        host = host or self.HOST_A
        kw = {
            'edit_section_dashboard': {'section_id': self.section.id},
            'edit_service_dashboard': {'service_id': self.service.id},
            'delete_service_dashboard': {'service_id': self.service.id},
            'toggle_service_active': {'service_id': self.service.id},
            'toggle_service_featured': {'service_id': self.service.id},
            'gallery_item_edit': {'item_id': self.item.id},
            'gallery_item_delete': {'item_id': self.item.id},
            'gallery_item_toggle': {'item_id': self.item.id},
            'mark_contact_read': {'contact_id': self.contact.id},
            'mark_contact_replied': {'contact_id': self.contact.id},
        }.get(url_name, {})
        url = reverse(url_name, kwargs=kw)
        post_views = {
            'delete_service_dashboard', 'toggle_service_active', 'toggle_service_featured',
            'gallery_item_delete', 'gallery_item_toggle', 'gallery_item_add',
            'mark_contact_read', 'mark_contact_replied',
        }
        if url_name == 'reorder_services':
            body = json.dumps({'order': [{'id': self.service.id, 'order': 3}]})
            return self.client.post(url, body, content_type='application/json', HTTP_HOST=host)
        if url_name in post_views:
            return self.client.post(url, {}, HTTP_HOST=host)
        return self.client.get(url, HTTP_HOST=host)


class DashboardRoleMatrixTests(DashboardRolesBase):
    def test_table_covers_every_action_and_role(self):
        self.assertEqual(set(ACTION_VIEWS), set(DASHBOARD_PERMISSIONS))
        for roles in DASHBOARD_PERMISSIONS.values():
            self.assertTrue(roles <= set(ROLES))
        self.assertEqual(
            set(ROLES), {'owner', 'admin', 'editor', 'viewer'},
            'Hay un rol nuevo: defínelo en la matriz y en este test.')

    def test_expected_matrix(self):
        expected = {
            'view_dashboard': {'owner', 'admin', 'editor', 'viewer'},
            'view_contacts': {'owner', 'admin', 'editor'},
            'edit_content': {'owner', 'admin', 'editor'},
            'manage_contacts': {'owner', 'admin', 'editor'},
            'delete_content': {'owner', 'admin'},
            'manage_branding': {'owner', 'admin'},
        }
        self.assertEqual({a: set(r) for a, r in DASHBOARD_PERMISSIONS.items()}, expected)

    def test_every_view_by_role(self):
        for action, roles_allowed in DASHBOARD_PERMISSIONS.items():
            for url_name in ACTION_VIEWS[action]:
                for role in ROLES:
                    with self.subTest(action=action, view=url_name, role=role):
                        # estado fresco por subTest (los POST borran/alternan)
                        self.seed()
                        self.client.force_login(self.users[role])
                        resp = self.request_view(url_name)
                        if role in roles_allowed:
                            self.assertIn(resp.status_code, (200, 302))
                        else:
                            self.assertEqual(resp.status_code, 403)
                            self.assertIn('No tienes permiso', resp.content.decode())

    def test_forbidden_mutations_do_not_change_data(self):
        self.client.force_login(self.users['viewer'])
        self.request_view('delete_service_dashboard')
        self.request_view('gallery_item_delete')
        self.request_view('mark_contact_read')
        self.assertTrue(Service.objects.filter(id=self.service.id).exists())
        self.assertTrue(GalleryItem.objects.filter(id=self.item.id).exists())
        self.contact.refresh_from_db()
        self.assertEqual(self.contact.status, 'new')

    def test_unknown_role_gets_nothing(self):
        u = self.users['viewer']
        UserProfile.objects.filter(user=u).update(role='x')
        u = User.objects.get(pk=u.pk)
        for action in DASHBOARD_PERMISSIONS:
            self.assertFalse(has_dashboard_permission(u, self.client_a, action))
        self.client.force_login(u)
        self.assertEqual(self.request_view('dashboard').status_code, 403)

    def test_unauthenticated_redirects_to_login(self):
        resp = self.request_view('dashboard')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/auth/login/', resp['Location'])


class DashboardCrossTenantTests(DashboardRolesBase):
    def test_owner_of_other_tenant_gets_403_everywhere(self):
        self.client.force_login(self.owner_b)
        for urls in ACTION_VIEWS.values():
            for url_name in urls:
                with self.subTest(view=url_name):
                    self.seed()
                    self.assertEqual(self.request_view(url_name).status_code, 403)

    def test_superuser_always_passes(self):
        self.client.force_login(self.superuser)
        for urls in ACTION_VIEWS.values():
            for url_name in urls:
                with self.subTest(view=url_name):
                    self.seed()
                    self.assertIn(self.request_view(url_name).status_code, (200, 302))

    def test_helper_denies_without_profile_or_tenant(self):
        no_profile = User.objects.create_user(username='np', password='pass12345')
        UserProfile.objects.filter(user=no_profile).delete()
        no_profile = User.objects.get(pk=no_profile.pk)
        self.assertFalse(has_dashboard_permission(no_profile, self.client_a, 'view_dashboard'))
        self.assertFalse(has_dashboard_permission(self.users['owner'], None, 'view_dashboard'))
        self.assertFalse(has_dashboard_permission(self.owner_b, self.client_a, 'view_dashboard'))
        self.assertTrue(has_dashboard_permission(self.superuser, None, 'manage_branding'))


class DashboardViewCoverageTests(SimpleTestCase):
    def test_every_dashboard_view_declares_a_permission(self):
        missing = []
        checked = 0
        for pattern in website_urls.urlpatterns:
            route = str(pattern.pattern)
            is_dashboard = route.startswith('dashboard/') or route.startswith('contact/<int')
            if not is_dashboard:
                continue
            checked += 1
            name = pattern.name
            action = getattr(pattern.callback, 'required_permission', None)
            if name in VIEW_EXCEPTIONS:
                continue
            if action not in DASHBOARD_PERMISSIONS:
                missing.append(name)
        self.assertGreaterEqual(checked, 19)
        self.assertEqual(missing, [], 'Vistas sin tenant_permission_required')

    def test_action_views_table_matches_declared_permissions(self):
        resolver = get_resolver()
        for action, names in ACTION_VIEWS.items():
            for name in names:
                with self.subTest(view=name):
                    callback = resolver.resolve(reverse_stub(name)).func
                    self.assertEqual(getattr(callback, 'required_permission', None), action)


def reverse_stub(name):
    args = [1] if name in {
        'edit_section_dashboard', 'edit_service_dashboard', 'delete_service_dashboard',
        'toggle_service_active', 'toggle_service_featured', 'gallery_item_edit',
        'gallery_item_delete', 'gallery_item_toggle', 'mark_contact_read',
        'mark_contact_replied',
    } else []
    return reverse(name, args=args)


class DashboardUiTests(DashboardRolesBase):
    def _html(self, role, url_name):
        self.client.force_login(self.users[role])
        resp = self.client.get(reverse(url_name), HTTP_HOST=self.HOST_A)
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_viewer_does_not_see_edit_delete_branding_or_contacts(self):
        html = self._html('viewer', 'dashboard_sections')
        self.assertNotIn(reverse('edit_section_dashboard', args=[self.section.id]), html)
        self.assertNotIn(reverse('edit_service_dashboard', args=[self.service.id]), html)
        self.assertNotIn(reverse('delete_service_dashboard', args=[self.service.id]), html)
        self.assertNotIn(reverse('create_service'), html)
        self.assertNotIn(reverse('dashboard_branding'), html)
        self.assertNotIn(reverse('dashboard_contacts'), html)

        index = self._html('viewer', 'dashboard')
        self.assertNotIn(reverse('dashboard_contacts'), index)
        self.assertNotIn('ana@test.com', index)

        gallery = self._html('viewer', 'dashboard_gallery')
        self.assertNotIn(reverse('gallery_item_add'), gallery)
        self.assertNotIn(reverse('gallery_item_delete', args=[self.item.id]), gallery)

    def test_editor_sees_edit_but_not_delete_or_branding(self):
        html = self._html('editor', 'dashboard_sections')
        self.assertIn(reverse('edit_service_dashboard', args=[self.service.id]), html)
        self.assertNotIn(reverse('delete_service_dashboard', args=[self.service.id]), html)
        self.assertNotIn(reverse('dashboard_branding'), html)
        self.assertIn(reverse('dashboard_contacts'), html)

    def test_owner_sees_everything(self):
        html = self._html('owner', 'dashboard_sections')
        self.assertIn(reverse('edit_section_dashboard', args=[self.section.id]), html)
        self.assertIn(reverse('edit_service_dashboard', args=[self.service.id]), html)
        self.assertIn(reverse('delete_service_dashboard', args=[self.service.id]), html)
        self.assertIn(reverse('dashboard_branding'), html)
        self.assertIn(reverse('dashboard_contacts'), html)
        index = self._html('owner', 'dashboard')
        self.assertIn('ana@test.com', index)
        gallery = self._html('owner', 'dashboard_gallery')
        self.assertIn(reverse('gallery_item_add'), gallery)
        self.assertIn(reverse('gallery_item_delete', args=[self.item.id]), gallery)
