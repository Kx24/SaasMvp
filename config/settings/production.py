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

Configuración de producción — Django Multi-Tenant SaaS
config/settings/production.py
"""
from .base import *
import os
import dj_database_url

# ==============================================================================
# SEGURIDAD
# ==============================================================================
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required in production")

# ==============================================================================
# DOMINIOS — FUENTE ÚNICA DE VERDAD (CSRF-04)
# ==============================================================================
# Todos los hosts de tenants se declaran por entorno y se parsean UNA sola vez.
# De este set derivan ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS → nunca divergen,
# sin variables muertas. Pensado para sobrevivir una migración de infra:
# si cambias de Render a otra plataforma, solo ajustas las env vars.
#
#   BASE_DOMAIN    → dominio raíz del SaaS (ej. andesscale.com)
#   TENANT_DOMAINS → dominios de tenants, separados por coma
#   EXTRA_DOMAINS  → dominios legacy/adicionales, separados por coma
# Para cada dominio se registra apex + www automáticamente.
# ==============================================================================

def _split_env(name):
    raw = os.environ.get(name, '') or ''
    return [d.strip().lower() for d in raw.split(',') if d.strip()]

def _with_www_variants(hosts):
    expanded = set()
    for h in hosts:
        if not h:
            continue
        expanded.add(h)
        expanded.add(h[4:] if h.startswith('www.') else f'www.{h}')
    return expanded

BASE_DOMAIN = (os.environ.get('BASE_DOMAIN', '') or '').strip().lower()

_tenant_hosts = set()
if BASE_DOMAIN:
    _tenant_hosts.add(BASE_DOMAIN)
_tenant_hosts.update(_split_env('TENANT_DOMAINS'))
_tenant_hosts.update(_split_env('EXTRA_DOMAINS'))
_tenant_hosts = _with_www_variants(_tenant_hosts)

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

# ---- ALLOWED_HOSTS ----
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.onrender.com']
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
ALLOWED_HOSTS.extend(sorted(_tenant_hosts))

# ---- CSRF_TRUSTED_ORIGINS ----
# Orígenes HTTPS explícitos (sin wildcards → no confiamos en subdominios
# arbitrarios). Render aparte.
CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in sorted(_tenant_hosts)]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# Tenant por defecto cuando no se detecta ninguno
DEFAULT_TENANT_SLUG = os.environ.get('DEFAULT_TENANT_SLUG', 'servelec')

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
# STATIC / MEDIA
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    security_index = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
    MIDDLEWARE.insert(security_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware')

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# SEGURIDAD HTTPS
# ==============================================================================
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==============================================================================
# AISLAMIENTO DE COOKIES POR TENANT (CSRF-04 / requisito de ciberseguridad)
# ==============================================================================
# Cookies host-only: cada tenant (andesscale.com, servelec-ingenieria.cl, ...)
# tiene SUS propias cookies de sesión y CSRF. NUNCA fijar *_COOKIE_DOMAIN a un
# valor compartido tipo '.andesscale.com': rompería el CSRF de los demás
# tenants y filtraría sesión entre dominios. Aislamiento absoluto por diseño.
CSRF_COOKIE_DOMAIN = None
SESSION_COOKIE_DOMAIN = None

# SameSite=Lax: viaja en navegación top-level (incluye el POST same-site del
# login) pero no en requests cross-site → mitiga CSRF y aísla terceros.
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# Token CSRF por cookie, legible por el form (no HttpOnly).
CSRF_COOKIE_HTTPONLY = False

# ==============================================================================
# EMAIL
# ==============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.zoho.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    # Sin fallback silencioso a console.EmailBackend: un correo transaccional
    # (confirmación de pago, invitación de onboarding) "enviado" a la consola
    # de un dyno es indistinguible de un correo perdido, y nadie lo nota
    # hasta que un cliente reporta que nunca llegó. Preferimos que el deploy
    # no arranque, igual que con SECRET_KEY.
    raise ValueError(
        "EMAIL_HOST_USER y EMAIL_HOST_PASSWORD son obligatorios en "
        "producción: sin ellos los emails transaccionales (pago, "
        "onboarding, contacto) se pierden en silencio."
    )

# ==============================================================================
# CACHE
# ==============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ==============================================================================
# LOGGING
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{levelname}] {asctime} {name} {message}', 'style': '{'},
        'simple': {'format': '[{levelname}] {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'apps.tenants': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# ==============================================================================
# DEBUG
# ==============================================================================
# Sin override por variable de entorno (#AUD-12): DEBUG=True en producción
# expone traceback completo, variables de entorno y rutas del sistema en
# cualquier error 500 a cualquier visitante.
DEBUG = False