# apps/website/templatetags/website_tags.py

from django import template
from apps.website.models import Section, Service

register = template.Library()


@register.simple_tag(takes_context=True)
def get_section(context, section_type):
    """
    Obtiene una sección por tipo (hero, about, contact)
    """
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return None
    
    try:
        return Section.objects.get(
            client=request.client,
            section_type=section_type,
            is_active=True
        )
    except Section.DoesNotExist:
        return None


@register.simple_tag(takes_context=True)
def get_services(context):
    """
    Obtiene todos los servicios activos del modelo Service
    (CORREGIDO: antes buscaba en Section, ahora usa Service)
    """
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return []
    
    return Service.objects.filter(
        client=request.client,
        is_active=True
    ).order_by('order')


@register.simple_tag(takes_context=True)
def get_featured_services(context):
    """
    Obtiene solo los servicios destacados
    """
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return []
    
    return Service.objects.filter(
        client=request.client,
        is_active=True,
        is_featured=True
    ).order_by('order')


@register.simple_tag(takes_context=True)
def client_settings(context):
    """
    Obtiene la configuración del cliente
    """
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return None
    
    return request.client.settings if hasattr(request.client, 'settings') else None


@register.simple_tag(takes_context=True)
def get_testimonials(context):
    """
    Obtiene todos los testimonios activos
    """
    from apps.website.models import Testimonial
    
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return []
    
    return Testimonial.objects.filter(
        client=request.client,
        is_active=True
    ).order_by('order')


@register.simple_tag(takes_context=True)
def get_featured_testimonials(context):
    """
    Obtiene solo los testimonios destacados
    """
    from apps.website.models import Testimonial
    
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return []
    
    return Testimonial.objects.filter(
        client=request.client,
        is_active=True,
        is_featured=True
    ).order_by('order')