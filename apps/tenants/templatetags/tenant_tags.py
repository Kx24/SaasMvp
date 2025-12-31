"""
Template Tags para Multi-Tenant
===============================

Tags disponibles:
- {% tenant_static 'img/logo.png' %}  → Busca en media/tenants/{slug}/
- {% tenant_include 'components/hero.html' %} → Include con fallback
- {% get_tenant_media_url 'logo.png' as logo_url %}
"""
from django import template
from django.conf import settings
from django.template.loader import render_to_string, get_template
from django.template.exceptions import TemplateDoesNotExist
from pathlib import Path

register = template.Library()


@register.simple_tag(takes_context=True)
def tenant_static(context, path):
    """
    Retorna la URL de un archivo estático del tenant.
    
    Busca en:
    1. /media/tenants/{tenant_slug}/{path}
    2. /static/{path} (fallback)
    
    Uso:
        {% tenant_static 'img/logo.png' %}
        {% tenant_static 'css/custom.css' %}
    """
    request = context.get('request')
    client = context.get('client') or getattr(request, 'client', None)
    
    if client:
        # Ruta del tenant
        tenant_path = Path(settings.MEDIA_ROOT) / 'tenants' / client.slug / path
        
        if tenant_path.exists():
            return f"{settings.MEDIA_URL}tenants/{client.slug}/{path}"
    
    # Fallback a static
    return f"{settings.STATIC_URL}{path}"


@register.simple_tag(takes_context=True)
def tenant_media(context, path):
    """
    Retorna la URL de un archivo en media del tenant.
    
    Uso:
        {% tenant_media 'logo.png' %}
        → /media/tenants/servelec/logo.png
    """
    request = context.get('request')
    client = context.get('client') or getattr(request, 'client', None)
    
    if client:
        return f"{settings.MEDIA_URL}tenants/{client.slug}/{path}"
    
    return f"{settings.MEDIA_URL}{path}"


@register.simple_tag(takes_context=True)
def get_tenant_media_url(context, filename):
    """
    Obtiene la URL completa de un archivo media del tenant.
    
    Uso:
        {% get_tenant_media_url 'logo.png' as logo_url %}
        <img src="{{ logo_url }}" alt="Logo">
    """
    request = context.get('request')
    client = context.get('client') or getattr(request, 'client', None)
    
    if client:
        file_path = Path(settings.MEDIA_ROOT) / 'tenants' / client.slug / filename
        if file_path.exists():
            return f"{settings.MEDIA_URL}tenants/{client.slug}/{filename}"
    
    return ""


@register.simple_tag(takes_context=True)
def tenant_include(context, template_name):
    """
    Include un template con fallback por tenant.
    
    Busca en:
    1. tenants/{tenant_slug}/{template_name}
    2. tenants/_default/{template_name}
    3. {template_name} (ubicación normal)
    
    Uso:
        {% tenant_include 'components/hero.html' %}
    """
    request = context.get('request')
    client = context.get('client') or getattr(request, 'client', None)
    
    templates_to_try = []
    
    if client:
        # 1. Template específico del tenant
        templates_to_try.append(f"tenants/{client.slug}/{template_name}")
        
    # 2. Template default
    templates_to_try.append(f"tenants/_default/{template_name}")
    
    # 3. Template en ubicación normal
    templates_to_try.append(template_name)
    
    # Intentar cada template
    for tmpl in templates_to_try:
        try:
            return render_to_string(tmpl, context.flatten())
        except TemplateDoesNotExist:
            continue
    
    # Si ninguno existe, retornar comentario HTML
    return f"<!-- Template not found: {template_name} -->"


@register.inclusion_tag('partials/tenant_css.html', takes_context=True)
def tenant_custom_css(context):
    """
    Incluye CSS personalizado del tenant si existe.
    
    Busca en: /media/tenants/{slug}/css/custom.css
    
    Uso en base.html:
        {% tenant_custom_css %}
    """
    request = context.get('request')
    client = context.get('client') or getattr(request, 'client', None)
    
    css_url = None
    
    if client:
        css_path = Path(settings.MEDIA_ROOT) / 'tenants' / client.slug / 'css' / 'custom.css'
        if css_path.exists():
            css_url = f"{settings.MEDIA_URL}tenants/{client.slug}/css/custom.css"
    
    return {'css_url': css_url}


@register.simple_tag(takes_context=True)
def tenant_template_exists(context, template_name):
    """
    Verifica si existe un template personalizado para el tenant.
    
    Uso:
        {% tenant_template_exists 'components/hero.html' as has_custom_hero %}
        {% if has_custom_hero %}
            <!-- Usando template personalizado -->
        {% endif %}
    """
    request = context.get('request')
    client = context.get('client') or getattr(request, 'client', None)
    
    if client:
        try:
            get_template(f"tenants/{client.slug}/{template_name}")
            return True
        except TemplateDoesNotExist:
            pass
    
    return False


@register.simple_tag(takes_context=True)
def get_tenant_slug(context):
    """
    Retorna el slug del tenant actual.
    
    Uso:
        {% get_tenant_slug as tenant_slug %}
        <body class="tenant-{{ tenant_slug }}">
    """
    request = context.get('request')
    client = context.get('client') or getattr(request, 'client', None)
    
    return client.slug if client else 'default'