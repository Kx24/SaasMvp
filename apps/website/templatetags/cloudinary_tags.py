# =============================================================================
# apps/website/templatetags/cloudinary_tags.py
# =============================================================================
# Template tags para imágenes y videos de Cloudinary.
#
# TAGS DISPONIBLES:
#   {% cloudinary_url image 'hero' %}              → URL string
#   {% cloudinary_img image 'hero' alt='...' %}    → <img> con lazy load
#   {% cloudinary_picture image 'hero' alt='...'%} → <picture> con srcset
#   {% cloudinary_bg image 'hero' %}               → URL para background-image
#   {% cloudinary_video video %}                   → <video> con fuentes optimizadas
#   {% cloudinary_embed url %}                     → <iframe> para YouTube/Vimeo
#   {{ image|cloudinary:'hero' }}                  → filtro, retorna URL
#
# USO RÁPIDO:
#   {% load cloudinary_tags %}
#
# AGREGAR NUEVOS PRESETS:
#   Agregar el preset en apps/core/cloudinary_utils.py → CLOUDINARY_PRESETS
#   y si es responsive, en RESPONSIVE_PRESET_MAP.
#   Los template tags lo usarán automáticamente sin cambios aquí.
# =============================================================================

from django import template
from django.utils.html import format_html, format_html_join

from apps.core.cloudinary_utils import (
    BREAKPOINTS,
    CLOUDINARY_PRESETS,
    VIDEO_PRESETS,
    get_cloudinary_url,
    get_srcset_urls,
    get_video_sources,
    get_video_thumbnail_url,
    get_video_url,
)

register = template.Library()


# =============================================================================
# HELPERS INTERNOS
# =============================================================================

def _build_attrs(attrs: dict):
    """Convierte un dict de atributos HTML en SafeString (nombre y valor escapados)."""
    return format_html_join(
        ' ', '{}="{}"',
        ((key, str(value)) for key, value in attrs.items()
         if value is not None and value != ''),
    )


# =============================================================================
# TAGS DE IMAGEN
# =============================================================================

@register.simple_tag
def cloudinary_url(image, preset='thumbnail'):
    """
    Retorna URL de Cloudinary con transformaciones del preset.

    Uso:
        {% load cloudinary_tags %}
        <img src="{% cloudinary_url section.image 'hero' %}" alt="...">
        <div style="background-image: url('{% cloudinary_url section.image 'hero' %}')">
    """
    if not image:
        return ''
    return get_cloudinary_url(image, preset) or ''


@register.simple_tag
def cloudinary_img(image, preset='thumbnail', alt='', css_class='',
                   loading='lazy', width=None, height=None, **extra_attrs):
    """
    Genera <img> con URL de Cloudinary.

    Args:
        image:      CloudinaryField o public_id string
        preset:     Preset de transformación (ver CLOUDINARY_PRESETS)
        alt:        Texto alternativo (siempre definirlo para accesibilidad)
        css_class:  Clases CSS / Tailwind
        loading:    'lazy' (default) | 'eager' para above-the-fold
        width:      Ancho explícito (evita CLS - Cumulative Layout Shift)
        height:     Alto explícito (evita CLS)
        **extra_attrs: Atributos HTML adicionales (data-*, id, etc.)

    Uso:
        {% cloudinary_img section.image 'hero' alt='Banner' css_class='w-full' loading='eager' %}
        {% cloudinary_img service.image 'service_card' alt=service.name css_class='rounded-lg' %}
    """
    placeholder = format_html(
        '<img src="/static/img/placeholder.jpg" alt="{}" class="{}" loading="{}">',
        alt, css_class, loading,
    )

    if not image:
        return placeholder

    url = get_cloudinary_url(image, preset)
    if not url:
        return placeholder

    # Obtener dimensiones del preset para evitar CLS
    preset_config = CLOUDINARY_PRESETS.get(preset, {})
    img_width  = width  or preset_config.get('width', '')
    img_height = height or preset_config.get('height', '')

    attrs = {
        'src':     url,
        'alt':     alt,
        'class':   css_class,
        'loading': loading,
        'width':   img_width,
        'height':  img_height,
        **extra_attrs,
    }

    return format_html('<img {}>', _build_attrs(attrs))


