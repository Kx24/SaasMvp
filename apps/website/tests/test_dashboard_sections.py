"""DASH-05: secciones del dashboard -- editar título, texto e imagen."""
from unittest import mock

from django.urls import reverse

from apps.website.models import Section

from .test_support_dashboard import DESTROY, UPLOAD, DashboardTestCase, png_file, svg_file


class DashboardSectionsTests(DashboardTestCase):
    slug = 'dash-sec'

    def setUp(self):
        super().setUp()
        self.about = Section.objects.create(
            client=self.tenant, section_type='about', title='Quiénes somos',
            description='Texto original', order=20)

    def _edit_url(self, section=None):
        return reverse('edit_section_dashboard', args=[(section or self.about).id])

    def _data(self, **overrides):
        data = {'title': 'Quiénes somos', 'subtitle': '', 'description': 'Texto original',
                'is_active': 'on'}
        data.update(overrides)
        return data

    def test_list_shows_sections(self):
        response = self.get(reverse('dashboard_sections'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quiénes somos')
        self.assertEqual(list(response.context['sections']), [self.about])

    def test_edit_form_loads_current_values(self):
        response = self.get(self._edit_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].instance, self.about)
        self.assertContains(response, 'Texto original')

    def test_edit_title_and_text_persist_and_show_on_home(self):
        response = self.post(self._edit_url(), self._data(
            title='Título nuevo 9Z', subtitle='Sub nuevo', description='Descripción nueva 9Z'))
        self.assertRedirects(response, reverse('dashboard_sections'), fetch_redirect_response=False)
        self.about.refresh_from_db()
        self.assertEqual(self.about.title, 'Título nuevo 9Z')
        self.assertEqual(self.about.subtitle, 'Sub nuevo')
        self.assertEqual(self.about.description, 'Descripción nueva 9Z')

        home = self.get(reverse('home'))
        self.assertContains(home, 'Título nuevo 9Z')
        self.assertNotContains(home, 'Quiénes somos')

    def test_edit_shows_success_message(self):
        response = self.post(self._edit_url(), self._data(title='Otro'), follow=True)
        self.assertTrue(any('actualizada' in t for t in self.message_texts(response)))

    def test_empty_title_is_rejected(self):
        response = self.post(self._edit_url(), self._data(title=''))
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context['form'].errors)
        self.about.refresh_from_db()
        self.assertEqual(self.about.title, 'Quiénes somos')

    def test_too_long_title_is_rejected(self):
        response = self.post(self._edit_url(), self._data(title='x' * 201))
        self.assertEqual(response.status_code, 200)
        self.assertIn('title', response.context['form'].errors)
        self.about.refresh_from_db()
        self.assertEqual(self.about.title, 'Quiénes somos')

    def test_deactivating_section_persists(self):
        data = self._data()
        del data['is_active']
        self.post(self._edit_url(), data)
        self.about.refresh_from_db()
        self.assertFalse(self.about.is_active)

    def test_image_upload_saves_public_id(self):
        with mock.patch(UPLOAD, return_value={'public_id': 'dash-sec/sections/foto'}) as upload:
            response = self.post(self._edit_url(), {**self._data(), 'image': png_file()})
        self.assertEqual(response.status_code, 302)
        upload.assert_called_once()
        self.assertEqual(upload.call_args.kwargs['folder'], 'dash-sec/sections')
        self.about.refresh_from_db()
        self.assertEqual(str(self.about.image), 'dash-sec/sections/foto')

    def test_rejected_image_keeps_other_changes_and_reports_error(self):
        with mock.patch(UPLOAD, return_value={'public_id': 'x'}) as upload:
            response = self.post(
                self._edit_url(), {**self._data(title='Cambio con archivo malo'), 'image': svg_file()},
                follow=True)
        upload.assert_not_called()
        self.about.refresh_from_db()
        self.assertEqual(self.about.title, 'Cambio con archivo malo')
        self.assertFalse(self.about.image)
        self.assertTrue(any('imagen' in t.lower() for t in self.message_texts(response)))

    def test_cloudinary_failure_saves_text_and_reports_error(self):
        with mock.patch(UPLOAD, side_effect=RuntimeError('sin red')):
            response = self.post(
                self._edit_url(), {**self._data(title='Texto sí se guarda'), 'image': png_file()},
                follow=True)
        self.about.refresh_from_db()
        self.assertEqual(self.about.title, 'Texto sí se guarda')
        self.assertFalse(self.about.image)
        self.assertTrue(any('Error al subir' in t for t in self.message_texts(response)))

    def test_clear_image_removes_it(self):
        self.about.image = 'dash-sec/sections/vieja'
        self.about.save()
        with mock.patch(DESTROY) as destroy:
            self.post(self._edit_url(), {**self._data(), 'clear_image': 'on'})
        destroy.assert_called_once()
        self.about.refresh_from_db()
        self.assertFalse(self.about.image)

    def test_cannot_edit_another_tenants_section(self):
        foreign = Section.objects.create(client=self.other, section_type='about', title='Ajena')
        response = self.post(self._edit_url(foreign), self._data(title='Hackeada'))
        self.assertEqual(response.status_code, 404)
        foreign.refresh_from_db()
        self.assertEqual(foreign.title, 'Ajena')
