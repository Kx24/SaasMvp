"""
TenantTemplateLoader - Carga templates por TEMA (Theme-based)
=============================================================
Orden de búsqueda:

  Andesscale:
    1. templates/marketing/{template_name}
    2. templates/{template_name}          ← fallback global (base.html, etc.)

  Clientes (tenant con theme):
    1. templates/themes/{theme}/{template_name}
    2. templates/themes/default/{template_name}
    3. templates/{template_name}          ← fallback global

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
        # 1. Sanitizar — SafeString no es compatible con pathlib /
        if not template_name:
            return
        template_name = str(template_name).strip()
        if not template_name:
            return

        # 2. Ruta base de templates del proyecto
        try:
            base_dir = Path(str(settings.BASE_DIR)) / 'templates'
        except Exception:
            return

        # 3. Obtener tenant actual (thread-local del middleware)
        tenant = None
        try:
            from .middleware import get_current_tenant
            tenant = get_current_tenant()
        except Exception as e:
            logger.debug(f"[ThemeLoader] No tenant: {e}")

        # 4. Construir lista de rutas candidatas en orden de prioridad
        if tenant and tenant.slug == 'andesscale':
            candidates = [
                base_dir / 'marketing' / template_name,
                base_dir / template_name,
            ]
        else:
            theme = 'default'
            if tenant and hasattr(tenant, 'template') and tenant.template:
                theme = tenant.template.strip().lower()

            candidates = [base_dir / 'themes' / theme / template_name]
            if theme != 'default':
                candidates.append(base_dir / 'themes' / 'default' / template_name)
            candidates.append(base_dir / template_name)

        # 5. Yield solo las rutas que existen
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