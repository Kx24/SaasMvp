"""DASH-05: marca del dashboard -- colores, fuente y logo; valores inválidos; la home refleja los tokens."""
from unittest import mock

from cloudinary import CloudinaryResource
from django.urls import reverse

from apps.tenants.forms import BrandingForm

from .test_support_dashboard import DashboardTestCase, png_file, svg_file


class DashboardBrandingTests(DashboardTestCase):
    slug = 'dash-brand'

    def _data(self, **overrides):
        settings_obj = self.tenant.settings
        data = {f: getattr(settings_obj, f) or '' for f in BrandingForm.Meta.fields
                if f not in ('logo', 'logo_footer')}
        data.update(overrides)
        return data

    def _settings(self):
        self.tenant.settings.refresh_from_db()
        return self.tenant.settings

    def test_page_loads_with_current_values(self):
        response = self.get(reverse('dashboard_branding'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].instance, self.tenant.settings)

    def test_change_colors_and_font_persist_and_home_shows_tokens(self):
        response = self.post(reverse('dashboard_branding'), self._data(
            primary_color='#112233', secondary_color='#445566', accent_color='#778899',
            font_family='Outfit'))
        self.assertRedirects(response, reverse('dashboard_branding'), fetch_redirect_response=False)
        s = self._settings()
        self.assertEqual((s.primary_color, s.secondary_color, s.accent_color, s.font_family),
                         ('#112233', '#445566', '#778899', 'Outfit'))

        home = self.get(reverse('home'))
        self.assertContains(home, '--color-primary:   #112233')
        self.assertContains(home, '--color-secondary: #445566')

    def test_success_message_is_shown(self):
        response = self.post(reverse('dashboard_branding'),
                             self._data(tagline='Nuevo lema'), follow=True)
        self.assertTrue(any('guardados' in t for t in self.message_texts(response)))
        self.assertEqual(self._settings().tagline, 'Nuevo lema')

    def test_invalid_colors_are_rejected(self):
        original = self._settings().primary_color
        for bad in ('rojo', '#ZZZZZZ', '#12345', 'red;}', '112233', '#1234567'):
            with self.subTest(bad):
                response = self.post(reverse('dashboard_branding'), self._data(primary_color=bad))
                self.assertEqual(response.status_code, 200)
                self.assertIn('primary_color', response.context['form'].errors)
                self.assertEqual(self._settings().primary_color, original)

    def test_invalid_secondary_and_accent_colors_are_rejected(self):
        for field in ('secondary_color', 'accent_color'):
            with self.subTest(field):
                response = self.post(reverse('dashboard_branding'), self._data(**{field: '#GGGGGG'}))
                self.assertEqual(response.status_code, 200)
                self.assertIn(field, response.context['form'].errors)

    def test_error_message_when_form_invalid(self):
        response = self.post(reverse('dashboard_branding'),
                             self._data(primary_color='nope'))
        self.assertTrue(any('errores' in t for t in self.message_texts(response)))

    def test_unknown_font_is_rejected(self):
        original = self._settings().font_family
        response = self.post(reverse('dashboard_branding'), self._data(font_family='Comic Papyrus'))
        self.assertIn('font_family', response.context['form'].errors)
        self.assertEqual(self._settings().font_family, original)

    def test_invalid_email_is_rejected(self):
        response = self.post(reverse('dashboard_branding'), self._data(contact_email='no-es-mail'))
        self.assertIn('contact_email', response.context['form'].errors)

    def test_logo_upload_saves_resource(self):
        resource = CloudinaryResource(public_id='dash-brand/branding/logo', format='png',
                                      type='upload', resource_type='image')
        with mock.patch('cloudinary.uploader.upload_resource', return_value=resource) as upload:
            response = self.post(reverse('dashboard_branding'),
                                 {**self._data(), 'logo': png_file('logo.png')})
        self.assertEqual(response.status_code, 302)
        upload.assert_called_once()
        self.assertIn('dash-brand/branding/logo', str(self._settings().logo))

    def test_disallowed_logo_is_rejected_and_never_uploaded(self):
        with mock.patch('cloudinary.uploader.upload_resource') as upload:
            response = self.post(reverse('dashboard_branding'),
                                 {**self._data(), 'logo': svg_file()})
        upload.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertIn('logo', response.context['form'].errors)
        self.assertFalse(self._settings().logo)

    def test_branding_does_not_touch_other_tenant(self):
        other_color = self.other.settings.primary_color
        self.post(reverse('dashboard_branding'), self._data(primary_color='#0A0B0C'))
        self.other.settings.refresh_from_db()
        self.assertEqual(self.other.settings.primary_color, other_color)
