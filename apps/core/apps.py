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