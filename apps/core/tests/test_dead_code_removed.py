"""Guardia (DEUDA-06): el código muerto retirado no debe reaparecer."""
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

BASE = Path(settings.BASE_DIR)


class DeadCodeRemovedTests(SimpleTestCase):
    def test_cloudinary_settings_file_is_gone(self):
        self.assertFalse((BASE / 'config/settings/cloudinary_settings.py').exists())

    def test_order_processor_module_is_gone(self):
        self.assertFalse((BASE / 'apps/orders/services/order_processor.py').exists())

    def test_order_processor_not_exposed(self):
        import apps.orders.services as services
        self.assertFalse(hasattr(services, 'OrderProcessor'))

    def test_stray_marketing_migration_copy_is_gone(self):
        self.assertFalse((BASE / 'apps/marketing/0001_initial.py').exists())
        self.assertTrue((BASE / 'apps/marketing/migrations/0001_initial.py').exists())
