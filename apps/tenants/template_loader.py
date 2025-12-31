"""
TenantTemplateLoader - Carga templates según el tenant activo
=============================================================

Orden de búsqueda:
1. templates/tenants/{tenant_slug}/{template_name}
2. templates/tenants/_default/{template_name}
3. Fallback a los loaders normales de Django

Compatible con Django 5.2+
Maneja SafeString, None, y edge cases.
"""

import logging
from pathlib import Path

from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.utils.safestring import SafeString

logger = logging.getLogger(__name__)


class TenantTemplateLoader(FilesystemLoader):
    """
    Template loader que busca templates específicos por tenant.
    
    Este loader es seguro para usar en producción:
    - Maneja SafeString de Django
    - No falla si no hay tenant
    - Logging para debugging
    """
    
    def get_template_sources(self, template_name):
        """
        Genera las rutas donde buscar el template.
        
        Args:
            template_name: Nombre del template (puede ser str o SafeString)
            
        Yields:
            Origin objects para cada posible ubicación del template
        """
        # ============================================================
        # SANITIZACIÓN DE INPUT
        # ============================================================
        # Django puede pasar SafeString, debemos convertir a str
        if template_name is None:
            return
        
        if isinstance(template_name, (SafeString, str)):
            template_name = str(template_name)
        else:
            # Si es otro tipo, intentar convertir
            try:
                template_name = str(template_name)
            except Exception:
                logger.warning(f"Cannot convert template_name to str: {type(template_name)}")
                return
        
        # Evitar paths vacíos
        if not template_name or not template_name.strip():
            return
        
        # ============================================================
        # OBTENER TENANT ACTUAL
        # ============================================================
        tenant = None
        tenant_slug = None
        
        try:
            from .middleware import get_current_tenant
            tenant = get_current_tenant()
            if tenant:
                tenant_slug = str(tenant.slug) if tenant.slug else None
        except Exception as e:
            # Si hay error obteniendo tenant, continuar sin él
            logger.debug(f"Could not get current tenant: {e}")
        
        # ============================================================
        # DIRECTORIO BASE DE TENANTS
        # ============================================================
        try:
            base_dir = Path(settings.BASE_DIR) / 'templates' / 'tenants'
        except Exception:
            # Si no podemos construir el path, salir
            return
        
        # ============================================================
        # 1. BUSCAR EN CARPETA DEL TENANT ESPECÍFICO
        # ============================================================
        if tenant_slug:
            try:
                tenant_path = base_dir / tenant_slug / template_name
                if tenant_path.exists() and tenant_path.is_file():
                    logger.debug(f"[TenantLoader] Found: {tenant_path}")
                    yield Origin(
                        name=str(tenant_path),
                        template_name=template_name,
                        loader=self,
                    )
                    return
            except Exception as e:
                logger.debug(f"[TenantLoader] Error checking tenant path: {e}")
        
        # ============================================================
        # 2. BUSCAR EN _DEFAULT
        # ============================================================
        try:
            default_path = base_dir / '_default' / template_name
            if default_path.exists() and default_path.is_file():
                logger.debug(f"[TenantLoader] Found in _default: {default_path}")
                yield Origin(
                    name=str(default_path),
                    template_name=template_name,
                    loader=self,
                )
                return
        except Exception as e:
            logger.debug(f"[TenantLoader] Error checking _default path: {e}")
        
        # ============================================================
        # 3. FALLBACK - NO YIELD, DJANGO USARÁ OTROS LOADERS
        # ============================================================
        # No hacemos yield aquí, dejamos que filesystem.Loader y 
        # app_directories.Loader busquen el template
        logger.debug(f"[TenantLoader] Not found, falling back: {template_name}")
    
    def get_contents(self, origin):
        """
        Lee el contenido del template desde el archivo.
        """
        try:
            with open(origin.name, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)
        except IOError as e:
            logger.error(f"[TenantLoader] Error reading {origin.name}: {e}")
            raise TemplateDoesNotExist(origin)