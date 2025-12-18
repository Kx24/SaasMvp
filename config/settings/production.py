"""
Configuración de producción para Django
Usar con: python manage.py runserver --settings=config.settings.production
"""

from .base import *
import os
import dj_database_url

# ==============================================================================
# SEGURIDAD
# ==============================================================================

DEBUG = False

# SECRET_KEY debe estar en variable de entorno
SECRET_KEY = os.environ.get('SECRET_KEY', 'CHANGE-THIS-IN-PRODUCTION')

# Dominios permitidos
ALLOWED_HOSTS = [
    '.onrender.com',  # Render.com
    'localhost',
    '127.0.0.1',
]

# Agregar dominio de Render automáticamente
render_domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_domain:
    ALLOWED_HOSTS.append(render_domain)

# Agregar dominio personalizado si existe
custom_domain = os.environ.get('DOMAIN')
if custom_domain:
    ALLOWED_HOSTS.append(custom_domain)
    ALLOWED_HOSTS.append(f'www.{custom_domain}')

# ==============================================================================
# BASE DE DATOS
# ==============================================================================

# PostgreSQL desde Render (dj-database-url maneja la conexión)
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ==============================================================================
# STATIC FILES
# ==============================================================================

# Whitenoise para servir archivos estáticos
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# MEDIA FILES
# ==============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# SEGURIDAD HTTPS
# ==============================================================================

# Forzar HTTPS en producción
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Headers de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==============================================================================
# EMAIL (Console backend por ahora, configurar SMTP después)
# ==============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Para configurar email real después:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
# EMAIL_USE_TLS = True
# DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')

# ==============================================================================
# LOGGING
# ==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# ==============================================================================
# CORS (si necesario en futuro)
# ==============================================================================

# CORS_ALLOWED_ORIGINS = []

# ==============================================================================
# CACHE (opcional, para mejorar performance después)
# ==============================================================================

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#     }
# }