@register.simple_tag
def cloudinary_picture(image, preset='hero', alt='', css_class='', loading='lazy'):
    """
    Genera <picture> con srcset para responsive images (mobile/tablet/desktop).

    Usa RESPONSIVE_PRESET_MAP para obtener la variante correcta por breakpoint.
    El browser elige automáticamente la imagen más apropiada según el viewport.

    Args:
        image:    CloudinaryField o public_id string
        preset:   Preset base (ej: 'hero', 'service_card', 'gallery_full')
        alt:      Texto alternativo
        css_class: Clases CSS del <img> interno
        loading:  'lazy' | 'eager'

    Uso:
        {# Hero - cargar eager (above the fold) #}
        {% cloudinary_picture section.image 'hero' alt='Banner principal' loading='eager' %}

        {# Servicios - lazy load #}
        {% cloudinary_picture service.image 'service_card' alt=service.name css_class='rounded-xl' %}

        {# Galería #}
        {% cloudinary_picture item.image 'gallery_full' alt=item.title %}

    HTML generado:
        <picture>
          <source media="(max-width: 480px)"  srcset="...mobile_url...">
          <source media="(max-width: 768px)"  srcset="...tablet_url...">
          <img src="...desktop_url..." alt="..." class="..." loading="lazy" width="..." height="...">
        </picture>
    """
    placeholder = format_html(
        '<picture><img src="/static/img/placeholder.jpg" alt="{}" '
        'class="{}" loading="{}"></picture>',
        alt, css_class, loading,
    )

    if not image:
        return placeholder

    urls = get_srcset_urls(image, preset)

    if not any([urls['mobile'], urls['tablet'], urls['desktop']]):
        return placeholder

    # Fallback: desktop o el que exista
    fallback_url = urls['desktop'] or urls['tablet'] or urls['mobile']

    # Dimensiones del preset desktop para evitar CLS
    preset_config = CLOUDINARY_PRESETS.get(preset, {})
    img_width  = preset_config.get('width', '')
    img_height = preset_config.get('height', '')

    sources = []

    if urls['mobile']:
        sources.append(format_html(
            '<source media="(max-width: {}px)" srcset="{}">',
            BREAKPOINTS['mobile'], urls['mobile'],
        ))
    if urls['tablet']:
        sources.append(format_html(
            '<source media="(max-width: {}px)" srcset="{}">',
            BREAKPOINTS['tablet'], urls['tablet'],
        ))

    img_attrs = _build_attrs({
        'src':     fallback_url,
        'alt':     alt,
        'class':   css_class,
        'loading': loading,
        'width':   img_width,
        'height':  img_height,
    })

    return format_html(
        '<picture>{}<img {}></picture>',
        format_html_join('', '{}', ((src,) for src in sources)),
        img_attrs,
    )


@register.simple_tag
def cloudinary_bg(image, preset='hero'):
    """
    Retorna URL para usar como background-image en CSS inline.

    Uso:
        <div style="background-image: url('{% cloudinary_bg section.image 'hero' %}')">

        {# Con Tailwind bg-cover #}
        <section class="bg-cover bg-center min-h-[70vh]"
                 style="background-image: url('{% cloudinary_bg section.image %}')">
    """
    if not image:
        return '/static/img/placeholder.jpg'
    return get_cloudinary_url(image, preset) or '/static/img/placeholder.jpg'


# =============================================================================
# TAGS DE VIDEO
# =============================================================================

