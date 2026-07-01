"""
URLs para la aplicación website
Incluye: home, dashboard, auth (se importa desde auth_urls), y edición inline
"""
from django.urls import path, include
from apps.website.views import dashboard_branding
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
    path('dashboard/contacts/', views.dashboard_contacts, name='dashboard_contacts'),
    path('dashboard/branding/', dashboard_branding, name='dashboard_branding'),
    path('dashboard/portada/', views.dashboard_portada, name='dashboard_portada'),
    
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

    # ============================================================
    # DASHBOARD - SECCIONES #card 15
    # ============================================================
    path('dashboard/section/<int:section_id>/edit/', views.edit_section_dashboard, name='edit_section_dashboard'),

    # ============================================================
    # DASHBOARD - SERVICIOS CRUD
    # ============================================================
    path('dashboard/service/create/', views.create_service, name='create_service'),
    path('dashboard/service/<int:service_id>/edit/', views.edit_service_dashboard, name='edit_service_dashboard'),
    path('dashboard/service/<int:service_id>/delete/', views.delete_service_dashboard, name='delete_service_dashboard'),

    # ============================================================
    # DASHBOARD - SERVICIOS AJAX
    # ============================================================
    path('dashboard/service/<int:service_id>/toggle-active/', views.toggle_service_active, name='toggle_service_active'),
    path('dashboard/service/<int:service_id>/toggle-featured/', views.toggle_service_featured, name='toggle_service_featured'),
    path('dashboard/services/reorder/', views.reorder_services, name='reorder_services'),
    path('dashboard/gallery/', views.dashboard_gallery, name='dashboard_gallery'), #Lineas galería
    path('dashboard/gallery/add/', views.gallery_item_add, name='gallery_item_add'),
    path('dashboard/gallery/<int:item_id>/edit/', views.gallery_item_edit, name='gallery_item_edit'),
    path('dashboard/gallery/<int:item_id>/delete/', views.gallery_item_delete, name='gallery_item_delete'),
    path('dashboard/gallery/<int:item_id>/toggle/', views.gallery_item_toggle, name='gallery_item_toggle'),

]