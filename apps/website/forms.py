"""
Formularios para la aplicación website
"""
from django import forms
from .models import Section, Service, Testimonial, ContactSubmission


class SectionForm(forms.ModelForm):
    """
    Formulario para editar secciones del sitio.
    Usa Tailwind CSS para styling.
    """
    
    class Meta:
        model = Section
        fields = ['title', 'subtitle', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
                'placeholder': 'Título de la sección',
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
                'placeholder': 'Subtítulo (opcional)',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary',
            }),
        }
        labels = {
            'title': 'Título',
            'subtitle': 'Subtítulo',
            'is_active': '¿Mostrar esta sección?',
        }


class ServiceForm(forms.ModelForm):
    """
    Formulario para crear/editar servicios.
    """
    
    class Meta:
        model = Service
        fields = ['name', 'description', 'icon', 'price_text', 'is_active', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nombre del servicio',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 4,
                'placeholder': 'Descripción del servicio...',
            }),
            'icon': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '⚡ (emoji o clase de icono)',
            }),
            'price_text': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Ej: Desde $50.000 o Consultar precio',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary',
            }),
        }
        labels = {
            'name': 'Nombre del Servicio',
            'description': 'Descripción Breve',
            'icon': 'Icono',
            'price_text': 'Precio (opcional)',
            'is_active': '¿Mostrar este servicio?',
            'is_featured': '¿Destacar en home?',
        }


class TestimonialForm(forms.ModelForm):
    """
    Formulario para crear/editar testimonios.
    """
    
    class Meta:
        model = Testimonial
        fields = ['client_name', 'company', 'position', 'content', 'rating', 'is_active', 'is_featured']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Nombre del cliente',
            }),
            'company': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Empresa (opcional)',
            }),
            'position': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Cargo (opcional)',
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'rows': 4,
                'placeholder': 'Testimonio del cliente...',
            }),
            'rating': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary',
            }),
        }

class ContactForm(forms.ModelForm):
    """
    Formulario de contacto público con validación y Tailwind CSS.
    """
    
    class Meta:
        model = ContactSubmission
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
                'placeholder': 'Tu nombre completo',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
                'placeholder': 'tu@email.com',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
                'placeholder': '+56 9 1234 5678 (opcional)',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
                'placeholder': 'Asunto del mensaje (opcional)',
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition',
                'rows': 6,
                'placeholder': 'Escribe tu mensaje aquí...',
                'required': True,
            }),
        }
        labels = {
            'name': 'Nombre',
            'email': 'Email',
            'phone': 'Teléfono',
            'subject': 'Asunto',
            'message': 'Mensaje',
        }
    
    def clean_email(self):
        """Validación adicional de email"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email
    
    def clean_message(self):
        """Validación de mensaje mínimo"""
        message = self.cleaned_data.get('message')
        if message and len(message) < 10:
            raise forms.ValidationError('El mensaje debe tener al menos 10 caracteres.')
        return message





