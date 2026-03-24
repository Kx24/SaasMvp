# =============================================================================
# apps/website/forms.py  — REEMPLAZA EL ARCHIVO ACTUAL
# =============================================================================
# CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
#
#   - SectionForm y ServiceForm: SIN CAMBIOS
#
#   - ContactForm REESCRITO:
#       · Honeypot field: campo `website` oculto con CSS.
#         Si viene con valor → spam silencioso (el view guarda con is_spam=True
#         y responde 200 OK igual para no alertar al bot).
#       · Campo `form_source`: hidden, lo inyecta el template según su posición
#         (hero | footer | page | modal).
#       · Campo `intent`: intención del usuario elegida en el Paso 1 del multi-step
#         (quote | support | general). Define qué campos contextuales se muestran.
#       · Validaciones inline: email con formato, nombre mínimo 2 chars.
#       · Campos opcionales explícitos: phone, company solo se validan si vienen.
#
# PARA LOS TEMPLATES:
#   El formulario multi-step (Card #55b) maneja la visibilidad de los campos
#   con Alpine.js — este form simplemente los define todos. El backend valida
#   según la intención recibida.
# =============================================================================

from django import forms
from .models import Section, Service, ContactSubmission


# =============================================================================
# SECTION FORM — sin cambios
# =============================================================================

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['title', 'subtitle', 'description', 'image', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Título de la sección'
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Subtítulo (opcional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descripción completa (opcional)',
                'rows': 4
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
            }),
        }
        labels = {
            'title': 'Título',
            'subtitle': 'Subtítulo',
            'description': 'Descripción',
            'image': 'Imagen',
            'is_active': '¿Mostrar esta sección?'
        }


# =============================================================================
# SERVICE FORM — sin cambios
# =============================================================================

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'full_description', 'image', 'price_text', 'is_active', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nombre del servicio'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descripción breve (aparece en la tarjeta)',
                'rows': 3
            }),
            'full_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Descripción completa (aparece en la página del servicio)',
                'rows': 5
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'accept': 'image/*'
            }),
            'price_text': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Ej: Desde $100.000, Cotizar, Gratis'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary'
            }),
        }
        labels = {
            'name': 'Nombre del Servicio',
            'description': 'Descripción Breve',
            'full_description': 'Descripción Completa',
            'image': 'Imagen',
            'price_text': 'Texto de Precio',
            'is_active': '¿Mostrar este servicio?',
            'is_featured': '¿Es un servicio destacado?'
        }


# =============================================================================
# CONTACT FORM — REESCRITO con honeypot + form_source + intent
# =============================================================================

class ContactForm(forms.Form):
    """
    Formulario público de contacto.

    Diseñado para el flujo multi-step del Card #55b.
    El backend procesa todos los campos independientemente de cómo
    el frontend los muestre o agrupe.

    Campos de control (no visibles al usuario):
        website     → Honeypot: debe llegar vacío. Si viene con valor = bot.
        form_source → Desde qué sección del sitio se envió (hero/footer/page/modal).
        intent      → Intención elegida en el Paso 1 (quote/support/general).

    Campos del usuario:
        name        → Requerido, mínimo 2 caracteres.
        email       → Requerido, formato válido.
        phone       → Opcional. Solo relevante para intent=support.
        company     → Opcional. Solo relevante para intent=quote.
        message     → Requerido.
    """

    # -------------------------------------------------------------------------
    # CAMPOS DE CONTROL
    # -------------------------------------------------------------------------

    # Honeypot: oculto con CSS en el template (NO usar display:none ni hidden input
    # porque algunos bots lo detectan). Se usa position:absolute + opacity:0.
    # Nunca debe llegar con valor desde un humano real.
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'tabindex': '-1',
            'autocomplete': 'off',
            # El estilo de ocultamiento va en el template:
            # style="position:absolute;left:-9999px;opacity:0;height:0;"
        })
    )

    # Identifica desde qué sección del sitio llegó el mensaje.
    # El template lo inyecta como hidden con el valor correspondiente.
    FORM_SOURCE_CHOICES = [
        ('hero',   'Hero / Banner principal'),
        ('footer', 'Footer del sitio'),
        ('page',   'Página de contacto'),
        ('modal',  'Modal emergente'),
    ]
    form_source = forms.ChoiceField(
        choices=FORM_SOURCE_CHOICES,
        initial='page',
        widget=forms.HiddenInput()
    )

    # Intención del usuario — elegida en el Paso 1 del multi-step.
    INTENT_CHOICES = [
        ('quote',   'Cotización'),
        ('support', 'Soporte'),
        ('general', 'Consulta general'),
    ]
    intent = forms.ChoiceField(
        choices=INTENT_CHOICES,
        initial='general',
        widget=forms.HiddenInput()
    )

    # -------------------------------------------------------------------------
    # CAMPOS DEL USUARIO
    # -------------------------------------------------------------------------

    name = forms.CharField(
        max_length=200,
        min_length=2,
        widget=forms.TextInput(attrs={
            'placeholder': 'Tu nombre',
            'autocomplete': 'name',
            'inputmode': 'text',
        }),
        error_messages={
            'required': 'Por favor ingresa tu nombre.',
            'min_length': 'El nombre debe tener al menos 2 caracteres.',
        }
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'tu@email.com',
            'autocomplete': 'email',
            'inputmode': 'email',
        }),
        error_messages={
            'required': 'Por favor ingresa tu email.',
            'invalid': 'Ingresa un email válido (ej: nombre@dominio.com).',
        }
    )

    # Opcional — visible en intent=support
    phone = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+56 9 1234 5678 (opcional)',
            'autocomplete': 'tel',
            'inputmode': 'tel',
        })
    )

    # Opcional — visible en intent=quote
    company = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Tu empresa (opcional)',
            'autocomplete': 'organization',
        })
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Escribe tu mensaje aquí...',
            'rows': 4,
        }),
        error_messages={
            'required': 'Por favor escribe tu mensaje.',
        }
    )

    # -------------------------------------------------------------------------
    # VALIDACIÓN
    # -------------------------------------------------------------------------

    def is_honeypot_triggered(self) -> bool:
        """
        Retorna True si el honeypot fue activado (posible bot).
        Llamar DESPUÉS de is_valid().
        """
        return bool(self.cleaned_data.get('website', ''))

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        # Rechazar nombres que sean solo números o caracteres repetidos
        if name and name.replace(' ', '').isnumeric():
            raise forms.ValidationError('Ingresa tu nombre real.')
        return name

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('El mensaje debe tener al menos 10 caracteres.')
        return message

    def get_subject_by_intent(self) -> str:
        """
        Genera un asunto automático basado en la intención.
        Usado por el view al crear el ContactSubmission.
        """
        intent_labels = {
            'quote':   'Solicitud de cotización',
            'support': 'Soporte técnico',
            'general': 'Consulta general',
        }
        intent = self.cleaned_data.get('intent', 'general')
        return intent_labels.get(intent, 'Contacto desde el sitio')
