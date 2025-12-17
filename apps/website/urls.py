"""
URLs para la aplicación website
"""

from django.urls import path
from . import views

urlpatterns = [
    # Página principal
    path('', views.home, name='home'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/sections/', views.dashboard_sections, name='dashboard_sections'),
    path('dashboard/services/', views.dashboard_services, name='dashboard_services'),
    path('dashboard/testimonials/', views.dashboard_testimonials, name='dashboard_testimonials'),
    path('dashboard/contacts/', views.dashboard_contacts, name='dashboard_contacts'),
    
    # Acciones de contactos
    path('contact/<int:contact_id>/read/', views.mark_contact_read, name='mark_contact_read'),
    path('contact/<int:contact_id>/replied/', views.mark_contact_replied, name='mark_contact_replied'),
    
    # Formulario de contacto (Card #10)
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    
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