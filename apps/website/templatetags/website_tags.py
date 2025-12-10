from django import template
from apps.website.models import Section, Service

register = template.Library()

@register.simple_tag(takes_context=True)
def get_section(context, section_type):
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
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return []
    
    return Service.objects.filter(
        client=request.client,
        is_active=True
    ).order_by('order', 'name')