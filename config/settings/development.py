"""
Settings para desarrollo local.
"""
from .base import *

DEBUG = True

# Clave de cifrado de desarrollo derivada de SECRET_KEY (#SEC-06): dev y tests
# no necesitan variables de entorno. Nunca se deriva en producción.
if not FIELD_ENCRYPTION_KEYS:
    import base64
    import hashlib
    FIELD_ENCRYPTION_KEYS = [
        base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest()).decode()
    ]

ALLOWED_HOSTS = ['*']

# Database - Neon (configuración para desarrollo local)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email backend para desarrollo (imprime en consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cloudinary - No requerido en desarrollo
# Las imágenes se guardarán en /media/
# Herramientas de desarrollo (#SEC-10): solo en requirements-dev.txt, no en producción.
INSTALLED_APPS = [*INSTALLED_APPS, 'django_extensions']
