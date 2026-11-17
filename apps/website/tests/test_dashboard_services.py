"""DASH-05: servicios del dashboard -- crear, editar, activar, destacar, reordenar, borrar."""
import json
from unittest import mock

from django.urls import reverse

from apps.website.models import Service

from .test_support_dashboard import UPLOAD, DashboardTestCase, png_file


class DashboardServicesTests(DashboardTestCase):
    slug = 'dash-svc'

    def setUp(self):
        super().setUp()
        self.alfa = Service.objects.create(client=self.tenant, name='Alfa 4K', description='d', order=10)
        self.beta = Service.objects.create(client=self.tenant, name='Beta 4K', description='d', order=20)
        self.ajeno = Service.objects.create(client=self.other, name='Ajeno 4K', description='d', order=10)

    # ---- crear ----

    def test_create_persists_for_tenant_and_shows_on_home(self):
        response = self.post(reverse('create_service'), {
            'name': 'Servicio Nuevo 4K', 'description': 'Hace cosas', 'price_text': 'Desde $1',
            'is_active': 'on'})
        self.assertRedirects(response, reverse('dashboard_sections'), fetch_redirect_response=False)
        service = Service.objects.get(name='Servicio Nuevo 4K')
        self.assertEqual(service.client, self.tenant)
        self.assertEqual(service.price_text, 'Desde $1')
        self.assertTrue(service.is_active)
        self.assertContains(self.get(reverse('home')), 'Servicio Nuevo 4K')

    def test_create_shows_success_message_and_lists_it(self):
        response = self.post(reverse('create_service'),
                             {'name': 'Listado 4K', 'description': 'd'}, follow=True)
        self.assertTrue(any('creado' in t for t in self.message_texts(response)))
        self.assertContains(response, 'Listado 4K')

    def test_create_without_name_is_rejected(self):
        before = Service.objects.filter(client=self.tenant).count()
        response = self.post(reverse('create_service'), {'name': '', 'description': 'd'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('name', response.context['form'].errors)
        self.assertEqual(Service.objects.filter(client=self.tenant).count(), before)

    def test_create_blocked_at_plan_limit(self):
        self.tenant.max_services = 2
        self.tenant.save(update_fields=['max_services'])
        response = self.post(reverse('create_service'),
                             {'name': 'De más 4K', 'description': 'd'}, follow=True)
        self.assertFalse(Service.objects.filter(name='De más 4K').exists())
        self.assertTrue(any('Tu plan permite 2' in t for t in self.message_texts(response)))

    def test_create_with_image_uploads_to_tenant_folder(self):
        with mock.patch(UPLOAD, return_value={'public_id': 'dash-svc/services/x'}) as upload:
            self.post(reverse('create_service'),
                      {'name': 'Con foto 4K', 'description': 'd', 'image': png_file()})
        self.assertEqual(upload.call_args.kwargs['folder'], 'dash-svc/services')
        self.assertEqual(str(Service.objects.get(name='Con foto 4K').image), 'dash-svc/services/x')

    # ---- editar ----

    def test_edit_updates_fields(self):
        url = reverse('edit_service_dashboard', args=[self.alfa.id])
        self.assertEqual(self.get(url).status_code, 200)
        response = self.post(url, {'name': 'Alfa Editado 4K', 'description': 'Nueva desc',
                                   'is_active': 'on', 'is_featured': 'on'})
        self.assertRedirects(response, reverse('dashboard_sections'), fetch_redirect_response=False)
        self.alfa.refresh_from_db()
        self.assertEqual(self.alfa.name, 'Alfa Editado 4K')
        self.assertEqual(self.alfa.description, 'Nueva desc')
        self.assertTrue(self.alfa.is_featured)
        self.assertContains(self.get(reverse('home')), 'Alfa Editado 4K')

    def test_edit_with_empty_description_is_rejected(self):
        url = reverse('edit_service_dashboard', args=[self.alfa.id])
        response = self.post(url, {'name': 'Alfa Editado 4K', 'description': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIn('description', response.context['form'].errors)
        self.alfa.refresh_from_db()
        self.assertEqual(self.alfa.name, 'Alfa 4K')

    def test_cannot_edit_another_tenants_service(self):
        url = reverse('edit_service_dashboard', args=[self.ajeno.id])
        self.assertEqual(self.post(url, {'name': 'X', 'description': 'd'}).status_code, 404)
        self.ajeno.refresh_from_db()
        self.assertEqual(self.ajeno.name, 'Ajeno 4K')

    # ---- activar / destacar ----

    def test_toggle_active_flips_and_hides_from_home(self):
        url = reverse('toggle_service_active', args=[self.alfa.id])
        data = self.post(url).json()
        self.assertEqual((data['success'], data['is_active']), (True, False))
        self.alfa.refresh_from_db()
        self.assertFalse(self.alfa.is_active)
        self.assertNotContains(self.get(reverse('home')), 'Alfa 4K')

        self.assertTrue(self.post(url).json()['is_active'])
        self.alfa.refresh_from_db()
        self.assertTrue(self.alfa.is_active)
        self.assertContains(self.get(reverse('home')), 'Alfa 4K')

    def test_toggle_featured_flips(self):
        url = reverse('toggle_service_featured', args=[self.alfa.id])
        self.assertTrue(self.post(url).json()['is_featured'])
        self.alfa.refresh_from_db()
        self.assertTrue(self.alfa.is_featured)
        self.assertFalse(self.post(url).json()['is_featured'])
        self.alfa.refresh_from_db()
        self.assertFalse(self.alfa.is_featured)

    def test_toggles_reject_another_tenants_service(self):
        for name in ('toggle_service_active', 'toggle_service_featured'):
            with self.subTest(name):
                self.assertEqual(self.post(reverse(name, args=[self.ajeno.id])).status_code, 404)
        self.ajeno.refresh_from_db()
        self.assertTrue(self.ajeno.is_active)
        self.assertFalse(self.ajeno.is_featured)

    # ---- reordenar ----

    def _reorder(self, pairs):
        return self.client.post(
            reverse('reorder_services'),
            json.dumps({'order': [{'id': i, 'order': o} for i, o in pairs]}),
            content_type='application/json', HTTP_HOST=self.host)

    def test_reorder_persists_and_changes_home_order(self):
        response = self._reorder([(self.alfa.id, 20), (self.beta.id, 10)])
        self.assertTrue(response.json()['success'])
        self.alfa.refresh_from_db()
        self.beta.refresh_from_db()
        self.assertEqual((self.alfa.order, self.beta.order), (20, 10))
        body = self.get(reverse('home')).content.decode()
        self.assertLess(body.index('Beta 4K'), body.index('Alfa 4K'))
        listed = list(self.get(reverse('dashboard_sections')).context['services'])
        self.assertEqual(listed, [self.beta, self.alfa])

    def test_reorder_never_touches_another_tenant(self):
        response = self._reorder([(self.ajeno.id, 99)])
        self.assertEqual(response.status_code, 404)
        self.ajeno.refresh_from_db()
        self.assertEqual(self.ajeno.order, 10)

    def test_reorder_get_is_refused(self):
        data = self.get(reverse('reorder_services')).json()
        self.assertFalse(data['success'])

    # ---- borrar ----

    def test_delete_asks_for_confirmation_before_deleting(self):
        url = reverse('delete_service_dashboard', args=[self.alfa.id])
        response = self.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alfa 4K')
        self.assertTrue(Service.objects.filter(pk=self.alfa.pk).exists())

    def test_delete_post_removes_it(self):
        url = reverse('delete_service_dashboard', args=[self.alfa.id])
        response = self.post(url, follow=True)
        self.assertFalse(Service.objects.filter(pk=self.alfa.pk).exists())
        self.assertTrue(any('eliminado' in t for t in self.message_texts(response)))
        self.assertNotIn(self.alfa, list(response.context['services']))

    def test_cannot_delete_another_tenants_service(self):
        url = reverse('delete_service_dashboard', args=[self.ajeno.id])
        self.assertEqual(self.post(url).status_code, 404)
        self.assertTrue(Service.objects.filter(pk=self.ajeno.pk).exists())
