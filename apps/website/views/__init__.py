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
from .media import media_embed_add, media_upload_confirm, media_upload_signature
from .public import contact_submit, data_subject_request, home, privacy_policy
from .sections import dashboard_sections, edit_section_dashboard
from .services import (
    create_service,
    create_service_dashboard,
    delete_service_dashboard,
    edit_service_dashboard,
    reorder_services,
    toggle_service,
    toggle_service_active,
    toggle_service_featured,
)

__all__ = [
    'contact_submit', 'data_subject_request',
    'create_service', 'create_service_dashboard', 'dashboard', 'dashboard_branding',
    'dashboard_contacts', 'dashboard_gallery', 'dashboard_portada', 'dashboard_sections',
    'delete_service_dashboard', 'edit_section_dashboard', 'edit_service_dashboard', 'gallery_item_add',
    'gallery_item_delete', 'gallery_item_edit', 'gallery_item_toggle', 'get_client_ip',
    'home', 'mark_contact_read', 'mark_contact_replied', 'privacy_policy', 'reorder_services',
    'toggle_service', 'toggle_service_active', 'toggle_service_featured',
    'media_embed_add', 'media_upload_confirm', 'media_upload_signature',
]
