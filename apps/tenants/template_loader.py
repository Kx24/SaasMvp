"""
Template Loader Multi-Tenant
============================

Busca templates en este orden:
1. templates/tenants/{tenant_slug}/  (personalizado)
2. templates/tenants/_default/       (base)
3. templates/                         (fallback normal)

Compatible con Django 5.2+
"""
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.template import Origin, TemplateDoesNotExist
from django.conf import settings
from pathlib import Path


class TenantTemplateLoader(FilesystemLoader):
    """
    Loader que busca templates específicos por tenant.
    """
    
    def get_template_sources(self, template_name):
        """
        Genera las rutas donde buscar el template.
        
        Para un tenant "servelec" y template "landing/home.html":
        1. templates/tenants/servelec/landing/home.html
        2. templates/tenants/_default/landing/home.html
        """
        # Obtener el tenant del thread local
        tenant_slug = self._get_current_tenant_slug()
        
        # Directorio base de templates
        base_dir = Path(settings.BASE_DIR) / 'templates' / 'tenants'
        
        if tenant_slug:
            # 1. Buscar en carpeta del tenant específico
            tenant_path = base_dir / tenant_slug / template_name
            if tenant_path.exists():
                yield Origin(
                    name=str(tenant_path),
                    template_name=template_name,
                    loader=self,
                )
        
        # 2. Buscar en _default
        default_path = base_dir / '_default' / template_name
        if default_path.exists():
            yield Origin(
                name=str(default_path),
                template_name=template_name,
                loader=self,
            )
    
    def _get_current_tenant_slug(self):
        """
        Obtiene el slug del tenant actual.
        Usa thread-local storage para acceder desde el loader.
        """
        try:
            from apps.tenants.middleware import get_current_tenant
            tenant = get_current_tenant()
            return tenant.slug if tenant else None
        except Exception:
            return None
    
    def get_contents(self, origin):
        """
        Lee el contenido del template.
        """
        try:
            with open(origin.name, encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)