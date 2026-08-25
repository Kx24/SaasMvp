"""
Suite de aislamiento multi-tenant real (#MED-02).

Reemplaza `python manage.py test_isolation` (management command manual,
`apps/tenants/management/commands/test_isolation.py`) por tests
automáticos que corren en cada push (gate de §2 del kanban).

Importante: `TenantAwareManager._current_client` (el atributo de clase
que `test_isolation.py` seteaba a mano) nunca se seteaba en código de
request real -- ni el middleware ni ninguna vista lo tocaban, solo ese
comando manual. En producción no filtraba nada: `Model.objects.all()`
devolvía TODOS los tenants. Se eliminó de `apps/tenants/managers.py`
(era código muerto y, de haberse usado alguna vez en una vista, un
riesgo real: atributo de clase = compartido entre requests concurrentes
de distintos tenants). El aislamiento real siempre dependió -- y sigue
dependiendo -- de que cada vista filtre explícitamente por
`client=request.client`. Esta suite prueba eso vía HTTP con `HTTP_HOST`
distinto por tenant, no el manager.

Section/Service ya tienen cobertura de autorización de dashboard en
apps/website/tests/test_tenant_authorization.py (#AUD-03: el gate de
`tenant_member_required` a nivel de dominio). Acá se agrega lo que
faltaba: fuga de contenido en la home pública, y aislamiento a nivel de
objeto (IDOR) para GalleryItem y ContactSubmission, que #AUD-03 no
cubrió.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, Domain
from apps.website.models import ContactSubmission, GalleryItem, Section, Service


class TenantHomePageLeakTestCase(TestCase):
    """La home pública de un tenant nunca debe mostrar contenido de otro."""

    @classmethod
    def setUpTestData(cls):
        cls.client_a = Client.objects.create(name='Tenant A', contact_email='a@test.com')
        Domain.objects.create(
            client=cls.client_a, domain='tenant-a.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )
        cls.client_b = Client.objects.create(name='Tenant B', contact_email='b@test.com')
        Domain.objects.create(
            client=cls.client_b, domain='tenant-b.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

        Service.objects.create(
            client=cls.client_a, name='Servicio Secreto de A', is_active=True,
        )
        Service.objects.create(
            client=cls.client_b, name='Servicio Publico de B', is_active=True,
        )

    def test_home_of_b_never_shows_content_of_a(self):
        response = self.client.get('/', HTTP_HOST='tenant-b.test')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Servicio Secreto de A')
        self.assertContains(response, 'Servicio Publico de B')

    def test_home_of_a_never_shows_content_of_b(self):
        response = self.client.get('/', HTTP_HOST='tenant-a.test')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Servicio Publico de B')
        self.assertContains(response, 'Servicio Secreto de A')


class TenantDashboardObjectIsolationTestCase(TestCase):
    """
    `tenant_member_required` (#AUD-03) ya bloquea el acceso a nivel de
    dominio (owner de A no entra al dashboard de B). Estos tests cubren
    lo que ese gate NO prueba: un owner correctamente autenticado en SU
    PROPIO dominio no debe poder tocar, por ID, un objeto que pertenece
    a otro tenant (IDOR) -- cada vista debe filtrar también por
    `client=request.client` al buscar el objeto.
    """

    @classmethod
    def setUpTestData(cls):
        cls.client_a = Client.objects.create(name='Tenant A', contact_email='a@test.com')
        Domain.objects.create(
            client=cls.client_a, domain='tenant-a.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )
        cls.client_b = Client.objects.create(name='Tenant B', contact_email='b@test.com')
        Domain.objects.create(
            client=cls.client_b, domain='tenant-b.test', domain_type='custom',
            is_primary=True, is_active=True, is_verified=True,
        )

        cls.owner_b = User.objects.create_user(username='owner_b', password='pass12345')
        UserProfile.objects.filter(user=cls.owner_b).update(client=cls.client_b, role='owner')

        cls.client_b.settings.enable_gallery = True
        cls.client_b.settings.save()

        cls.gallery_section_a = Section.objects.create(
            client=cls.client_a, section_type='gallery', title='Galería A',
        )
        cls.gallery_item_a = GalleryItem.objects.create(
            client=cls.client_a, section=cls.gallery_section_a,
            image='tenants/tenant-a/gallery/secreto', title='Foto de A',
        )
        cls.contact_a = ContactSubmission.objects.create(
            client=cls.client_a, name='Cliente de A', email='cliente@a.test',
            message='Consulta confidencial de A',
        )

    def setUp(self):
        self.client.force_login(self.owner_b)

    def _post(self, url_name, kwargs):
        return self.client.post(
            reverse(url_name, kwargs=kwargs), HTTP_HOST='tenant-b.test'
        )

    def test_owner_b_cannot_delete_gallery_item_of_a(self):
        response = self._post('gallery_item_delete', {'item_id': self.gallery_item_a.id})

        self.assertEqual(response.status_code, 404)
        self.assertTrue(GalleryItem.objects.filter(id=self.gallery_item_a.id).exists())

    def test_owner_b_cannot_toggle_gallery_item_of_a(self):
        response = self._post('gallery_item_toggle', {'item_id': self.gallery_item_a.id})

        self.assertEqual(response.status_code, 404)
        self.gallery_item_a.refresh_from_db()
        self.assertTrue(self.gallery_item_a.is_active)

    def test_owner_b_cannot_edit_gallery_item_of_a(self):
        response = self.client.post(
            reverse('gallery_item_edit', kwargs={'item_id': self.gallery_item_a.id}),
            data={'title': 'Hackeado'},
            HTTP_HOST='tenant-b.test',
        )

        self.assertEqual(response.status_code, 404)
        self.gallery_item_a.refresh_from_db()
        self.assertEqual(self.gallery_item_a.title, 'Foto de A')

    def test_owner_b_cannot_mark_contact_of_a_as_read(self):
        response = self._post('mark_contact_read', {'contact_id': self.contact_a.id})

        self.assertEqual(response.status_code, 404)
        self.contact_a.refresh_from_db()
        self.assertEqual(self.contact_a.status, 'new')

    def test_owner_b_dashboard_gallery_never_lists_item_of_a(self):
        response = self.client.get(reverse('dashboard_gallery'), HTTP_HOST='tenant-b.test')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Foto de A')

    def test_owner_b_dashboard_contacts_never_lists_contact_of_a(self):
        response = self.client.get(reverse('dashboard_contacts'), HTTP_HOST='tenant-b.test')

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Consulta confidencial de A')
