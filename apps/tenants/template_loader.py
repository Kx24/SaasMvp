"""
TenantTemplateLoader - Carga templates según el tenant activo
=============================================================

Orden de búsqueda:
1. templates/tenants/{tenant_slug}/{template_name}
2. templates/tenants/_default/{template_name}
3. Fallback a los loaders normales de Django

Compatible con Django 5.2+
"""

import logging
from pathlib import Path

from django.conf import settings
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.filesystem import Loader as FilesystemLoader

from .middleware import get_current_tenant

logger = logging.getLogger(__name__)


class TenantTemplateLoader(FilesystemLoader):
    """
    Template loader que busca templates específicos por tenant.
    """
    
    def get_template_sources(self, template_name):
        """
        Genera las rutas donde buscar el template.
        
        Args:
            template_name: Nombre del template (ej: 'landing/home.html')
            
        Yields:
            Origin objects para cada posible ubicación del template
        """
        # IMPORTANTE: Convertir a str para evitar error con SafeString
        template_name = str(template_name)
        
        # Directorio base de templates de tenants
        base_dir = Path(settings.BASE_DIR) / 'templates' / 'tenants'
        
        # Obtener tenant actual desde thread-local
        tenant = get_current_tenant()
        tenant_slug = tenant.slug if tenant else None
        
        # 1. Buscar en carpeta del tenant específico
        if tenant_slug:
            tenant_path = base_dir / tenant_slug / template_name
            if tenant_path.exists():
                logger.debug(f"Template found for tenant '{tenant_slug}': {tenant_path}")
                yield Origin(
                    name=str(tenant_path),
                    template_name=template_name,
                    loader=self,
                )
                return  # Encontrado, no buscar más
        
        # 2. Buscar en _default
        default_path = base_dir / '_default' / template_name
        if default_path.exists():
            logger.debug(f"Template found in _default: {default_path}")
            yield Origin(
                name=str(default_path),
                template_name=template_name,
                loader=self,
            )
            return  # Encontrado, no buscar más
        
        # 3. Fallback: dejar que los otros loaders busquen
        # No yield nada aquí, Django continuará con el siguiente loader
        logger.debug(f"Template '{template_name}' not found in tenant dirs, falling back")
    
    def get_contents(self, origin):
        """
        Lee el contenido del template desde el archivo.
        
        Args:
            origin: Origin object con la ruta del template
            
        Returns:
            Contenido del template como string
        """
        try:
            with open(origin.name, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)
        except IOError as e:
            logger.error(f"Error reading template {origin.name}: {e}")
            raise TemplateDoesNotExist(origin)