"""
Generalización de hero_ctas a componente compartido (BOLT-08, §2a del
design system).

hero_ctas.html existía duplicado en servelec y themes/default (mismo
markup de par de botones, distintos textos/estilos). El markup pasa a
vivir UNA vez en templates/components/hero_ctas_base.html (parámetros:
textos/hrefs/estilos, secundario solo si recibe texto — precedente
media_collection); cada tema queda con un wrapper de pocas líneas que
produce el mismo HTML visible que hoy.

Nota de naming: el compartido NO puede llamarse components/hero_ctas.html
(nombre literal de la card): el TenantTemplateLoader resolvería ese path
al wrapper del tema activo ({tema}/components/hero_ctas.html) y el
include del wrapper recursaría sobre sí mismo — mismo shadowing
descubierto en BOLT-07 con el navbar.
"""
from pathlib import Path

from django.conf import settings
from django.template.loader import get_template, render_to_string
from django.test import TestCase

SHARED = 'components/hero_ctas_base.html'
WRAPPERS = {
    'servelec': Path(settings.BASE_DIR) / 'templates' / 'themes' / 'servelec' / 'components' / 'hero_ctas.html',
    'themes/default': Path(settings.BASE_DIR) / 'templates' / 'themes' / 'default' / 'components' / 'hero_ctas.html',
}


class HeroCtasSharedComponentTestCase(TestCase):
    def test_shared_component_exists(self):
        # Rojo original de la card: el componente compartido no existía.
        get_template(SHARED)

    def test_servelec_wrapper_renders_current_ctas(self):
        html = render_to_string('themes/servelec/components/hero_ctas.html')
        self.assertIn('Solicitar cotización', html)
        self.assertIn('href="#contacto"', html)
        self.assertIn('Ver servicios', html)
        self.assertIn('href="#servicios"', html)
        # Estilo de marca servelec preservado
        self.assertIn('#1DB954', html)

    def test_default_wrapper_renders_current_ctas(self):
        html = render_to_string('themes/default/components/hero_ctas.html')
        self.assertIn('Contáctanos', html)
        self.assertIn('href="#contacto"', html)
        self.assertIn('Ver servicios', html)
        self.assertIn('href="#servicios"', html)
        # Tokens del tema default preservados
        self.assertIn('var(--color-accent', html)

    def test_secondary_button_only_renders_with_text(self):
        html = render_to_string(SHARED, {'primary_text': 'Solo uno'})
        self.assertIn('Solo uno', html)
        self.assertNotIn('href="#servicios"', html)

    def test_button_markup_lives_only_in_shared_component(self):
        """§2a: los archivos por tema son wrappers con parámetros, sin
        duplicar el markup (DoD: 'grep confirma que la estructura de
        botones vive en un solo archivo')."""
        for theme, wrapper_path in WRAPPERS.items():
            with self.subTest(theme=theme):
                content = wrapper_path.read_text(encoding='utf-8')
                self.assertNotIn('<svg', content)
                self.assertIn('hero_ctas_base.html', content)
