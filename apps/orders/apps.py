# apps/orders/apps.py
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Órdenes y Pagos'
    
    def ready(self):
        # Importar signals cuando la app esté lista
        try:
            import apps.orders.signals  # noqa
        except ImportError:
            pass
