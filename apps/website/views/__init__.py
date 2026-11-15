"""Vistas de `website`, separadas por área (CONS-07).

Re-exporta todos los nombres que antes vivían en el módulo único `views.py`,
para que `urls.py` y los imports existentes sigan funcionando.
"""
from apps.core.rate_limit import get_client_ip

from .branding import dashboard, dashboard_branding, dashboard_portada
from .contacts import dashboard_contacts, mark_contact_read, mark_contact_replied
from .gallery import (
    dashboard_gallery,
    gallery_item_add,
    gallery_item_delete,
    gallery_item_edit,
    gallery_item_toggle,
)
from .public import contact_submit, home, login_modal
from .sections import cancel_edit_section, dashboard_sections, edit_section, edit_section_dashboard
from .services import (
    add_service,
    cancel_edit_service,
    create_service,
    create_service_dashboard,
    dashboard_services,
    delete_service,
    delete_service_dashboard,
    edit_service,
    edit_service_dashboard,
    reorder_services,
    toggle_service,
    toggle_service_active,
    toggle_service_featured,
)

__all__ = [
    'add_service', 'cancel_edit_section', 'cancel_edit_service', 'contact_submit',
    'create_service', 'create_service_dashboard', 'dashboard', 'dashboard_branding',
    'dashboard_contacts', 'dashboard_gallery', 'dashboard_portada', 'dashboard_sections',
    'dashboard_services', 'delete_service', 'delete_service_dashboard', 'edit_section',
    'edit_section_dashboard', 'edit_service', 'edit_service_dashboard', 'gallery_item_add',
    'gallery_item_delete', 'gallery_item_edit', 'gallery_item_toggle', 'get_client_ip',
    'home', 'login_modal', 'mark_contact_read', 'mark_contact_replied', 'reorder_services',
    'toggle_service', 'toggle_service_active', 'toggle_service_featured',
]
