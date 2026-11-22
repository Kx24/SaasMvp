"""
TenantTemplateLoader - Carga templates por CLIENTE
===================================================
Árbol de temas (COMP-02):

  templates/themes/default/      ← tema base
  templates/themes/servelec/     ← Servelec
  templates/themes/andesscale/   ← tema de la plataforma
  templates/components/          ← componentes compartidos (fallback global)

Búsqueda para un tenant:
    1. templates/{tenant.template}/{template_name}   ← ej. themes/servelec
       (si `Client.template` no está seteado, templates/{tenant.slug}/...)
    2. templates/default/{template_name}             ← fallback genérico
    3. templates/{template_name}                     ← fallback global

El tenant de la plataforma (settings.PLATFORM_TENANT_SLUG) usa
`Client.template = 'themes/andesscale'`; en una base sin migrar (template
base) el loader lo resuelve igual por slug.

Ejemplos:
  servelec   → templates/themes/servelec/landing/home.html
  plataforma → templates/themes/andesscale/landing/home.html

Compatible con Django 5.2+
"""

import logging
from pathlib import Path

from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader

logger = logging.getLogger(__name__)

PLATFORM_THEME = 'themes/andesscale'


class TenantTemplateLoader(BaseLoader):

    def get_template_sources(self, template_name):
        # Sanitizar — SafeString no es compatible con pathlib
        if not template_name:
            return
        template_name = str(template_name).strip()
        if not template_name:
            return

        # Ruta base de templates del proyecto
        try:
            base_dir = Path(str(settings.BASE_DIR)) / 'templates'
        except Exception:
            return

        # Obtener tenant actual (thread-local del middleware)
        tenant = None
        try:
            from .middleware import get_current_tenant
            tenant = get_current_tenant()
        except Exception as e:
            logger.debug(f"[ThemeLoader] No tenant: {e}")

        # Construir candidatos según el tenant
        if tenant:
            # Si tiene un campo 'template' configurado, ese tiene prioridad;
            # si no, el slug del cliente hace de nombre de carpeta.
            client_folder = tenant.slug
            if hasattr(tenant, 'template') and tenant.template:
                client_folder = tenant.template.strip().lower()

            # Fallback para una base sin migrar: el tenant de la plataforma
            # con el tema base abre el tema de la plataforma.
            if (
                tenant.slug == getattr(settings, 'PLATFORM_TENANT_SLUG', None)
                and client_folder in ('themes/default', tenant.slug)
            ):
                client_folder = PLATFORM_THEME

            candidates = [
                base_dir / client_folder / template_name,   # ej: templates/themes/servelec/landing/home.html
                base_dir / 'default'    / template_name,   # fallback genérico
                base_dir / template_name,                   # fallback global (base.html, errors/, etc.)
            ]
        else:
            # Sin tenant (admin de Django, rutas internas, etc.)
            candidates = [
                base_dir / template_name,
            ]

        # Yield solo las rutas que existen
        for path in candidates:
            if path.exists():
                logger.debug(f"[ThemeLoader] Found: {path}")
                yield Origin(
                    name=str(path),
                    template_name=template_name,
                    loader=self,
                )

    def get_contents(self, origin):
        try:
            with open(origin.name, encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)