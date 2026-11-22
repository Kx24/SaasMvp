"""
Registro de módulos del dashboard (CONS-08, opción A).

Declara qué módulos existen, qué flag de ``ClientSettings`` los enciende, qué
límite del plan les aplica, qué rutas del dashboard les pertenecen y qué
entradas de menú aportan. El menú (``dashboard_menu``) y el acceso
(``module_required``) derivan de aquí (``CONS-09``).
"""
import functools
from collections.abc import Callable
from dataclasses import dataclass

from django.http import Http404


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
    usage: Callable[[object], int] | None = None  # cuenta el uso del límite
    limit_noun: str = ''  # plural para el mensaje: "servicios", "imágenes"


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
            'dashboard_portada',
            'edit_section_dashboard',
        ),
        menu=(
            MenuEntry('Inicio', 'dashboard', 'home', 'view_dashboard', 10),
            MenuEntry('Marca', 'dashboard_branding', 'palette', 'manage_branding', 20),
            MenuEntry('Portada', 'dashboard_portada', 'image', 'edit_content', 30),
            MenuEntry('Secciones', 'dashboard_sections', 'layout', 'edit_content', 40),
        ),
    ),
    Module(
        key='services',
        label='Servicios',
        flag=None,
        limit_field='max_services',
        usage=lambda client: _usage_services(client),
        limit_noun='servicios',
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
        usage=lambda client: _usage_gallery(client),
        limit_noun='imágenes de galería',
        url_names=(
            'dashboard_gallery',
            'gallery_item_add',
            'gallery_item_edit',
            'gallery_item_delete',
            'gallery_item_toggle',
        ),
        menu=(
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


class ModuleLimitReached(Exception):
    """El tenant alcanzó el tope de su plan para un módulo (BIZ-01)."""

    def __init__(self, module, limit):
        self.module = module
        self.limit = limit
        super().__init__(f'Límite alcanzado en {module.key}: {limit}')

    @property
    def message(self):
        nombre = self.module.limit_noun
        return (
            f'Tu plan permite {self.limit} {nombre}. '
            'Borra uno o pide una ampliación.'
        )


def _usage_services(client):
    from apps.website.models import Service

    return Service.objects.filter(client=client).count()


def _usage_gallery(client):
    from apps.website.models import GalleryItem

    return GalleryItem.objects.filter(
        client=client, section__section_type='gallery'
    ).count()


def limit_for(client, key):
    """Tope efectivo del módulo ``key`` para ``client``; ``None`` = sin límite.

    Galería: el menor entre ``ClientSettings.gallery_images_limit`` y
    ``Client.max_images``. Un valor <= 0 significa "sin cupo".
    """
    module = get_module(key)
    if module.limit_field is None:
        return None
    limits = [getattr(client, module.limit_field, None)]
    if key == 'gallery':
        settings = getattr(client, 'settings', None)
        limits.append(getattr(settings, 'gallery_images_limit', None))
    limits = [max(value, 0) for value in limits if value is not None]
    return min(limits) if limits else None


def usage_for(client, key):
    module = get_module(key)
    if module.usage is None:
        return 0
    return module.usage(client)


def check_limit(client, key, usage=None):
    """Lanza ``ModuleLimitReached`` si ``usage >= limit``.

    ``usage`` permite al llamador pasar un conteo más específico (p. ej. el de
    una galería de servicio); por defecto se usa el del registro.
    """
    limit = limit_for(client, key)
    if limit is None:
        return
    if usage is None:
        usage = usage_for(client, key)
    if usage >= limit:
        raise ModuleLimitReached(get_module(key), limit)


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


def module_required(key):
    """Decorador de vista: 404 si el módulo ``key`` está apagado para el tenant.

    Va *debajo* de ``tenant_permission_required`` (primero login y tenant,
    luego módulo).
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def _check_module(request, *args, **kwargs):
            if not is_enabled(getattr(request, 'client', None), key):
                raise Http404('Módulo no disponible.')
            return view_func(request, *args, **kwargs)

        return _check_module

    return decorator


def enabled_modules(client):
    return tuple(m for m in MODULES if is_enabled(client, m.key))


def module_for_url(url_name):
    for module in MODULES:
        if url_name in module.url_names:
            return module
    return None
