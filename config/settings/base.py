"""
Django settings - Base configuration
Con soporte para Multi-Dominio
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# ============================================================
# CONFIGURACIÓN MULTI-DOMINIO
# ============================================================

# Dominio base del SaaS (para subdominios automáticos)
BASE_DOMAIN = config('BASE_DOMAIN', default='tuapp.cl')

# Dominio del landing del SaaS (donde se registran nuevos clientes)
SAAS_DOMAIN = config('SAAS_DOMAIN', default='tuapp.cl')

# Tenant por defecto en desarrollo (slug del cliente)
DEFAULT_TENANT_SLUG = config('DEFAULT_TENANT_SLUG', default=None)

# ALLOWED_HOSTS dinámico
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Agregar wildcard para subdominios en producción
if not DEBUG:
    ALLOWED_HOSTS.append(f'.{BASE_DOMAIN}')  # *.tuapp.cl

# ============================================================
# APLICACIONES
# ============================================================

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
    'apps.accounts',  # Agregar cuando esté listo
]

# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # ========== TENANT MIDDLEWARE ==========
    # IMPORTANTE: Después de AuthenticationMiddleware
    'apps.tenants.middleware.TenantMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR}/db.sqlite3',
        conn_max_age=600,
    )
}

# ============================================================
# AUTH
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================================
# I18N
# ============================================================

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ============================================================
# STATIC & MEDIA
# ============================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================
# TEMPLATES - Con soporte Multi-Tenant
# ============================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        # IMPORTANTE: Desactivar APP_DIRS cuando usamos loaders personalizados
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.tenants.context_processors.client_context',
            ],
#            'loaders': [
#                # 1. Primero: Buscar en tenants/{slug}/ y tenants/_default/
#                'apps.tenants.template_loader.TenantTemplateLoader',
#                # 2. Segundo: Buscar en DIRS (templates/)
#                'django.template.loaders.filesystem.Loader',
#                # 3. Tercero: Buscar en apps (app/templates/)
#                'django.template.loaders.app_directories.Loader',
#            ],
        },
    },
]

# ============================================================
# NOTA: El orden de loaders es importante
# ============================================================
#
# Cuando se solicita "landing/home.html" para tenant "servelec":
#
# 1. TenantTemplateLoader busca:
#    - templates/tenants/servelec/landing/home.html (si existe, usa este)
#    - templates/tenants/_default/landing/home.html (si existe, usa este)
#
# 2. Si no encuentra, filesystem.Loader busca:
#    - templates/landing/home.html
#
# 3. Si no encuentra, app_directories.Loader busca:
#    - apps/*/templates/landing/home.html
#
# ============================================================

# ============================================================
# SESSIONS
# ============================================================

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 7200  # 2 horas
SESSION_COOKIE_NAME = 'saasmvp_sessionid'
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True

# ============================================================
# CSRF
# ============================================================

# Dominios confiables para CSRF (importante para multi-dominio)
CSRF_TRUSTED_ORIGINS = [
    f'https://*.{BASE_DOMAIN}',
    f'https://{SAAS_DOMAIN}',
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ])

# ============================================================
# OTROS
# ============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
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
        'apps.tenants': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}