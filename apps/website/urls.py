"""
URLs para la aplicación website
"""
from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),
    
    # Edición de secciones
    path('section/<int:section_id>/edit/', views.edit_section, name='edit_section'),
    path('section/<int:section_id>/cancel/', views.cancel_edit_section, name='cancel_edit_section'),
    
    # Gestión de servicios
    path('service/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('service/<int:service_id>/cancel/', views.cancel_edit_service, name='cancel_edit_service'),
    path('service/<int:service_id>/delete/', views.delete_service, name='delete_service'),
    path('service/add/', views.add_service, name='add_service'),
    
    # Login modal
    path('login-modal/', views.login_modal, name='login_modal'),
]