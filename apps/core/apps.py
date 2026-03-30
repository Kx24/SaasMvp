from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        # Configurar Cloudinary cuando Django esté listo
        import cloudinary
        from django.conf import settings
        
        cloudinary.config(
            cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', ''),
            api_key=getattr(settings, 'CLOUDINARY_API_KEY', ''),
            api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', ''),
            secure=getattr(settings, 'CLOUDINARY_SECURE', True)
        )

        from apps.core.signals_cloudinary import register_cloudinary_signals
        register_cloudinary_signals()
        

# =============================================================================
# NOTA IMPORTANTE
# =============================================================================
# register_cloudinary_signals() usa dispatch_uid únicos por modelo, por lo que
# llamarla desde múltiples AppConfig NO duplica los signals.
# Los dispatch_uid garantizan que cada conexión ocurra exactamente una vez:
#
#   dispatch_uid='cloudinary_delete_clientsettings'
#   dispatch_uid='cloudinary_delete_section'
#   dispatch_uid='cloudinary_delete_service'
#   dispatch_uid='cloudinary_delete_seoconfig'
#
# Es seguro llamar register_cloudinary_signals() desde los tres apps.py.
# =============================================================================