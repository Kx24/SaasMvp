"""
Formularios para la aplicación Website
CARD #15: Forms para dashboard
"""
from django import forms
from .models import Section, Service, ContactSubmission


class SectionForm(forms.ModelForm):
    """
    Formulario para editar secciones
    """
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


class ServiceForm(forms.ModelForm):
    """
    Formulario para crear/editar servicios
    """
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


class ContactForm(forms.ModelForm):
    """
    Formulario público de contacto
    """
    class Meta:
        model = ContactSubmission
        fields = ['name', 'email', 'phone', 'company', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Tu nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'tu@email.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': '+56 9 1234 5678 (opcional)'
            }),
            'company': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Tu empresa (opcional)'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Asunto del mensaje'
            }),
            'message': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                'placeholder': 'Escribe tu mensaje aquí...',
                'rows': 5
            }),
        }
        labels = {
            'name': 'Nombre',
            'email': 'Email',
            'phone': 'Teléfono',
            'company': 'Empresa',
            'subject': 'Asunto',
            'message': 'Mensaje'
        }