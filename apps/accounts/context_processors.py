from apps.accounts.permissions import dashboard_permissions_for


def dashboard_permissions(request):
    """Expone ``dash_perms`` (acción -> bool) a las plantillas del dashboard.

    Solo comodidad de interfaz: el 403 de ``tenant_permission_required``
    es la defensa real.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    return {'dash_perms': dashboard_permissions_for(user, getattr(request, 'client', None))}
