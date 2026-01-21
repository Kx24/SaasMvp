from django.urls import path
from . import views

# Definimos el namespace para evitar confusiones (opcional pero recomendado)
# app_name = 'tenants' 

urlpatterns = [
    # 1. Onboarding (Crear Nuevo)
    path('superadmin/nuevo/', views.onboarding_view, name='superadmin_onboarding'),

    # 2. Lista de Tenants (Dashboard)
    # IMPORTANTE: El 'name' aquí es la clave para que funcione el redirect
    path('tenants/', views.tenant_list, name='tenant_list'),
]