"""
Settings para la suite Playwright de #TOOL-01 (tests/e2e/).

Extiende development, pero apunta a una DB SQLite descartable propia
-- nunca al db.sqlite3 de desarrollo del usuario. playwright.config.js
la migra y siembra (seed_e2e_tenants) antes de levantar el servidor.
"""
from .development import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_e2e.sqlite3',  # noqa: F405
    }
}

# Los 3 tenants de la suite se resuelven por Host header (sin DNS real);
# Playwright lo sobreescribe por request, no necesita estar en ALLOWED_HOSTS
# porque TenantMiddleware reemplaza esa validación por lookup en Domain.
ALLOWED_HOSTS = ['*']
