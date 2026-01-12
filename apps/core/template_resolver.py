# =============================================================================
# apps/core/template_resolver.py
# =============================================================================
# Helper para resolver templates por tenant usando SLUG (no ID)
# 
# Orden de búsqueda:
# 1. tenants/{slug}/...        (template específico del cliente)
# 2. tenants/_default/...      (template por defecto)
# 3. {path original}           (fallback)
# =============================================================================

from django.template import TemplateDoesNotExist
from django.template.loader import get_template
import logging

logger = logging.getLogger(__name__)


def get_tenant_template(request, template_path):
    """
    Resuelve el template correcto para el tenant actual.
    
    Args:
        request: HttpRequest con request.client
        template_path: Ruta relativa del template (ej: 'landing/home.html')
    
    Returns:
        Ruta del template a usar
    
    Ejemplo:
        # Si request.client.slug = 'servelec-ingenieria'
        get_tenant_template(request, 'landing/home.html')
        # Busca en orden:
        # 1. tenants/servelec-ingenieria/landing/home.html
        # 2. tenants/_default/landing/home.html
        # 3. landing/home.html
    """
    if not hasattr(request, 'client') or not request.client:
        logger.warning("get_tenant_template: No client in request, using default")
        return template_path
    
    slug = request.client.slug
    
    # Lista de templates a probar (en orden de prioridad)
    templates_to_try = [
        f"tenants/{slug}/{template_path}",      # Específico del tenant
        f"tenants/_default/{template_path}",    # Default
        template_path,                           # Fallback original
    ]
    
    for template_name in templates_to_try:
        try:
            get_template(template_name)
            logger.debug(f"Template resolved: {template_name}")
            return template_name
        except TemplateDoesNotExist:
            continue
    
    # Si ninguno existe, retornar el original (Django mostrará error)
    logger.warning(f"No template found for {slug}/{template_path}, using: {template_path}")
    return template_path


def render_tenant_template(request, template_path, context=None):
    """
    Shortcut para renderizar template de tenant.
    
    Uso:
        from apps.core.template_resolver import render_tenant_template
        
        def home(request):
            context = {'services': services}
            return render_tenant_template(request, 'landing/home.html', context)
    """
    from django.shortcuts import render
    
    resolved_template = get_tenant_template(request, template_path)
    return render(request, resolved_template, context or {})


class TenantTemplateMixin:
    """
    Mixin para Class-Based Views que resuelve templates por tenant.
    
    Uso:
        class HomeView(TenantTemplateMixin, TemplateView):
            template_name = 'landing/home.html'
    """
    
    def get_template_names(self):
        """
        Retorna lista de templates a probar.
        Django usa el primero que encuentre.
        """
        base_template = self.template_name
        
        if not hasattr(self.request, 'client') or not self.request.client:
            return [base_template]
        
        slug = self.request.client.slug
        
        return [
            f"tenants/{slug}/{base_template}",
            f"tenants/_default/{base_template}",
            base_template,
        ]