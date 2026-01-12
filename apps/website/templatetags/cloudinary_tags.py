# =============================================================================
# apps/website/templatetags/cloudinary_tags.py
# =============================================================================
# Template tags para mostrar imágenes de Cloudinary en templates
# Card C2: Integración con templates
# =============================================================================

from django import template
from django.utils.safestring import mark_safe
from apps.core.cloudinary_utils import get_cloudinary_url, CLOUDINARY_PRESETS

register = template.Library()


@register.simple_tag
def cloudinary_url(image, preset='thumbnail'):
    """
    Genera URL de Cloudinary con transformaciones.
    
    Uso en template:
        {% load cloudinary_tags %}
        {% cloudinary_url section.image 'hero' %}
        
        <img src="{% cloudinary_url section.image 'hero' %}" alt="...">
    """
    if not image:
        return ''
    
    url = get_cloudinary_url(image, preset)
    return url or ''


@register.simple_tag
def cloudinary_img(image, preset='thumbnail', alt='', css_class='', **attrs):
    """
    Genera tag <img> completo con URL de Cloudinary.
    
    Uso en template:
        {% cloudinary_img section.image 'hero' alt='Banner principal' css_class='w-full' %}
        
        {% cloudinary_img service.image 'service_card' alt=service.name css_class='rounded-lg' loading='lazy' %}
    """
    if not image:
        # Retornar placeholder o nada
        return mark_safe(f'<img src="/static/img/placeholder.jpg" alt="{alt}" class="{css_class}">')
    
    url = get_cloudinary_url(image, preset)
    if not url:
        return ''
    
    # Construir atributos adicionales
    extra_attrs = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
    
    html = f'<img src="{url}" alt="{alt}" class="{css_class}" {extra_attrs}>'
    return mark_safe(html)


@register.simple_tag
def cloudinary_bg(image, preset='hero'):
    """
    Genera URL para usar como background-image en CSS inline.
    
    Uso en template:
        <div style="background-image: url('{% cloudinary_bg section.image 'hero' %}')">
        </div>
        
        O con Tailwind:
        <div class="bg-cover bg-center" style="background-image: url('{% cloudinary_bg section.image 'hero' %}')">
    """
    if not image:
        return '/static/img/placeholder.jpg'
    
    url = get_cloudinary_url(image, preset)
    return url or '/static/img/placeholder.jpg'


@register.inclusion_tag('components/cloudinary_picture.html')
def cloudinary_picture(image, preset='hero', alt='', css_class=''):
    """
    Genera elemento <picture> con múltiples tamaños para responsive.
    
    Uso en template:
        {% cloudinary_picture section.image 'hero' alt='Banner' css_class='w-full' %}
    
    Requiere crear el template: templates/components/cloudinary_picture.html
    """
    if not image:
        return {
            'has_image': False,
            'alt': alt,
            'css_class': css_class,
        }
    
    return {
        'has_image': True,
        'url_desktop': get_cloudinary_url(image, preset),
        'url_tablet': get_cloudinary_url(image, preset, width=992),
        'url_mobile': get_cloudinary_url(image, preset, width=576),
        'alt': alt,
        'css_class': css_class,
    }


@register.filter
def cloudinary(image, preset='thumbnail'):
    """
    Filtro para generar URL de Cloudinary.
    
    Uso en template:
        {{ section.image|cloudinary:'hero' }}
        
        <img src="{{ service.image|cloudinary:'service_card' }}" alt="...">
    """
    if not image:
        return ''
    
    return get_cloudinary_url(image, preset) or ''


@register.simple_tag
def cloudinary_presets():
    """
    Retorna lista de presets disponibles (útil para debug).
    
    Uso en template:
        {% cloudinary_presets as presets %}
        {% for name, config in presets.items %}
            {{ name }}: {{ config.width }}x{{ config.height }}
        {% endfor %}
    """
    return CLOUDINARY_PRESETS
