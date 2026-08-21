"""
Tests de autorización cross-tenant en el dashboard.

#AUD-03: @login_required por sí solo no verifica que el usuario autenticado
pertenezca al tenant del dominio visitado. Sin `tenant_member_required`,
un owner del tenant A logueado puede visitar el dominio del tenant B y
editar/eliminar su contenido -- fuga de datos cross-tenant.

Matriz: {owner A, owner B, superuser, sin profile} x
        {dashboard, edit_section_dashboard, delete_service_dashboard}
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain
from apps.website.models import Section, Service


class TenantAuthorizationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_a = Client.objects.create(
            name='Tenant A', company_name='Tenant A SpA',
            contact_email='a@test.com', contact_phone='+56900000001',
            is_active=True,
        )
        Domain.objects.create(
            client=cls.client_a, domain='tenant-a.test',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )

        cls.client_b = Client.objects.create(
            name='Tenant B', company_name='Tenant B SpA',
            contact_email='b@test.com', contact_phone='+56900000002',
            is_active=True,
        )
        Domain.objects.create(
            client=cls.client_b, domain='tenant-b.test',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )

        cls.owner_a = User.objects.create_user(username='owner_a', password='pass12345')
        UserProfile.objects.filter(user=cls.owner_a).update(client=cls.client_a, role='owner')

        cls.owner_b = User.objects.create_user(username='owner_b', password='pass12345')
        UserProfile.objects.filter(user=cls.owner_b).update(client=cls.client_b, role='owner')

        cls.superuser = User.objects.create_superuser(
            username='root', password='pass12345', email='root@test.com'
        )

        cls.no_profile_user = User.objects.create_user(username='no_profile', password='pass12345')
        UserProfile.objects.filter(user=cls.no_profile_user).delete()

        cls.section_a = Section.objects.create(
            client=cls.client_a, section_type='about', title='Sobre A', order=1,
        )
        cls.service_a = Service.objects.create(
            client=cls.client_a, name='Servicio A',
        )

    def _login_as(self, user):
        self.client.force_login(user)

    def _get(self, url_name, url_kwargs=None):
        url = reverse(url_name, kwargs=url_kwargs or {})
        return self.client.get(url, HTTP_HOST='tenant-b.test')

    def _post(self, url_name, url_kwargs=None, data=None):
        url = reverse(url_name, kwargs=url_kwargs or {})
        return self.client.post(url, data=data or {}, HTTP_HOST='tenant-b.test')

    # ---- dashboard (GET, sin objeto de otro tenant involucrado) ----

    def test_owner_b_can_access_own_dashboard(self):
        self._login_as(self.owner_b)
        response = self._get('dashboard')
        self.assertEqual(response.status_code, 200)

    def test_owner_a_cannot_access_dashboard_of_b(self):
        self._login_as(self.owner_a)
        response = self._get('dashboard')
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_access_dashboard_of_b(self):
        self._login_as(self.superuser)
        response = self._get('dashboard')
        self.assertEqual(response.status_code, 200)

    def test_user_without_profile_cannot_access_dashboard(self):
        self._login_as(self.no_profile_user)
        response = self._get('dashboard')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self._get('dashboard')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/auth/login/', response.url)

    # ---- edit_section_dashboard (objeto de tenant A, visto desde B) ----

    def test_owner_a_cannot_edit_own_section_when_visiting_domain_b(self):
        """Owner de A, logueado, visita el dominio de B: debe rechazarse
        ANTES de tocar la base de datos -- el filtro `client=request.client`
        del get_object_or_404 ya evita filtrar datos de B, pero sin este
        chequeo el owner de A podría editar contenido de B si conociera IDs
        de B. Aquí se prueba con un id de la propia sección de A servida
        desde el dominio de B: debe dar 403, no 404 silencioso."""
        self._login_as(self.owner_a)
        response = self._get(
            'edit_section_dashboard', {'section_id': self.section_a.id}
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_b_editing_nonexistent_own_section_gets_404_not_403(self):
        """Owner de B, en su propio dominio, pidiendo un id que no existe
        para B (es de A) -> 404 del ORM, la autorización ya lo dejó pasar."""
        self._login_as(self.owner_b)
        response = self._get(
            'edit_section_dashboard', {'section_id': self.section_a.id}
        )
        self.assertEqual(response.status_code, 404)

    # ---- delete_service_dashboard (POST, mutación) ----

    def test_owner_a_cannot_delete_service_via_domain_b(self):
        self._login_as(self.owner_a)
        response = self._post(
            'delete_service_dashboard', {'service_id': self.service_a.id}
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Service.objects.filter(id=self.service_a.id).exists())

    def test_superuser_delete_flow_reaches_view_logic(self):
        """No verifica el delete en sí (no es servicio de B), solo que el
        superuser pasa el gate de autorización y llega al 404 del ORM
        (no al 403 de tenant)."""
        self._login_as(self.superuser)
        response = self._post(
            'delete_service_dashboard', {'service_id': self.service_a.id}
        )
        self.assertEqual(response.status_code, 404)
