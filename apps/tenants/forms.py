# apps/tenants/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Client, Domain

class TenantOnboardingForm(forms.Form):
    # --- 1. DATOS DE ACCESO Y DOMINIO ---
    section_domain = forms.CharField(widget=forms.HiddenInput, required=False)
    
    name = forms.CharField(
        label="Nombre del Cliente / Empresa", 
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Constructora del Sur SpA'})
    )
    slug = forms.SlugField(
        label="Slug del Sistema", 
        max_length=100,
        help_text="Identificador único para URLs internas (ej: constructora-sur)"
    )
    domain = forms.CharField(
        label="Dominio (Sin http/https)", 
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'ej: constructorasur.cl'}),
        help_text="El dominio real donde se verá el sitio."
    )

    # --- 2. DISEÑO Y BRANDING ---
    section_design = forms.CharField(widget=forms.HiddenInput, required=False)
    
    # Aquí seleccionamos el diseño (Arquitectura Nivel 3)
    THEME_CHOICES = Client.THEME_CHOICES # Usamos los que definiste en el modelo
    template = forms.ChoiceField(
        label="Plantilla de Diseño", 
        choices=THEME_CHOICES, 
        initial='default'
    )
    
    logo = forms.ImageField(label="Logo Principal", required=False)
    
    primary_color = forms.CharField(
        label="Color Primario", 
        widget=forms.TextInput(attrs={'type': 'color'}), 
        initial='#0ea5e9'
    )
    secondary_color = forms.CharField(
        label="Color Secundario", 
        widget=forms.TextInput(attrs={'type': 'color'}), 
        initial='#0284c7'
    )

    # --- 3. DATOS DE CONTACTO PÚBLICO ---
    section_contact = forms.CharField(widget=forms.HiddenInput, required=False)
    
    whatsapp_number = forms.CharField(
        label="WhatsApp (569...)", 
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '56912345678'})
    )
    contact_email = forms.EmailField(label="Email de Contacto", required=False)
    
    # Validaciones personalizadas
    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if Client.objects.filter(slug=slug).exists():
            raise ValidationError("Este slug ya está ocupado.")
        return slug

    def clean_domain(self):
        domain = self.cleaned_data['domain'].lower().strip()
        # Quitamos http/https si lo pegaron por error
        domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
        if Domain.objects.filter(domain=domain).exists():
            raise ValidationError("Este dominio ya está registrado en el sistema.")
        return domain