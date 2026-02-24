# apps/accounts/forms.py
"""
Formularios de autenticación y gestión de cuenta.
"""

from django import forms
from django.core.validators import MinLengthValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class SetPasswordForm(forms.Form):
    """
    Formulario para configurar/restablecer contraseña.
    """
    
    password = forms.CharField(
        label="Nueva contraseña",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        }),
        help_text="Mínimo 8 caracteres"
    )
    
    password_confirm = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        })
    )
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        # Validar fortaleza
        if len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        
        # Validaciones adicionales de Django (opcional)
        try:
            validate_password(password)
        except ValidationError as e:
            raise ValidationError(e.messages)
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError("Las contraseñas no coinciden.")
        
        return cleaned_data


class LoginForm(forms.Form):
    """
    Formulario de login.
    """
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'tu@email.com',
            'autocomplete': 'email',
        })
    )
    
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        label="Recordarme",
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
        })
    )


class RequestPasswordResetForm(forms.Form):
    """
    Formulario para solicitar recuperación de contraseña.
    """
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'tu@email.com',
            'autocomplete': 'email',
        }),
        help_text="Ingresa el email asociado a tu cuenta"
    )
