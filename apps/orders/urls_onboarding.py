# apps/orders/urls_onboarding.py
"""
URLs para el onboarding post-pago.

Estas URLs son públicas (acceso por token) y no requieren autenticación.
"""

from django.urls import path
from . import views_onboarding

# Nota: Estas URLs se incluyen en config/urls.py directamente,
# no bajo el namespace 'orders' para tener URLs más limpias.

urlpatterns = [
    # Formulario de onboarding
    path(
        '<uuid:token>/',
        views_onboarding.onboarding_view,
        name='onboarding'
    ),
    
    # Página de éxito
    path(
        '<uuid:token>/success/',
        views_onboarding.onboarding_success_view,
        name='onboarding_success'
    ),
]
