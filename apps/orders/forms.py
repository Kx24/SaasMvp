# apps/orders/forms.py
"""
Formularios para el onboarding post-pago.

El ClientOnboardingForm es usado después de que el cliente paga.
Hereda campos del plan y la orden, y permite configurar el tenant.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from apps.tenants.models import Client, Domain


class ClientOnboardingForm(forms.Form):
    """
    Formulario de onboarding para clientes que ya pagaron.
    
    Campos heredados de la Order (solo lectura):
    - email (mostrado pero no editable)
    - plan (mostrado pero no editable)
    
    Campos que el cliente completa:
    - Datos de la empresa
    - Branding (logo, colores)
    - Tema visual (según plan)
    """
    
    # =========================================================================
    # SECCIÓN 1: DATOS DE LA EMPRESA
    # =========================================================================
    
    company_name = forms.CharField(
        label="Nombre de tu Empresa",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Constructora del Sur SpA',
            'class': 'form-input'
        }),
        help_text="Este nombre aparecerá en tu sitio web"
    )
    
    slug = forms.SlugField(
        label="Identificador único",
        max_length=100,
        required=False,  # Se autogenera si no se proporciona
        widget=forms.TextInput(attrs={
            'placeholder': 'constructora-sur',
            'class': 'form-input'
        }),
        help_text="Se usará para tu subdominio: tu-slug.andesscale.cl"
    )
    
    # El dominio inicial será un subdominio automático
    # El dominio personalizado se configura después manualmente
    
    # =========================================================================
    # SECCIÓN 2: BRANDING
    # =========================================================================
    
    logo = forms.ImageField(
        label="Logo de tu empresa",
        required=False,
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-input'
        }),
        help_text="Formato PNG o JPG. Tamaño recomendado: 200x80 px"
    )
    
    primary_color = forms.CharField(
        label="Color principal",
        max_length=7,
        initial='#2563eb',
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-color'
        }),
        help_text="Color principal de tu marca"
    )
    
    secondary_color = forms.CharField(
        label="Color secundario",
        max_length=7,
        initial='#1e40af',
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'form-color'
        }),
        help_text="Color de acentos y botones"
    )
    
    # =========================================================================
    # SECCIÓN 3: TEMA VISUAL
    # =========================================================================
    
    # Las opciones se llenan dinámicamente según el plan
    template = forms.ChoiceField(
        label="Diseño de tu sitio",
        choices=[],  # Se llena en __init__
        widget=forms.RadioSelect(attrs={
            'class': 'form-radio'
        }),
        help_text="Elige el estilo visual de tu sitio"
    )
    
    # =========================================================================
    # SECCIÓN 4: CONTACTO
    # =========================================================================
    
    contact_phone = forms.CharField(
        label="Teléfono de contacto",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+56 9 1234 5678',
            'class': 'form-input'
        })
    )
    
    whatsapp_number = forms.CharField(
        label="WhatsApp",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '56912345678',
            'class': 'form-input'
        }),
        help_text="Solo números, con código de país (56)"
    )
    
    # El email viene de la orden, no se pide de nuevo
    
    # =========================================================================
    # SECCIÓN 5: CONTENIDO INICIAL (opcional)
    # =========================================================================
    
    tagline = forms.CharField(
        label="Eslogan o descripción corta",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Soluciones eléctricas para tu hogar',
            'class': 'form-input'
        }),
        help_text="Aparecerá en la sección principal de tu sitio"
    )
    
    about_text = forms.CharField(
        label="Descripción de tu empresa",
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Cuéntanos brevemente sobre tu empresa...',
            'class': 'form-textarea'
        }),
        help_text="Puedes editarlo después desde tu panel"
    )
    
    def __init__(self, *args, available_themes=None, **kwargs):
        """
        Inicializa el formulario con los temas disponibles según el plan.
        
        Args:
            available_themes: Lista de slugs de temas disponibles
        """
        super().__init__(*args, **kwargs)
        
        # Configurar opciones de tema según el plan
        if available_themes:
            theme_choices = []
            theme_labels = {
                'default': ('Tema Estándar', 'Diseño limpio y profesional'),
                'electricidad': ('Electricidad', 'Ideal para servicios eléctricos'),
                'industrial': ('Industrial', 'Para empresas de manufactura'),
                'construccion': ('Construcción', 'Perfecto para constructoras'),
                'servicios': ('Servicios Profesionales', 'Consultorías y asesorías'),
            }
            
            for theme_slug in available_themes:
                label, description = theme_labels.get(
                    theme_slug, 
                    (theme_slug.title(), '')
                )
                display = f"{label}" if not description else f"{label} - {description}"
                theme_choices.append((theme_slug, display))
            
            self.fields['template'].choices = theme_choices
            
            # Si solo hay un tema, preseleccionarlo
            if len(theme_choices) == 1:
                self.fields['template'].initial = theme_choices[0][0]
        else:
            # Default si no se especifican temas
            self.fields['template'].choices = [
                ('default', 'Tema Estándar - Diseño limpio y profesional')
            ]
            self.fields['template'].initial = 'default'
    
    def clean_slug(self):
        """Valida y genera slug si está vacío."""
        slug = self.cleaned_data.get('slug', '').strip()
        company_name = self.cleaned_data.get('company_name', '')
        
        # Autogenerar si está vacío
        if not slug and company_name:
            slug = slugify(company_name)
        
        if not slug:
            raise ValidationError("El identificador es requerido")
        
        # Verificar unicidad
        if Client.objects.filter(slug=slug).exists():
            # Agregar sufijo numérico
            base_slug = slug
            counter = 1
            while Client.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
                if counter > 100:
                    raise ValidationError("No se pudo generar un identificador único")
        
        return slug
    
    def clean_whatsapp_number(self):
        """Limpia y valida número de WhatsApp."""
        number = self.cleaned_data.get('whatsapp_number', '')
        
        if not number:
            return ''
        
        # Remover espacios, guiones, paréntesis
        number = ''.join(filter(str.isdigit, number))
        
        # Agregar 56 si no lo tiene
        if number and not number.startswith('56'):
            if number.startswith('9') and len(number) == 9:
                number = '56' + number
        
        return number
    
    def clean_contact_phone(self):
        """Limpia formato de teléfono."""
        phone = self.cleaned_data.get('contact_phone', '')
        
        if not phone:
            return ''
        
        # Permitir formato libre pero limpiar un poco
        phone = phone.strip()
        
        return phone
