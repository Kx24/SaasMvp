"""
Configuración de producción para Django Multi-Tenant SaaS
=========================================================

Características:
- ALLOWED_HOSTS dinámico (carga dominios de la DB)
- Múltiples dominios por tenant
- SSL/HTTPS forzado
- WhiteNoise para static files
- Logging optimizado

Usar con: DJANGO_SETTINGS_MODULE=config.settings.production
"""

from .base import *
import os
import dj_database_url

# ==============================================================================
# SEGURIDAD
# ==============================================================================

DEBUG = False

# SECRET_KEY debe estar en variable de entorno
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

# ==============================================================================
# ALLOWED_HOSTS - Multi-Tenant Dinámico
# ==============================================================================

# Hosts base (siempre permitidos)
ALLOWED_HOSTS = [
    '.onrender.com',      # Cualquier subdominio de Render
    'localhost',
    '127.0.0.1',
]

# Dominio de Render automático
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Dominio base del SaaS (para subdominios wildcard)
BASE_DOMAIN = os.environ.get('BASE_DOMAIN', '')
if BASE_DOMAIN:
    ALLOWED_HOSTS.append(BASE_DOMAIN)
    ALLOWED_HOSTS.append(f'.{BASE_DOMAIN}')  # Wildcard: *.tudominio.cl

# Dominios adicionales desde variable de entorno (separados por coma)
# Ejemplo: EXTRA_DOMAINS=servelec-ingenieria.cl,www.servelec-ingenieria.cl,otro.cl
EXTRA_DOMAINS = os.environ.get('EXTRA_DOMAINS', '')
if EXTRA_DOMAINS:
    for domain in EXTRA_DOMAINS.split(','):
        domain = domain.strip()
        if domain:
            ALLOWED_HOSTS.append(domain)

# ==============================================================================
# BASE DE DATOS
# ==============================================================================

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# ==============================================================================
# STATIC FILES - WhiteNoise
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise para servir archivos estáticos eficientemente
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Asegurar que WhiteNoise está en middleware (debe estar después de SecurityMiddleware)
# Ya debería estar en base.py, pero verificamos
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    # Insertar después de SecurityMiddleware
    security_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
    MIDDLEWARE.insert(security_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# ==============================================================================
# MEDIA FILES
# ==============================================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Nota: En producción, considera usar Cloudinary para media files
# WhiteNoise NO sirve media files en producción por defecto
# Para MVP, puedes habilitar con WHITENOISE_USE_FINDERS pero no es recomendado

# ==============================================================================
# SEGURIDAD HTTPS
# ==============================================================================

# Forzar HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies seguras
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Headers de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==============================================================================
# CSRF - Dominios confiables
# ==============================================================================

CSRF_TRUSTED_ORIGINS = []

# Agregar dominio de Render
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# Agregar dominio base
if BASE_DOMAIN:
    CSRF_TRUSTED_ORIGINS.append(f'https://{BASE_DOMAIN}')
    CSRF_TRUSTED_ORIGINS.append(f'https://*.{BASE_DOMAIN}')

# Agregar dominios extra
if EXTRA_DOMAINS:
    for domain in EXTRA_DOMAINS.split(','):
        domain = domain.strip()
        if domain:
            CSRF_TRUSTED_ORIGINS.append(f'https://{domain}')

# ==============================================================================
# EMAIL - Configuración de producción
# ==============================================================================

# Usar variables de entorno para email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.zoho.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Si no hay configuración de email, usar console backend
if not EMAIL_HOST_USER:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ==============================================================================
# TENANT SETTINGS
# ==============================================================================

# Dominio base para subdominios automáticos
# Ejemplo: si BASE_DOMAIN=miapp.cl, un tenant "demo" será demo.miapp.cl
BASE_DOMAIN = os.environ.get('BASE_DOMAIN', 'onrender.com')

# Tenant por defecto cuando no se detecta ninguno
DEFAULT_TENANT_SLUG = os.environ.get('DEFAULT_TENANT_SLUG', 'servelec')

# ==============================================================================
# LOGGING
# ==============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
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
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.tenants': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ==============================================================================
# CACHE (Opcional - mejora performance)
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ==============================================================================
# DEBUG EN PRODUCCIÓN (temporal, solo para debugging)
# ==============================================================================

# Si necesitas debug temporal en producción:
# DEBUG = os.environ.get('DEBUG_PRODUCTION', 'False').lower() == 'true'