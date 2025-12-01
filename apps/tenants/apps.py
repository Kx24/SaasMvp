"""
Configuración de la app Tenants.
"""
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """
    Configuración de la aplicación Tenants.
    
    El método ready() se ejecuta cuando Django carga la app.
    Aquí registramos los signals.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tenants'
    verbose_name = 'Sistema Multi-Tenant'
    
    def ready(self):
        """
        Se ejecuta cuando Django termina de cargar la app.
        Importamos signals para que se registren.
        """
        import apps.tenants.signals  # noqa