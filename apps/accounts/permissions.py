"""
Matriz de permisos del dashboard por rol (DASH-04).

Única fuente de verdad: qué roles de ``UserProfile.role`` pueden ejecutar
cada acción del dashboard. Las vistas la aplican con
``apps.accounts.decorators.tenant_permission_required`` y las plantillas la
consultan vía ``dash_perms`` (context processor).
"""

_ALL = frozenset({'owner', 'admin', 'editor', 'viewer'})
_EDIT = frozenset({'owner', 'admin', 'editor'})
_ADMIN = frozenset({'owner', 'admin'})

DASHBOARD_PERMISSIONS = {
    'view_dashboard': _ALL,
    'view_contacts': _EDIT,
    'edit_content': _EDIT,
    'manage_contacts': _EDIT,
    'delete_content': _ADMIN,
    'manage_branding': _ADMIN,
}


def has_dashboard_permission(user, client, action):
    """True si ``user`` puede ejecutar ``action`` en el tenant ``client``.

    Superuser siempre; sin perfil, de otro tenant, sin tenant o con rol
    desconocido: no.
    """
    if user is None or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True
    if client is None:
        return False
    profile = getattr(user, 'profile', None)
    if profile is None or profile.client_id != client.id:
        return False
    return profile.role in DASHBOARD_PERMISSIONS.get(action, frozenset())


def dashboard_permissions_for(user, client):
    """Dict acción -> bool para las plantillas."""
    return {
        action: has_dashboard_permission(user, client, action)
        for action in DASHBOARD_PERMISSIONS
    }
