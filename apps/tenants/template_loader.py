"""
TenantTemplateLoader - Carga templates por TEMA (Theme-based)
=============================================================
Lógica de búsqueda:
1. Si es Andesscale -> templates/marketing/{template_name}
2. Si es Cliente -> templates/themes/{client.template}/{template_name}
3. Fallback -> templates/themes/default/{template_name}

Compatible con Django 5.2+
"""

import logging
from pathlib import Path
from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.utils.safestring import SafeString

logger = logging.getLogger(__name__)

class TenantTemplateLoader(FilesystemLoader):
    
    def get_template_sources(self, template_name):
        # --- 1. Sanitización (Igual que antes) ---
        if template_name is None:
            return
        if isinstance(template_name, (SafeString, str)):
            template_name = str(template_name)
        else:
            return
        
        if not template_name or not template_name.strip():
            return
        
        # --- 2. Obtener Tenant ---
        tenant = None
        try:
            from .middleware import get_current_tenant
            tenant = get_current_tenant()
        except Exception as e:
            logger.debug(f"Could not get current tenant: {e}")

        # Definir ruta base de templates
        try:
            base_dir = Path(settings.BASE_DIR) / 'templates'
        except Exception:
            return

        # ============================================================
        # CASO A: SITIO DE MARKETING (Andesscale)
        # ============================================================
        # Si el slug es andesscale (o el que definas como principal),
        # busca en la carpeta 'marketing'
        if tenant and tenant.slug == 'andesscale':
            marketing_path = base_dir / 'marketing' / template_name
            if marketing_path.exists():
                logger.debug(f"[ThemeLoader] Marketing found: {marketing_path}")
                yield Origin(
                    name=str(marketing_path),
                    template_name=template_name,
                    loader=self
                )
            return  # Si es marketing, no busca en themes ni defaults

        # ============================================================
        # CASO B: CLIENTES (Themes)
        # ============================================================
        
        # 1. Determinar el tema
        # Por defecto usamos 'default' si no hay tenant o campo template
        theme = 'default'
        if tenant and hasattr(tenant, 'template') and tenant.template:
            theme = tenant.template.strip().lower()

        # 2. Buscar en el tema específico (ej: themes/electricidad/...)
        theme_path = base_dir / 'themes' / theme / template_name
        if theme_path.exists():
            logger.debug(f"[ThemeLoader] Theme '{theme}' found: {theme_path}")
            yield Origin(
                name=str(theme_path),
                template_name=template_name,
                loader=self
            )
            return

        # 3. Fallback a Default (themes/default/...)
        # Si el cliente usa 'electricidad' pero falta el archivo, busca en 'default'
        if theme != 'default':
            default_path = base_dir / 'themes' / 'default' / template_name
            if default_path.exists():
                logger.debug(f"[ThemeLoader] Fallback to default: {default_path}")
                yield Origin(
                    name=str(default_path),
                    template_name=template_name,
                    loader=self
                )

    def get_contents(self, origin):
        try:
            with open(origin.name, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)