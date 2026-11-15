"""CONS-07: `apps/website/views` es un paquete por área, sin cambiar las URLs."""
import importlib
from pathlib import Path

from django.test import SimpleTestCase

from apps.website import auth_urls, urls

URL_NAMES = [
    'contact_submit',
    'create_service', 'dashboard', 'dashboard_branding', 'dashboard_contacts',
    'dashboard_gallery', 'dashboard_portada', 'dashboard_sections', 'delete_service_dashboard', 'edit_section_dashboard', 'edit_service_dashboard', 'gallery_item_add', 'gallery_item_delete', 'gallery_item_edit',
    'gallery_item_toggle', 'home', 'mark_contact_read', 'mark_contact_replied',
    'reorder_services', 'toggle_service_active', 'toggle_service_featured',
]
AUTH_URL_NAMES = ['client_login', 'client_logout']
AREA_MODULES = ['public', 'sections', 'services', 'gallery', 'contacts', 'branding']
MAX_LINES = 400


class ViewsPackageTests(SimpleTestCase):
    def test_views_is_a_package_with_area_modules(self):
        views = importlib.import_module('apps.website.views')
        self.assertTrue(hasattr(views, '__path__'))
        for name in AREA_MODULES:
            importlib.import_module(f'apps.website.views.{name}')

    def test_no_module_exceeds_line_limit(self):
        views = importlib.import_module('apps.website.views')
        self.assertTrue(hasattr(views, '__path__'))
        for path in Path(list(views.__path__)[0]).glob('*.py'):
            lines = len(path.read_text(encoding='utf-8').splitlines())
            self.assertLessEqual(lines, MAX_LINES, f'{path.name} tiene {lines} líneas')

    def test_url_names_are_frozen(self):
        self.assertEqual(sorted(p.name for p in urls.urlpatterns if p.name), URL_NAMES)
        self.assertEqual(sorted(p.name for p in auth_urls.urlpatterns if p.name), AUTH_URL_NAMES)

    def test_every_pattern_resolves_to_a_callable(self):
        for pattern in urls.urlpatterns + auth_urls.urlpatterns:
            self.assertTrue(callable(pattern.callback), pattern.name)
