"""
TenantTemplateLoader - Carga templates por CLIENTE
===================================================
Nueva estructura (un directorio por cliente/marca):

  AndesScale (marca propia):
    1. templates/andesscale/{template_name}
    2. templates/{template_name}              ← fallback global

  Clientes (tenant con slug o template configurado):
    1. templates/{tenant.slug}/{template_name}     ← carpeta del cliente
    2. templates/default/{template_name}           ← fallback genérico
    3. templates/{template_name}                   ← fallback global

Ejemplos:
  servelec  → templates/servelec/landing/home.html
  andesscale → templates/andesscale/landing/home.html

Compatible con Django 5.2+
"""

import logging
from pathlib import Path
from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader

logger = logging.getLogger(__name__)


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
        if tenant and tenant.slug == 'andesscale':
            # Marca propia — usa su propia carpeta
            candidates = [
                base_dir / 'andesscale' / template_name,
                base_dir / template_name,
            ]
        elif tenant:
            # Cliente — usa slug como nombre de carpeta
            # Si tiene un campo 'template' configurado, ese tiene prioridad
            client_folder = tenant.slug
            if hasattr(tenant, 'template') and tenant.template:
                client_folder = tenant.template.strip().lower()

            candidates = [
                base_dir / client_folder / template_name,   # ej: templates/servelec/landing/home.html
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