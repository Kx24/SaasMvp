# apps/accounts/urls.py
"""
URLs de autenticación y gestión de cuenta.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Login / Logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Configurar contraseña (con token)
    path('set-password/<uuid:token>/', views.set_password_view, name='set_password'),
    
    # Recuperar contraseña
    path('forgot-password/', views.request_password_reset_view, name='forgot_password'),
    
    # Cambiar contraseña (autenticado)
    path('change-password/', views.change_password_view, name='change_password'),
]
