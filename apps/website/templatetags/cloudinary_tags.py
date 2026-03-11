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
from django.utils.safestring import mark_safe
from django.utils.html import escape

from apps.core.cloudinary_utils import (
    get_cloudinary_url,
    get_srcset_urls,
    get_video_url,
    get_video_thumbnail_url,
    get_video_sources,
    CLOUDINARY_PRESETS,
    VIDEO_PRESETS,
    BREAKPOINTS,
)

register = template.Library()


# =============================================================================
# HELPERS INTERNOS
# =============================================================================

def _build_attrs(attrs: dict) -> str:
    """Convierte un dict de atributos HTML en string seguro."""
    parts = []
    for key, value in attrs.items():
        if value is not None and value != '':
            parts.append(f'{escape(key)}="{escape(str(value))}"')
    return ' '.join(parts)


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
    placeholder = f'<img src="/static/img/placeholder.jpg" alt="{escape(alt)}" class="{escape(css_class)}" loading="{loading}">'

    if not image:
        return mark_safe(placeholder)

    url = get_cloudinary_url(image, preset)
    if not url:
        return mark_safe(placeholder)

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

    return mark_safe(f'<img {_build_attrs(attrs)}>')


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
    placeholder = (
        f'<picture>'
        f'<img src="/static/img/placeholder.jpg" alt="{escape(alt)}" '
        f'class="{escape(css_class)}" loading="{loading}">'
        f'</picture>'
    )

    if not image:
        return mark_safe(placeholder)

    urls = get_srcset_urls(image, preset)

    if not any([urls['mobile'], urls['tablet'], urls['desktop']]):
        return mark_safe(placeholder)

    # Fallback: desktop o el que exista
    fallback_url = urls['desktop'] or urls['tablet'] or urls['mobile']

    # Dimensiones del preset desktop para evitar CLS
    preset_config = CLOUDINARY_PRESETS.get(preset, {})
    img_width  = preset_config.get('width', '')
    img_height = preset_config.get('height', '')

    sources = []

    if urls['mobile']:
        sources.append(
            f'<source media="(max-width: {BREAKPOINTS["mobile"]}px)" srcset="{urls["mobile"]}">'
        )
    if urls['tablet']:
        sources.append(
            f'<source media="(max-width: {BREAKPOINTS["tablet"]}px)" srcset="{urls["tablet"]}">'
        )

    img_attrs = _build_attrs({
        'src':     fallback_url,
        'alt':     alt,
        'class':   css_class,
        'loading': loading,
        'width':   img_width,
        'height':  img_height,
    })

    html = (
        '<picture>'
        + ''.join(sources)
        + f'<img {img_attrs}>'
        + '</picture>'
    )

    return mark_safe(html)


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
        return mark_safe('')

    sources = get_video_sources(video)
    if not sources:
        return mark_safe('')

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

    sources_html = '\n    '.join(
        f'<source src="{escape(s["url"])}" type="{escape(s["type"])}">'
        for s in sources
    )

    html = (
        f'<video {video_attrs} {" ".join(bool_attrs)}>\n'
        f'    {sources_html}\n'
        f'    Tu navegador no soporta el elemento video.\n'
        f'</video>'
    )

    return mark_safe(html)


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
        return mark_safe('')

    wrapper_class = f'relative w-full overflow-hidden {css_class}'.strip()

    html = (
        f'<div class="{escape(wrapper_class)}" style="aspect-ratio: {escape(aspect_ratio)}">'
        f'<iframe '
        f'src="{escape(url)}" '
        f'title="{escape(title)}" '
        f'class="absolute inset-0 w-full h-full border-0" '
        f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen" '
        f'allowfullscreen '
        f'loading="lazy">'
        f'</iframe>'
        f'</div>'
    )

    return mark_safe(html)


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