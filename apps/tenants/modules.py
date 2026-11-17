"""
Registro de módulos del dashboard (CONS-08, opción A).

Declara qué módulos existen, qué flag de ``ClientSettings`` los enciende, qué
límite del plan les aplica, qué rutas del dashboard les pertenecen y qué
entradas de menú aportan. Esta card solo declara: ni el menú ni las vistas lo
consumen todavía (``CONS-09``).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class MenuEntry:
    label: str
    url_name: str
    icon: str
    permission: str  # clave de apps.accounts.permissions.DASHBOARD_PERMISSIONS
    order: int


@dataclass(frozen=True)
class Module:
    key: str
    label: str
    flag: str | None  # campo booleano de ClientSettings; None = siempre activo
    limit_field: str | None  # campo de Client con el límite del plan
    url_names: tuple[str, ...]  # rutas del dashboard que pertenecen al módulo
    menu: tuple[MenuEntry, ...] = ()
    public_component: str | None = None
    menu_visible_when_disabled: bool = False


MODULES = (
    Module(
        key='core',
        label='Sitio',
        flag=None,
        limit_field=None,
        url_names=(
            'dashboard',
            'dashboard_sections',
            'dashboard_branding',
            'edit_section_dashboard',
        ),
        menu=(
            MenuEntry('Inicio', 'dashboard', 'home', 'view_dashboard', 10),
            MenuEntry('Marca', 'dashboard_branding', 'palette', 'manage_branding', 20),
            MenuEntry('Secciones', 'dashboard_sections', 'layout', 'edit_content', 40),
        ),
    ),
    Module(
        key='services',
        label='Servicios',
        flag=None,
        limit_field='max_services',
        url_names=(
            'create_service',
            'edit_service_dashboard',
            'delete_service_dashboard',
            'toggle_service_active',
            'toggle_service_featured',
            'reorder_services',
        ),
        # Sin entrada propia: se gestionan desde Secciones.
    ),
    Module(
        key='gallery',
        label='Galería',
        flag='enable_gallery',
        limit_field='max_images',
        url_names=(
            # ``dashboard_portada`` va aquí y no en ``core``: la vista responde
            # con "El módulo de imágenes no está activado" si ``enable_gallery``
            # está apagado (views/branding.py), o sea depende del flag de galería.
            'dashboard_portada',
            'dashboard_gallery',
            'gallery_item_add',
            'gallery_item_edit',
            'gallery_item_delete',
            'gallery_item_toggle',
        ),
        menu=(
            MenuEntry('Portada', 'dashboard_portada', 'image', 'edit_content', 30),
            MenuEntry('Galería', 'dashboard_gallery', 'images', 'edit_content', 50),
        ),
    ),
    Module(
        key='contact',
        label='Contacto',
        flag='enable_contact_form',
        limit_field=None,
        url_names=(
            'dashboard_contacts',
            'mark_contact_read',
            'mark_contact_replied',
        ),
        menu=(
            MenuEntry('Mensajes', 'dashboard_contacts', 'mail', 'view_contacts', 60),
        ),
        menu_visible_when_disabled=True,
    ),
)


def get_module(key):
    for module in MODULES:
        if module.key == key:
            return module
    raise KeyError(key)


def is_enabled(client, key):
    """True si el módulo ``key`` está activo para ``client``.

    Sin flag: siempre. Con ``client=None`` o sin ``settings``: solo los que no
    tienen flag.
    """
    module = get_module(key)
    if module.flag is None:
        return True
    settings = getattr(client, 'settings', None) if client is not None else None
    if settings is None:
        return False
    return bool(getattr(settings, module.flag, False))


def enabled_modules(client):
    return tuple(m for m in MODULES if is_enabled(client, m.key))


def module_for_url(url_name):
    for module in MODULES:
        if url_name in module.url_names:
            return module
    return None
