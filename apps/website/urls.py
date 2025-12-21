"""
URLs para la aplicación website
Incluye: home, dashboard, auth (se importa desde auth_urls), y edición inline
"""
from django.urls import path, include
from . import views

urlpatterns = [
    # ============================================================
    # PÁGINA PRINCIPAL
    # ============================================================
    path('', views.home, name='home'),
    
    # ============================================================
    # DASHBOARD (requiere login)
    # ============================================================
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/sections/', views.dashboard_sections, name='dashboard_sections'),
    path('dashboard/services/', views.dashboard_services, name='dashboard_services'),
    path('dashboard/testimonials/', views.dashboard_testimonials, name='dashboard_testimonials'),
    path('dashboard/contacts/', views.dashboard_contacts, name='dashboard_contacts'),
    
    # ============================================================
    # ACCIONES DE CONTACTOS (desde dashboard)
    # ============================================================
    path('contact/<int:contact_id>/read/', views.mark_contact_read, name='mark_contact_read'),
    path('contact/<int:contact_id>/replied/', views.mark_contact_replied, name='mark_contact_replied'),
    
    # ============================================================
    # FORMULARIO DE CONTACTO (público)
    # ============================================================
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    
    # ============================================================
    # EDICIÓN INLINE (requiere login)
    # ============================================================
    # Secciones
    path('section/<int:section_id>/edit/', views.edit_section, name='edit_section'),
    path('section/<int:section_id>/cancel/', views.cancel_edit_section, name='cancel_edit_section'),
    
    # Servicios
    path('service/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('service/<int:service_id>/cancel/', views.cancel_edit_service, name='cancel_edit_service'),
    path('service/<int:service_id>/delete/', views.delete_service, name='delete_service'),
    path('service/add/', views.add_service, name='add_service'),
    
    # ============================================================
    # LOGIN MODAL (para edición inline - HTMX)
    # ============================================================
    path('login-modal/', views.login_modal, name='login_modal'),
]