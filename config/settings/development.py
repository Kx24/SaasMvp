"""
Settings para desarrollo local.
"""
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Database - SQLite para desarrollo
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