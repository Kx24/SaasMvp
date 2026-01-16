# =============================================================================
# apps/core/template_resolver.py - ARQUITECTURA THEMES (NIVEL 3)
# =============================================================================
# Este helper ya NO calcula rutas manualmente (ej: tenants/{slug}).
# Simplemente pasa el nombre del template a Django, y deja que el
# TenantTemplateLoader (configurado en settings) decida si cargar
# el tema Marketing, Electricidad o Default.
# =============================================================================

from django.shortcuts import render

def get_tenant_template(request, template_path):
    """
    Retorna el nombre del template limpio.
    
    En la nueva arquitectura, ya no necesitamos transformar 
    'home.html' a 'tenants/slug/home.html'.
    
    El TenantTemplateLoader interceptará 'home.html' y buscará 
    en la carpeta del tema correcto automáticamente.
    
    Mantenemos esta función por compatibilidad con las vistas existentes.
    """
    return template_path


def render_tenant_template(request, template_path, context=None):
    """
    Renderiza un template delegando la búsqueda al sistema de Loaders de Django.
    
    Args:
        request: HttpRequest (necesario para que el Loader detecte el tenant)
        template_path: Ruta relativa genérica (ej: 'landing/home.html')
        context: Diccionario de datos
        
    El flujo es:
    1. View llama a render_tenant_template(req, 'landing/home.html')
    2. Django llama a TenantTemplateLoader.get_template('landing/home.html')
    3. Loader verifica: ¿Es Andesscale? -> busca en templates/marketing/
    4. Si no, ¿Qué tema tiene el cliente? -> busca en templates/themes/{tema}/
    """
    return render(request, template_path, context or {})


class TenantTemplateMixin:
    """
    Mixin para Class-Based Views.
    
    Ya no necesita inyectar prefijos de tenants. Simplemente retorna
    el nombre del template original y deja que el Loader haga el trabajo.
    """
    
    def get_template_names(self):
        return [self.template_name]