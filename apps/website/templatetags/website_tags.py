
from django import template

from apps.tenants.fonts import google_fonts_query as _google_fonts_query
from apps.tenants.models import FormConfig
from apps.website.models import GalleryItem, Section, Service

register = template.Library()


@register.simple_tag
def google_fonts_query(font_name):
    """
    Fragmento `family=...` de Google Fonts para la fuente de cuerpo
    elegida por el tenant (#AUD-11 Paso 3). Uso:
        <link href="https://fonts.googleapis.com/css2?family={% google_fonts_query client.settings.font_family %}&display=swap" rel="stylesheet">
    """
    return _google_fonts_query(font_name)

MEDIA_SLOTS = {
    'hero':    'components/slots/hero_overlay.html',
    'gallery': 'components/slots/gallery_caption.html',
    'profile': 'components/slots/profile_card.html',
    'empty':   'components/slots/empty.html',
}

@register.simple_tag
def slot_template(slot_key):
    if not slot_key or slot_key not in MEDIA_SLOTS:
        if slot_key:
            logger.warning(f"[MediaSlot] Slot desconocido: '{slot_key}', usando 'empty'")
        return MEDIA_SLOTS['empty']
    return MEDIA_SLOTS[slot_key]


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
    except Section.MultipleObjectsReturned:
        logger.warning(
            f"[Section] Múltiples secciones activas para "
            f"client={request.client.slug} type={section_type}. "
            f"Usando la primera."
        )
        return Section.objects.filter(
            client=request.client,
            section_type=section_type,
            is_active=True
        ).first()


