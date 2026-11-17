from apps.accounts.permissions import dashboard_permissions_for, has_dashboard_permission
from apps.tenants.modules import MODULES, is_enabled


def dashboard_menu(request):
    """Expone ``dash_menu``: entradas de menú visibles para este usuario y tenant.

    Una entrada aparece si su módulo está activo (o es
    ``menu_visible_when_disabled``) y el rol permite su permiso.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    client = getattr(request, 'client', None)
    entries = []
    for module in MODULES:
        if not (is_enabled(client, module.key) or module.menu_visible_when_disabled):
            continue
        for entry in module.menu:
            if has_dashboard_permission(user, client, entry.permission):
                entries.append(entry)
    entries.sort(key=lambda e: e.order)
    context = {'dash_menu': entries}
    if client is not None and any(e.url_name == 'dashboard_contacts' for e in entries):
        # Contador de "Mensajes" del menú: nuevos, sin spam ni correos bloqueados.
        from apps.website.models import ContactSubmission, exclude_blocked

        context['unread_contacts'] = exclude_blocked(
            ContactSubmission.objects.filter(client=client, status='new', is_spam=False),
            client,
        ).count()
    return context


def dashboard_permissions(request):
    """Expone ``dash_perms`` (acción -> bool) a las plantillas del dashboard.

    Solo comodidad de interfaz: el 403 de ``tenant_permission_required``
    es la defensa real.
    """
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    return {'dash_perms': dashboard_permissions_for(user, getattr(request, 'client', None))}
