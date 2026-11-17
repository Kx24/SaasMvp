"""BIZ-01: los límites del plan (max_services, max_images) tienen efecto real."""
from unittest import mock

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.tenants import modules
from apps.tenants.models import Client, ClientSettings, Domain
from apps.website.models import GalleryItem, Section, Service

HOST_A = 'limits-a.test'
HOST_B = 'limits-b.test'


def _mk_client(name, domain, **extra):
    c = Client.objects.create(
        name=name, company_name=f'{name} SpA', contact_email=f'{domain}@test.com',
        contact_phone='+56900000001', is_active=True, **extra,
    )
    Domain.objects.create(
        client=c, domain=domain, domain_type='custom',
        is_primary=True, is_active=True, is_verified=True,
    )
    return c


class ModuleLimitsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client_a = _mk_client('Limits A', HOST_A)
        cls.client_b = _mk_client('Limits B', HOST_B)
        cls.owner = User.objects.create_user(username='lim_owner', password='pass12345')
        UserProfile.objects.filter(user=cls.owner).update(client=cls.client_a, role='owner')
        ClientSettings.objects.filter(client=cls.client_a).update(enable_gallery=True)
        cls.section = Section.objects.create(
            client=cls.client_a, section_type='gallery', title='G', order=1)

    def setUp(self):
        self.client.force_login(self.owner)

    def _set(self, **fields):
        Client.objects.filter(pk=self.client_a.pk).update(**fields)
        self.client_a.refresh_from_db()

    def _messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def _mk_services(self, n, client=None):
        for i in range(n):
            Service.objects.create(client=client or self.client_a, name=f'S{i}')

    def _mk_items(self, n):
        for i in range(n):
            GalleryItem.objects.create(client=self.client_a, section=self.section, title=f'I{i}')

    def _post_service(self):
        return self.client.post(
            reverse('create_service'), {'name': 'Nuevo', 'description': 'd'}, HTTP_HOST=HOST_A)

    def _post_image(self):
        png = SimpleUploadedFile('a.png', b'\x89PNG\r\n\x1a\n', content_type='image/png')
        with mock.patch('apps.website.views.gallery._image_upload_ok', return_value=True), \
                mock.patch('cloudinary.uploader.upload', return_value={'public_id': 'x/y'}):
            return self.client.post(
                reverse('gallery_item_add'), {'gallery_type': 'gallery', 'image': png},
                HTTP_HOST=HOST_A)

    # --- registro ---------------------------------------------------------
    def test_limit_for_modulo_sin_limite_es_none(self):
        self.assertIsNone(modules.limit_for(self.client_a, 'core'))
        self.assertIsNone(modules.limit_for(self.client_a, 'contact'))

    def test_limit_para_cero_o_negativo_es_sin_cupo(self):
        self._set(max_services=0)
        self.assertEqual(modules.limit_for(self.client_a, 'services'), 0)
        with self.assertRaises(modules.ModuleLimitReached):
            modules.check_limit(self.client_a, 'services')
        self._set(max_services=-3)
        with self.assertRaises(modules.ModuleLimitReached):
            modules.check_limit(self.client_a, 'services')

    def test_tope_efectivo_galeria_es_el_menor(self):
        self._set(max_images=5)
        ClientSettings.objects.filter(client=self.client_a).update(gallery_images_limit=8)
        self.client_a.refresh_from_db()
        self.assertEqual(modules.limit_for(self.client_a, 'gallery'), 5)
        ClientSettings.objects.filter(client=self.client_a).update(gallery_images_limit=3)
        self.client_a.refresh_from_db()
        self.assertEqual(modules.limit_for(self.client_a, 'gallery'), 3)

    def test_conteo_es_por_tenant(self):
        self._set(max_services=2)
        self._mk_services(5, client=self.client_b)
        self._mk_services(1)
        self.assertEqual(modules.usage_for(self.client_a, 'services'), 1)
        modules.check_limit(self.client_a, 'services')  # no lanza

    # --- servicios --------------------------------------------------------
    def test_create_service_al_tope_no_crea_y_avisa(self):
        self._set(max_services=2)
        self._mk_services(2)
        response = self._post_service()
        self.assertEqual(Service.objects.filter(client=self.client_a).count(), 2)
        self.assertIn(
            'Tu plan permite 2 servicios. Borra uno o pide una ampliación.',
            self._messages(response))

    def test_create_service_bajo_el_tope_crea(self):
        self._set(max_services=2)
        self._mk_services(1)
        self._post_service()
        self.assertEqual(Service.objects.filter(client=self.client_a).count(), 2)

    def test_servicios_de_otro_tenant_no_cuentan(self):
        self._set(max_services=2)
        self._mk_services(3, client=self.client_b)
        self._post_service()
        self.assertEqual(Service.objects.filter(client=self.client_a).count(), 1)

    def test_editar_y_borrar_servicio_al_tope(self):
        self._set(max_services=1)
        self._mk_services(1)
        service = Service.objects.get(client=self.client_a)
        response = self.client.post(
            reverse('edit_service_dashboard', kwargs={'service_id': service.id}),
            {'name': 'Renombrado', 'description': 'd'}, HTTP_HOST=HOST_A)
        self.assertEqual(response.status_code, 302)
        service.refresh_from_db()
        self.assertEqual(service.name, 'Renombrado')
        self.client.post(
            reverse('delete_service_dashboard', kwargs={'service_id': service.id}),
            HTTP_HOST=HOST_A)
        self.assertFalse(Service.objects.filter(client=self.client_a).exists())

    def test_ui_muestra_uso_y_deshabilita_boton_al_tope(self):
        self._set(max_services=2)
        self._mk_services(1)
        html = self.client.get(reverse('dashboard_sections'), HTTP_HOST=HOST_A).content.decode()
        self.assertIn('1 de 2', html)
        self.assertIn(reverse('create_service'), html)
        self._mk_services(1)
        html = self.client.get(reverse('dashboard_sections'), HTTP_HOST=HOST_A).content.decode()
        self.assertIn('2 de 2', html)
        self.assertIn('aria-disabled="true"', html)
        self.assertNotIn(f'href="{reverse("create_service")}"', html)

    # --- galería ----------------------------------------------------------
    def test_gallery_item_add_al_tope_de_plan_no_crea_y_avisa(self):
        self._set(max_images=2)
        self._mk_items(2)
        response = self._post_image()
        self.assertEqual(GalleryItem.objects.filter(client=self.client_a).count(), 2)
        self.assertIn(
            'Tu plan permite 2 imágenes de galería. Borra uno o pide una ampliación.',
            self._messages(response))

    def test_gallery_item_add_bajo_el_tope_crea(self):
        self._set(max_images=2)
        self._mk_items(1)
        self._post_image()
        self.assertEqual(GalleryItem.objects.filter(client=self.client_a).count(), 2)

    def test_gallery_item_add_respeta_el_menor_de_los_dos_topes(self):
        self._set(max_images=10)
        ClientSettings.objects.filter(client=self.client_a).update(gallery_images_limit=1)
        self._mk_items(1)
        self._post_image()
        self.assertEqual(GalleryItem.objects.filter(client=self.client_a).count(), 1)

    def test_editar_y_borrar_imagen_al_tope(self):
        self._set(max_images=1)
        self._mk_items(1)
        item = GalleryItem.objects.get(client=self.client_a)
        response = self.client.post(
            reverse('gallery_item_edit', kwargs={'item_id': item.id}),
            {'title': 'Nuevo título'}, HTTP_HOST=HOST_A)
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.title, 'Nuevo título')
        self.client.post(
            reverse('gallery_item_delete', kwargs={'item_id': item.id}), HTTP_HOST=HOST_A)
        self.assertFalse(GalleryItem.objects.filter(client=self.client_a).exists())

    def test_galeria_ui_usa_el_tope_efectivo(self):
        self._set(max_images=2)
        self._mk_items(1)
        html = self.client.get(reverse('dashboard_gallery'), HTTP_HOST=HOST_A).content.decode()
        self.assertIn('1 de 2 usadas', html)