@register.simple_tag(takes_context=True)
def get_services(context):
    """
    Obtiene todos los servicios activos del modelo Service
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
def get_gallery(context):
    """
    Retorna los ítems de galería activos del tenant actual.

    Respeta el flag enable_gallery de ClientSettings:
    si el módulo está desactivado para este cliente, retorna []
    sin ejecutar query adicional a GalleryItem.

    Retorna [] (no None) para que {% if gallery_items %} funcione
    directamente en templates sin filtros extra.

    Uso:
        {% get_gallery as gallery_items %}
        {% if gallery_items %}
            {% include 'components/hero_gallery.html' with items=gallery_items mode="gallery" layout="grid" cols=3 %}
        {% endif %}
    """
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return []

    client = request.client
    settings = getattr(client, 'settings', None)
    if not settings or not settings.enable_gallery:
        return []

    return GalleryItem.objects.filter(
        client=client,
        gallery_type='gallery',
        is_active=True,
    ).order_by('order', 'created_at')

@register.simple_tag(takes_context=True)
def get_hero_images(context):
    """
    Retorna imágenes de portada según configuración del tenant.

    Lógica:
      1. Si enable_gallery está desactivado → []
      2. Obtiene imágenes activas (is_default=False, gallery_type='hero')
      3. Si show_default_hero=True o no hay imágenes activas → antepone el hero default
      4. El hero default se representa como None — el template lo detecta
         y renderiza el diseño base del tema
    """
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return []

    client = request.client
    settings = getattr(client, 'settings', None)
    if not settings or not settings.enable_gallery:
        return []

    # Imágenes activas del cliente (no default)
    active = list(
        GalleryItem.objects.filter(
            client=client,
            gallery_type='hero',
            is_active=True,
        ).order_by('order', 'created_at')
    )

    # Decidir si incluir el hero default
    show_default = settings.show_default_hero
    no_images = len(active) == 0

    if show_default or no_images:
        # None representa el slide del hero default
        return [None] + active
    else:
        return active
    
@register.simple_tag(takes_context=True)
def get_hero_split_media(context):
    """
    Retorna hasta 2 GalleryItem activos (gallery_type='hero'), para heroes de
    dos fotos simultáneas lado a lado (layout "split", ej. Rancho Cachimba).

    A diferencia de get_hero_images(), no antepone el slide default (None) —
    un layout split no tiene noción de "slide", son dos slots fijos. Si hay
    menos de 2 imágenes activas, el template decide el fallback visual.

    Uso:
        {% get_hero_split_media as hero_media %}
        {{ hero_media.0 }} → slot A (o None si no hay)
        {{ hero_media.1 }} → slot B (o None si no hay)
    """
    request = context.get('request')
    if not request or not hasattr(request, 'client'):
        return [None, None]

    client = request.client
    settings = getattr(client, 'settings', None)
    if not settings or not settings.enable_gallery:
        return [None, None]

    active = list(
        GalleryItem.objects.filter(
            client=client,
            gallery_type='hero',
            is_active=True,
        ).order_by('order', 'created_at')[:2]
    )
    while len(active) < 2:
        active.append(None)
    return active


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


# ==============================
# Form Config Template Tag
# ==============================

@register.simple_tag(takes_context=True)
def get_form_config(context):
    """
    Obtiene la configuración del formulario para el tenant actual.

    Si no existe FormConfig, retorna un objeto con valores por defecto.

    Uso:
        {% get_form_config as form_config %}
        {% if form_config.show_phone %}...{% endif %}
    """
    request = context.get('request')
    client = getattr(request, 'client', None)

    if not client:
        return DefaultFormConfig()

    try:
        return client.form_config
    except FormConfig.DoesNotExist:
        form_config = FormConfig.objects.create(client=client)
        return form_config


@register.filter
def split(value, sep=" "):
    """
    Uso: {{ text|split:" - " }} -> lista
    """
    if value is None:
        return []
    return str(value).split(sep)


@register.filter
def first(value):
    try:
        return value[0]
    except Exception:
        return ""


@register.filter
def last(value):
    try:
        return value[-1]
    except Exception:
        return ""


class DefaultFormConfig:
    """
    Objeto con valores por defecto para cuando no hay FormConfig.
    Simula el modelo FormConfig sin necesitar base de datos.
    """
    name_label = 'Nombre completo'
    name_placeholder = 'Tu nombre'
    email_label = 'Email'
    email_placeholder = 'tu@email.com'
    message_label = 'Mensaje'
    message_placeholder = '¿En qué podemos ayudarte?'
    message_rows = 4

    show_phone = True
    phone_required = False
    phone_label = 'Teléfono'
    phone_placeholder = '+56 9 1234 5678'

    show_company = False
    company_required = False
    company_label = 'Empresa'
    company_placeholder = 'Tu empresa'

    show_subject = True
    subject_required = False
    subject_label = 'Asunto'
    subject_options = 'Consulta general\nSolicitar cotización\nSoporte técnico\nOtro'

    show_address = False
    address_required = False
    address_label = 'Dirección'
    address_placeholder = ''

    show_city = False
    city_required = False
    city_label = 'Ciudad/Comuna'
    city_placeholder = ''

    show_budget = False
    budget_required = False
    budget_label = 'Presupuesto estimado'
    budget_options = 'Menos de $100.000\n$100.000 - $500.000\n$500.000 - $1.000.000\nMás de $1.000.000'

    show_urgency = False
    urgency_required = False
    urgency_label = 'Urgencia'
    urgency_options = 'Normal\nUrgente\nMuy urgente (24h)'

    show_source = False
    source_required = False
    source_label = '¿Cómo nos conociste?'
    source_options = 'Google\nRedes sociales\nRecomendación\nOtro'

    submit_button_text = 'Enviar mensaje'
    success_message = '¡Gracias por contactarnos! Te responderemos a la brevedad.'
    privacy_text = 'Al enviar, aceptas nuestra política de privacidad.'

    def get_subject_options_list(self):
        return [opt.strip() for opt in self.subject_options.split('\n') if opt.strip()]

    def get_budget_options_list(self):
        return [opt.strip() for opt in self.budget_options.split('\n') if opt.strip()]

    def get_urgency_options_list(self):
        return [opt.strip() for opt in self.urgency_options.split('\n') if opt.strip()]

    def get_source_options_list(self):
        return [opt.strip() for opt in self.source_options.split('\n') if opt.strip()]
