"""
#AUD-11 Paso 3: exposición acotada de personalización al tenant.

BrandingForm no exponía accent_color ni font_family (existían en el modelo
pero sin conexión real al dashboard). font_family debe ser una lista
curada (ChoiceField), no texto libre -- un valor arbitrario rompe el
fallback de fuente sin avisar (mismo tipo de bug que #BUG-01: un campo
que existe pero no está conectado a nada real).
"""
from django.test import TestCase

from apps.tenants.fonts import FONT_CHOICES
from apps.tenants.forms import BrandingForm
from apps.tenants.models import Client


class BrandingFormFontAndAccentTestCase(TestCase):
    def setUp(self):
        self.client_obj = Client.objects.create(
            name='Test Branding',
            company_name='Test Branding Inc',
            contact_email='branding@test.com',
            contact_phone='+56900000000',
        )
        self.settings_obj = self.client_obj.settings

    def _valid_data(self, **overrides):
        data = {
            'primary_color': '#3B82F6',
            'secondary_color': '#1E40AF',
            'accent_color': '#F59E0B',
            'font_family': 'Inter',
            'company_name': 'Test Branding Inc',
        }
        data.update(overrides)
        return data

    def test_form_exposes_accent_color_field(self):
        self.assertIn('accent_color', BrandingForm.base_fields)

    def test_form_exposes_font_family_field(self):
        self.assertIn('font_family', BrandingForm.base_fields)

    def test_accent_color_uses_color_widget(self):
        widget = BrandingForm.base_fields['accent_color'].widget
        self.assertEqual(widget.input_type, 'color')

    def test_font_family_accepts_each_curated_choice(self):
        for value, _label in FONT_CHOICES:
            form = BrandingForm(data=self._valid_data(font_family=value), instance=self.settings_obj)
            self.assertTrue(form.is_valid(), f"{value!r} debería ser válido: {form.errors}")

    def test_font_family_rejects_value_outside_curated_list(self):
        form = BrandingForm(data=self._valid_data(font_family='Comic Sans MS'), instance=self.settings_obj)
        self.assertFalse(form.is_valid())
        self.assertIn('font_family', form.errors)

    def test_saving_valid_form_persists_accent_and_font(self):
        form = BrandingForm(
            data=self._valid_data(accent_color='#22C55E', font_family='Outfit'),
            instance=self.settings_obj,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        saved.refresh_from_db()
        self.assertEqual(saved.accent_color, '#22C55E')
        self.assertEqual(saved.font_family, 'Outfit')
