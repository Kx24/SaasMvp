"""
#DEUDA-02 (Fase 1): GalleryItem sin gallery_type rigido.

gallery_type (2 choices fijas: hero/gallery) se reemplaza por FKs reales a
Section y Service. El "rol" de una imagen sale de item.section.section_type
(Section.SECTION_TYPES ya tiene 5 valores, no 2) o de item.role == 'service'
si esta linkeada a un Service -- sin agregar un enum propio nuevo.

Capacidad nueva verificada aca: un Service puede tener varias fotos (antes
imposible, Service.image era un CloudinaryField unico).
"""
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client as HttpClient
from django.test import TestCase

from apps.accounts.models import UserProfile
from apps.tenants.models import Client, ClientSettings, Domain
from apps.website.models import GalleryItem, Section, Service


class GalleryItemOwnerValidationTestCase(TestCase):
    """clean(): exactamente uno de section/service, y del mismo client."""

    def setUp(self):
        self.client_a = Client.objects.create(name='Tenant A', slug='tenant-a')
        self.client_b = Client.objects.create(name='Tenant B', slug='tenant-b')
        self.section_a = Section.objects.create(
            client=self.client_a, section_type='hero', title='Hero A'
        )
        self.service_a = Service.objects.create(
            client=self.client_a, name='Servicio A', description='desc'
        )

    def test_no_owner_is_invalid(self):
        item = GalleryItem(client=self.client_a, image='x')
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_both_owners_is_invalid(self):
        item = GalleryItem(
            client=self.client_a, image='x',
            section=self.section_a, service=self.service_a,
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_section_from_another_client_is_invalid(self):
        section_b = Section.objects.create(
            client=self.client_b, section_type='hero', title='Hero B'
        )
        item = GalleryItem(client=self.client_a, image='x', section=section_b)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_service_from_another_client_is_invalid(self):
        service_b = Service.objects.create(
            client=self.client_b, name='Servicio B', description='desc'
        )
        item = GalleryItem(client=self.client_a, image='x', service=service_b)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_valid_section_owner(self):
        item = GalleryItem(client=self.client_a, image='x', section=self.section_a)
        item.full_clean()  # no debe lanzar

    def test_valid_service_owner(self):
        item = GalleryItem(client=self.client_a, image='x', service=self.service_a)
        item.full_clean()  # no debe lanzar


class GalleryItemRoleTestCase(TestCase):

    def setUp(self):
        self.client_a = Client.objects.create(name='Tenant A', slug='tenant-a-role')
        self.hero_section = Section.objects.create(
            client=self.client_a, section_type='hero', title='Hero'
        )
        self.gallery_section = Section.objects.create(
            client=self.client_a, section_type='gallery', title='Galeria'
        )
        self.service = Service.objects.create(
            client=self.client_a, name='Servicio', description='desc'
        )

    def test_role_from_hero_section(self):
        item = GalleryItem.objects.create(
            client=self.client_a, image='x', section=self.hero_section
        )
        self.assertEqual(item.role, 'hero')

    def test_role_from_gallery_section(self):
        item = GalleryItem.objects.create(
            client=self.client_a, image='x', section=self.gallery_section
        )
        self.assertEqual(item.role, 'gallery')

    def test_role_from_service(self):
        item = GalleryItem.objects.create(
            client=self.client_a, image='x', service=self.service
        )
        self.assertEqual(item.role, 'service')


class GalleryItemOrderingAndCascadeTestCase(TestCase):

    def setUp(self):
        self.client_a = Client.objects.create(name='Tenant A', slug='tenant-a-order')
        self.section = Section.objects.create(
            client=self.client_a, section_type='gallery', title='Galeria'
        )
        self.service_1 = Service.objects.create(
            client=self.client_a, name='Servicio 1', description='desc'
        )
        self.service_2 = Service.objects.create(
            client=self.client_a, name='Servicio 2', description='desc'
        )

    def test_auto_order_scoped_by_owner_not_shared_globally(self):
        # 2 items en la galeria de section -> orders 10, 20
        GalleryItem.objects.create(client=self.client_a, image='a', section=self.section)
        item2 = GalleryItem.objects.create(client=self.client_a, image='b', section=self.section)
        self.assertEqual(item2.order, 20)

        # el primer item de un Service arranca en 10 (no sigue la secuencia de section)
        service_item = GalleryItem.objects.create(
            client=self.client_a, image='c', service=self.service_1
        )
        self.assertEqual(service_item.order, 10)

    def test_order_does_not_mix_between_two_services(self):
        GalleryItem.objects.create(client=self.client_a, image='a', service=self.service_1)
        item = GalleryItem.objects.create(client=self.client_a, image='b', service=self.service_2)
        self.assertEqual(item.order, 10)

    def test_deleting_section_cascades_to_gallery_items(self):
        item = GalleryItem.objects.create(client=self.client_a, image='a', section=self.section)
        self.section.delete()
        self.assertFalse(GalleryItem.objects.filter(pk=item.pk).exists())

    def test_deleting_service_cascades_to_gallery_items(self):
        item = GalleryItem.objects.create(client=self.client_a, image='a', service=self.service_1)
        self.service_1.delete()
        self.assertFalse(GalleryItem.objects.filter(pk=item.pk).exists())


class DashboardGalleryViewsTestCase(TestCase):
    """dashboard_gallery/dashboard_portada filtran por section_type correcto."""

    def setUp(self):
        self.client_a = Client.objects.create(
            name='Tenant A', slug='tenant-a-dash', is_active=True
        )
        Domain.objects.create(
            client=self.client_a, domain='tenant-a-dash.test',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )
        ClientSettings.objects.filter(client=self.client_a).update(enable_gallery=True)
        self.hero_section = Section.objects.create(
            client=self.client_a, section_type='hero', title='Hero'
        )
        self.gallery_section = Section.objects.create(
            client=self.client_a, section_type='gallery', title='Galeria'
        )
        self.hero_item = GalleryItem.objects.create(
            client=self.client_a, image='hero.jpg', section=self.hero_section
        )
        self.gallery_item = GalleryItem.objects.create(
            client=self.client_a, image='gallery.jpg', section=self.gallery_section
        )

        self.user = User.objects.create_user(username='owner', password='testpass123')
        UserProfile.objects.filter(user=self.user).update(client=self.client_a, role='owner')
        self.http = HttpClient()
        self.http.login(username='owner', password='testpass123')

    def test_dashboard_gallery_only_shows_gallery_items(self):
        response = self.http.get('/dashboard/gallery/', HTTP_HOST='tenant-a-dash.test')
        self.assertEqual(response.status_code, 200)
        items = list(response.context['gallery_items'])
        self.assertEqual(items, [self.gallery_item])

    def test_dashboard_portada_only_shows_hero_items(self):
        response = self.http.get('/dashboard/portada/', HTTP_HOST='tenant-a-dash.test')
        self.assertEqual(response.status_code, 200)
        items = list(response.context['hero_items'])
        self.assertEqual(items, [self.hero_item])


class GalleryItemAddServiceOwnershipTestCase(TestCase):
    """gallery_item_add con service_id -- ownership check cross-tenant (#MED-02)."""

    def setUp(self):
        self.client_a = Client.objects.create(
            name='Tenant A', slug='tenant-a-svc', is_active=True
        )
        Domain.objects.create(
            client=self.client_a, domain='tenant-a-svc.test',
            domain_type='custom', is_primary=True, is_active=True, is_verified=True,
        )
        self.client_b = Client.objects.create(
            name='Tenant B', slug='tenant-b-svc', is_active=True
        )
        ClientSettings.objects.filter(client=self.client_a).update(enable_gallery=True)
        self.service_a = Service.objects.create(
            client=self.client_a, name='Servicio A', description='desc'
        )
        self.service_b = Service.objects.create(
            client=self.client_b, name='Servicio B', description='desc'
        )

        self.user = User.objects.create_user(username='owner-a', password='testpass123')
        UserProfile.objects.filter(user=self.user).update(client=self.client_a, role='owner')
        self.http = HttpClient()
        self.http.login(username='owner-a', password='testpass123')

    def test_cannot_add_image_to_another_tenants_service(self):
        response = self.http.post(
            '/dashboard/gallery/add/',
            {'service_id': self.service_b.id},
            HTTP_HOST='tenant-a-svc.test',
        )
        self.assertIn(response.status_code, (403, 404))
        self.assertEqual(GalleryItem.objects.filter(service=self.service_b).count(), 0)


class TemplateTagsNoRegressionTestCase(TestCase):
    """get_gallery/get_hero_images siguen devolviendo lo mismo que con
    gallery_type -- ahora filtrando por section__section_type."""

    def setUp(self):
        from django.test import RequestFactory

        self.client_a = Client.objects.create(name='Tenant A', slug='tenant-a-tags')
        ClientSettings.objects.filter(client=self.client_a).update(
            enable_gallery=True, show_default_hero=False
        )
        # .update() no invalida el cache de la relacion reversa ya resuelta
        # por el signal de creacion -- sin esto client.settings queda stale.
        self.client_a.refresh_from_db()
        self.hero_section = Section.objects.create(
            client=self.client_a, section_type='hero', title='Hero'
        )
        self.gallery_section = Section.objects.create(
            client=self.client_a, section_type='gallery', title='Galeria'
        )
        self.hero_item = GalleryItem.objects.create(
            client=self.client_a, image='hero.jpg', section=self.hero_section
        )
        self.gallery_item = GalleryItem.objects.create(
            client=self.client_a, image='gallery.jpg', section=self.gallery_section
        )
        # Un item de servicio no debe aparecer en ninguno de los dos tags.
        service = Service.objects.create(
            client=self.client_a, name='Servicio', description='desc'
        )
        GalleryItem.objects.create(client=self.client_a, image='svc.jpg', service=service)

        request = RequestFactory().get('/')
        request.client = self.client_a
        self.context = {'request': request}

    def test_get_gallery_returns_only_gallery_section_items(self):
        from apps.website.templatetags.website_tags import get_gallery
        result = list(get_gallery(self.context))
        self.assertEqual(result, [self.gallery_item])

    def test_get_hero_images_returns_only_hero_section_items(self):
        from apps.website.templatetags.website_tags import get_hero_images
        result = list(get_hero_images(self.context))
        self.assertEqual(result, [self.hero_item])
