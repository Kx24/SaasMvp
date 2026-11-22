"""DASH-05: galería del dashboard -- agregar, editar, ocultar, borrar; archivos no permitidos (SEC-11)."""
from unittest import mock

from django.urls import reverse

from apps.website.models import GalleryItem, Section

from .test_support_dashboard import UPLOAD, DashboardTestCase, png_file, svg_file


class DashboardGalleryTests(DashboardTestCase):
    slug = 'dash-gal'
    gallery = True

    def setUp(self):
        super().setUp()
        self.section = Section.objects.create(
            client=self.tenant, section_type='gallery', title='', order=0)
        self.item = GalleryItem.objects.create(
            client=self.tenant, section=self.section, image='dash-gal/gallery/a', title='Foto A')

    def _add(self, **extra):
        return self.post(reverse('gallery_item_add'), {'gallery_type': 'gallery', **extra})

    # ---- agregar ----

    def test_add_uploads_and_creates_active_item(self):
        with mock.patch(UPLOAD, return_value={'public_id': 'dash-gal/gallery/nueva'}) as upload:
            response = self._add(image=png_file(), title='  Nueva  ', caption='Pie')
        self.assertRedirects(response, reverse('dashboard_gallery'), fetch_redirect_response=False)
        upload.assert_called_once()
        self.assertEqual(upload.call_args.kwargs['folder'], 'dash-gal/gallery')
        item = GalleryItem.objects.get(client=self.tenant, title='Nueva')
        self.assertIn('dash-gal/gallery/nueva', str(item.image))
        self.assertEqual((item.client, item.section), (self.tenant, self.section))
        self.assertEqual((item.title, item.caption, item.is_active), ('Nueva', 'Pie', True))

        listing = self.get(reverse('dashboard_gallery'))
        self.assertIn(item, listing.context['gallery_items'])
        self.assertEqual(listing.context['gallery_used'], 2)

    def test_add_shows_success_message(self):
        with mock.patch(UPLOAD, return_value={'public_id': 'dash-gal/gallery/n'}):
            response = self.post(reverse('gallery_item_add'),
                                 {'gallery_type': 'gallery', 'image': png_file()}, follow=True)
        self.assertTrue(any('agregada' in t for t in self.message_texts(response)))

    def test_add_without_file_is_rejected(self):
        with mock.patch(UPLOAD) as upload:
            response = self.post(reverse('gallery_item_add'),
                                 {'gallery_type': 'gallery'}, follow=True)
        upload.assert_not_called()
        self.assertEqual(GalleryItem.objects.filter(client=self.tenant).count(), 1)
        self.assertTrue(any('Selecciona una imagen' in t for t in self.message_texts(response)))

    def test_add_disallowed_file_is_rejected(self):
        """SEC-11: un SVG nunca llega a Cloudinary ni crea el ítem."""
        with mock.patch(UPLOAD) as upload:
            response = self.post(reverse('gallery_item_add'),
                                 {'gallery_type': 'gallery', 'image': svg_file()}, follow=True)
        upload.assert_not_called()
        self.assertEqual(GalleryItem.objects.filter(client=self.tenant).count(), 1)
        self.assertTrue(any('No se subió la imagen' in t for t in self.message_texts(response)))

    def test_add_cloudinary_failure_creates_nothing(self):
        with mock.patch(UPLOAD, side_effect=RuntimeError('sin red')):
            response = self.post(reverse('gallery_item_add'),
                                 {'gallery_type': 'gallery', 'image': png_file()}, follow=True)
        self.assertEqual(GalleryItem.objects.filter(client=self.tenant).count(), 1)
        self.assertTrue(any('Error al subir' in t for t in self.message_texts(response)))

    def test_add_blocked_at_plan_limit(self):
        self.tenant.max_images = 1
        self.tenant.save(update_fields=['max_images'])
        with mock.patch(UPLOAD) as upload:
            response = self.post(reverse('gallery_item_add'),
                                 {'gallery_type': 'gallery', 'image': png_file()}, follow=True)
        upload.assert_not_called()
        self.assertEqual(GalleryItem.objects.filter(client=self.tenant).count(), 1)
        self.assertTrue(any('Tu plan permite 1' in t for t in self.message_texts(response)))

    def test_add_get_redirects_without_creating(self):
        response = self.get(reverse('gallery_item_add'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GalleryItem.objects.filter(client=self.tenant).count(), 1)

    # ---- editar ----

    def test_edit_updates_text_and_order(self):
        url = reverse('gallery_item_edit', args=[self.item.id])
        self.assertEqual(self.get(url).status_code, 200)
        response = self.post(url, {'title': 'Foto A2', 'caption': 'Nuevo pie', 'order': '5'})
        self.assertRedirects(response, reverse('dashboard_gallery'), fetch_redirect_response=False)
        self.item.refresh_from_db()
        self.assertEqual((self.item.title, self.item.caption, self.item.order), ('Foto A2', 'Nuevo pie', 5))

    def test_edit_replaces_image(self):
        url = reverse('gallery_item_edit', args=[self.item.id])
        with mock.patch(UPLOAD, return_value={'public_id': 'dash-gal/gallery/b'}), \
                mock.patch('cloudinary.uploader.destroy') as destroy:
            self.post(url, {'title': 'Foto A', 'order': '10', 'image': png_file()})
        destroy.assert_called_once()
        self.item.refresh_from_db()
        self.assertEqual(str(self.item.image), 'dash-gal/gallery/b')

    def test_edit_disallowed_replacement_keeps_old_image(self):
        url = reverse('gallery_item_edit', args=[self.item.id])
        with mock.patch(UPLOAD) as upload:
            response = self.post(url, {'title': 'Cambio', 'order': '10', 'image': svg_file()},
                                 follow=True)
        upload.assert_not_called()
        self.item.refresh_from_db()
        self.assertEqual(str(self.item.image), 'dash-gal/gallery/a')
        self.assertEqual(self.item.title, 'Cambio')
        self.assertTrue(any('No se subió la imagen' in t for t in self.message_texts(response)))

    def test_edit_ignores_non_numeric_order(self):
        url = reverse('gallery_item_edit', args=[self.item.id])
        before = self.item.order
        self.post(url, {'title': 'Foto A', 'order': 'abc'})
        self.item.refresh_from_db()
        self.assertEqual(self.item.order, before)

    # ---- ocultar / borrar ----

    def test_toggle_hides_and_shows(self):
        url = reverse('gallery_item_toggle', args=[self.item.id])
        response = self.post(url, follow=True)
        self.item.refresh_from_db()
        self.assertFalse(self.item.is_active)
        self.assertTrue(any('oculta' in t for t in self.message_texts(response)))
        self.post(url)
        self.item.refresh_from_db()
        self.assertTrue(self.item.is_active)

    def test_toggle_get_changes_nothing(self):
        self.get(reverse('gallery_item_toggle', args=[self.item.id]))
        self.item.refresh_from_db()
        self.assertTrue(self.item.is_active)

    def test_delete_post_removes_item(self):
        response = self.post(reverse('gallery_item_delete', args=[self.item.id]), follow=True)
        self.assertFalse(GalleryItem.objects.filter(pk=self.item.pk).exists())
        self.assertTrue(any('eliminada' in t for t in self.message_texts(response)))

    def test_delete_get_does_not_delete(self):
        self.get(reverse('gallery_item_delete', args=[self.item.id]))
        self.assertTrue(GalleryItem.objects.filter(pk=self.item.pk).exists())

    def test_default_image_cannot_be_deleted(self):
        GalleryItem.objects.filter(pk=self.item.pk).update(is_default=True)
        response = self.post(reverse('gallery_item_delete', args=[self.item.id]), follow=True)
        self.assertTrue(GalleryItem.objects.filter(pk=self.item.pk).exists())
        self.assertTrue(any('por defecto' in t for t in self.message_texts(response)))

    def test_cannot_touch_another_tenants_item(self):
        other_section = Section.objects.create(client=self.other, section_type='gallery', title='')
        foreign = GalleryItem.objects.create(client=self.other, section=other_section, image='x/y')
        for name in ('gallery_item_edit', 'gallery_item_delete', 'gallery_item_toggle'):
            with self.subTest(name):
                self.assertEqual(self.post(reverse(name, args=[foreign.id])).status_code, 404)
        foreign.refresh_from_db()
        self.assertTrue(foreign.is_active)
