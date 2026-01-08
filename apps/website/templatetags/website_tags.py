# apps/website/templatetags/website_tags.py

from django import template
from apps.website.models import Section, Service
from apps.tenants.models import FormConfig

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
        # Sin tenant, retornar config por defecto
        return DefaultFormConfig()
    
    try:
        return client.form_config
    except FormConfig.DoesNotExist:
        # Crear config por defecto para el tenant
        form_config = FormConfig.objects.create(client=client)
        return form_config


class DefaultFormConfig:
    """
    Objeto con valores por defecto para cuando no hay FormConfig.
    Simula el modelo FormConfig sin necesitar base de datos.
    """
    # Campos básicos
    name_label = 'Nombre completo'
    name_placeholder = 'Tu nombre'
    email_label = 'Email'
    email_placeholder = 'tu@email.com'
    message_label = 'Mensaje'
    message_placeholder = '¿En qué podemos ayudarte?'
    message_rows = 4
    
    # Campos opcionales - estados
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
    
    # Configuración general
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




