"""
#DEUDA-03: consistencia entre Client.THEME_CHOICES y las carpetas reales de templates/.

Encontrado al investigar la card: el default del campo Client.template
('default') no coincide con ninguna THEME_CHOICES real, y la choice
'themes/industrial' no tiene carpeta. Ver tambien
apps/orders/tests/test_plan_themes.py para el mismo problema en el
selector de temas del checkout (Plan.available_themes).
"""
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from apps.tenants.models import Client


class ThemeChoicesConsistencyTestCase(TestCase):

    def test_every_theme_choice_has_a_real_template_folder(self):
        templates_dir = Path(settings.BASE_DIR) / 'templates'
        missing = [
            value for value, _label in Client.THEME_CHOICES
            if not (templates_dir / value / 'base.html').exists()
        ]
        self.assertEqual(
            missing, [],
            f"THEME_CHOICES sin carpeta/base.html real: {missing}"
        )

    def test_default_template_value_is_a_valid_choice(self):
        field = Client._meta.get_field('template')
        valid_values = dict(Client.THEME_CHOICES)
        self.assertIn(
            field.default, valid_values,
            f"Client.template default={field.default!r} no es una THEME_CHOICES valida"
        )

    def test_creating_a_client_without_template_uses_a_working_theme(self):
        templates_dir = Path(settings.BASE_DIR) / 'templates'
        client = Client.objects.create(name='Test Co', slug='theme-default-test')
        self.assertTrue(
            (templates_dir / client.template / 'base.html').exists(),
            f"El template por defecto '{client.template}' no resuelve a una carpeta real"
        )
