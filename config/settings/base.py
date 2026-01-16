"""
Django settings - Base configuration
=====================================

Multi-Tenant SaaS Platform
Compatible con Django 5.2+
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url
from decouple import config


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# SECURITY
# =============================================================================

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# =============================================================================
# MULTI-TENANT CONFIGURATION
# =============================================================================

# Dominio base para subdominios automáticos (ej: tenant.tuapp.cl)
BASE_DOMAIN = config('BASE_DOMAIN', default='localhost')

# Tenant por defecto cuando no se detecta ninguno
DEFAULT_TENANT_SLUG = config('DEFAULT_TENANT_SLUG', default=None)

# =============================================================================
# ALLOWED HOSTS
# =============================================================================

# Hosts básicos
ALLOWED_HOSTS = ['*']

# Agregar wildcard para subdominios en producción
if not DEBUG and BASE_DOMAIN != 'localhost':
    ALLOWED_HOSTS.append(f'.{BASE_DOMAIN}')

# Agregar hostname de Render automáticamente
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# =============================================================================
# APPLICATIONS
# =============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'django_extensions',
    
    # Local apps
    'apps.core',
    'apps.tenants',
    'apps.website',
    'apps.accounts',
    'cloudinary',
    'cloudinary_storage',  # Opcional, solo si usas como storage backend
]

# =============================================================================
# MIDDLEWARE
# =============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Tenant middleware - después de AuthenticationMiddleware
    'apps.tenants.middleware.TenantMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# =============================================================================
# TEMPLATES
# =============================================================================
# 
# Orden de búsqueda de templates:
# 1. TenantTemplateLoader: templates/tenants/{slug}/ y templates/tenants/_default/
# 2. FilesystemLoader: templates/
# 3. AppDirectoriesLoader: apps/*/templates/ (incluye admin/login.html)
#
# IMPORTANTE: APP_DIRS debe ser False cuando se usan loaders personalizados
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': False,  # IMPORTANTE: False cuando usamos loaders
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.tenants.context_processors.client_context',
            ],
            'loaders': [
                # 1. Templates por tenant
                'apps.tenants.template_loader.TenantTemplateLoader',
                # 2. Templates globales
                'django.template.loaders.filesystem.Loader',
                # 3. Templates de apps (admin, etc.)
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]
# =============================================================================
# CLOUDINARY CONFIGURATION
# Documentación: /docs/CLOUDINARY.md
# =============================================================================

CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='')
CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY', default='')
CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET', default='')
CLOUDINARY_SECURE = config('CLOUDINARY_SECURE', default=True, cast=bool)

# Estructura de carpetas por tenant
CLOUDINARY_FOLDERS = {
    'sections': 'sections',
    'services': 'services',
    'testimonials': 'testimonials',
    'branding': 'branding',
    'gallery': 'gallery',
}

# Presets de transformación
CLOUDINARY_PRESETS = {
    'thumbnail': {
        'crop': 'fill',
        'width': 300,
        'height': 200,
        'format': 'auto',
        'quality': 'auto',
    },
    'hero': {
        'crop': 'fill',
        'width': 1200,
        'height': 600,
        'format': 'auto',
        'quality': 'auto',
    },
    'service_card': {
        'crop': 'fill',
        'width': 400,
        'height': 300,
        'format': 'auto',
        'quality': 'auto',
    },
    'logo': {
        'crop': 'fit',
        'width': 200,
        'height': 80,
        'format': 'auto',
    },
    'avatar': {
        'crop': 'fill',
        'width': 100,
        'height': 100,
        'format': 'auto',
        'quality': 'auto',
        'radius': 'max',
    },
}

# Límites por defecto para tenants
CLOUDINARY_DEFAULT_LIMITS = {
    'max_media_items': 50,
    'max_media_size_mb': 100,
    'max_file_size_mb': 10,
    'allowed_formats': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
}

# Umbrales de alerta
CLOUDINARY_ALERT_THRESHOLDS = {
    'warning': 70,
    'critical': 85,
    'block': 95,
}

# =============================================================================
# DATABASE
# =============================================================================

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR}/db.sqlite3',
        conn_max_age=600,
    )
}

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise para servir archivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# AGREGAR ESTO PARA ARREGLAR LA CARGA DE IMÁGENES
# Esto asegura que cualquier ImageField use Cloudinary si no usas CloudinaryField explícitamente
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# =============================================================================
# SESSIONS
# =============================================================================

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 7200  # 2 horas
SESSION_COOKIE_NAME = 'saasmvp_sessionid'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True

# =============================================================================
# CSRF
# =============================================================================

CSRF_TRUSTED_ORIGINS = []

# Agregar dominios de producción
if BASE_DOMAIN and BASE_DOMAIN != 'localhost':
    CSRF_TRUSTED_ORIGINS.append(f'https://{BASE_DOMAIN}')
    CSRF_TRUSTED_ORIGINS.append(f'https://*.{BASE_DOMAIN}')

# Agregar hostname de Render
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# Desarrollo
if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ])

# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}: {message}',
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
            'formatter': 'verbose' if DEBUG else 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG' if DEBUG else 'INFO',
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
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# OTHER
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


import cloudinary
import cloudinary.uploader
import cloudinary.api