@register.simple_tag
def cloudinary_video(video, preset='web_hd', poster_image=None,
                     css_class='', autoplay=False, loop=False,
                     muted=True, controls=True, playsinline=True):
    """
    Genera <video> con fuentes optimizadas para videos almacenados en Cloudinary.

    Incluye mp4 + webm para máxima compatibilidad.
    Para videos de YouTube/Vimeo usar {% cloudinary_embed %}.

    Args:
        video:        CloudinaryField de video o public_id string
        preset:       Preset de video ('web_hd', 'web_sd', 'mobile')
        poster_image: CloudinaryField de imagen para usar como poster (opcional)
                      Si no se provee, Cloudinary extrae el primer frame del video
        css_class:    Clases CSS / Tailwind
        autoplay:     Autoplay (fuerza muted=True automáticamente)
        loop:         Repetir video en loop
        muted:        Sin audio (requerido para autoplay en browsers modernos)
        controls:     Mostrar controles del browser
        playsinline:  Reproducir inline en iOS (recomendado)

    Uso:
        {# Video con controles #}
        {% cloudinary_video section.video css_class='w-full rounded-xl' %}

        {# Video de fondo (autoplay, sin controles, loop) #}
        {% cloudinary_video hero.video autoplay=True loop=True controls=False css_class='absolute inset-0 object-cover w-full h-full' %}

        {# Video con imagen poster personalizada #}
        {% cloudinary_video section.video poster_image=section.image %}
    """
    if not video:
        return ''

    sources = get_video_sources(video)
    if not sources:
        return ''

    # Poster: imagen provista o thumbnail del video
    if poster_image:
        poster_url = get_cloudinary_url(poster_image, 'thumbnail')
    else:
        poster_url = get_video_thumbnail_url(video)

    # Atributos booleanos del <video>
    bool_attrs = []
    if autoplay or muted:  # autoplay requiere muted en browsers modernos
        bool_attrs.append('muted')
    if autoplay:
        bool_attrs.append('autoplay')
    if loop:
        bool_attrs.append('loop')
    if controls:
        bool_attrs.append('controls')
    if playsinline:
        bool_attrs.append('playsinline')

    video_attrs = _build_attrs({
        'class':  css_class,
        'poster': poster_url or '',
    })

    sources_html = format_html_join(
        '\n    ', '<source src="{}" type="{}">',
        ((s['url'], s['type']) for s in sources),
    )

    return format_html(
        '<video {} {}>\n    {}\n    Tu navegador no soporta el elemento video.\n</video>',
        video_attrs, ' '.join(bool_attrs), sources_html,
    )


@register.simple_tag
def cloudinary_embed(url, title='Video', css_class='', aspect_ratio='16/9'):
    """
    Genera <iframe> responsive para videos externos (YouTube, Vimeo).

    Para videos propios usar {% cloudinary_video %}.

    Args:
        url:          URL del iframe (YouTube embed, Vimeo embed, etc.)
        title:        Título accesible del iframe
        css_class:    Clases CSS adicionales del wrapper
        aspect_ratio: Relación de aspecto del wrapper ('16/9', '4/3', '1/1')

    Uso:
        {# YouTube #}
        {% cloudinary_embed 'https://www.youtube.com/embed/VIDEO_ID' title='Demo del producto' %}

        {# Vimeo #}
        {% cloudinary_embed 'https://player.vimeo.com/video/VIDEO_ID' title='Tour' %}

        {# Con clase personalizada #}
        {% cloudinary_embed section.video_url css_class='rounded-xl shadow-lg' %}

    HTML generado:
        <div class="relative w-full overflow-hidden rounded ..." style="aspect-ratio: 16/9">
          <iframe src="..." title="..." class="absolute inset-0 w-full h-full"
                  allow="autoplay; fullscreen" allowfullscreen loading="lazy">
          </iframe>
        </div>
    """
    if not url:
        return ''

    wrapper_class = f'relative w-full overflow-hidden {css_class}'.strip()

    return format_html(
        '<div class="{}" style="aspect-ratio: {}">'
        '<iframe '
        'src="{}" '
        'title="{}" '
        'class="absolute inset-0 w-full h-full border-0" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen" '
        'allowfullscreen '
        'loading="lazy">'
        '</iframe>'
        '</div>',
        wrapper_class, aspect_ratio, url, title,
    )


# =============================================================================
# FILTROS
# =============================================================================

@register.filter
def cloudinary(image, preset='thumbnail'):
    """
    Filtro para generar URL de Cloudinary.

    Uso:
        {{ section.image|cloudinary:'hero' }}
        <img src="{{ service.image|cloudinary:'service_card' }}" alt="...">
    """
    if not image:
        return ''
    return get_cloudinary_url(image, preset) or ''


@register.filter
def cloudinary_video_url(video, preset='web_hd'):
    """
    Filtro para generar URL de video de Cloudinary.

    Uso:
        {{ section.video|cloudinary_video_url:'web_hd' }}
    """
    if not video:
        return ''
    return get_video_url(video, preset) or ''


# =============================================================================
# TAGS DE DEBUG / UTILIDADES
# =============================================================================

@register.simple_tag
def cloudinary_presets():
    """
    Retorna los presets disponibles (útil en templates de debug).

    Uso:
        {% cloudinary_presets as presets %}
        {% for name, config in presets.items %}
            <li>{{ name }}: {{ config.width }}x{{ config.height }}</li>
        {% endfor %}
    """
    return CLOUDINARY_PRESETS


@register.simple_tag
def cloudinary_video_presets():
    """Retorna presets de video disponibles."""
    return VIDEO_PRESETS