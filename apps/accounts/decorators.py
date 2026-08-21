"""
Decoradores de autorización multi-tenant.

#AUD-03: @login_required por sí solo verifica que haya *alguien* logueado,
no que esa persona pertenezca al tenant del dominio que está visitando.
Sin este chequeo, un owner del tenant A puede loguearse y editar el
contenido del tenant B con solo visitar el dominio de B (mismo backend,
mismas cookies de sesión no comparten dominio pero la sesión de A en el
dominio de A es válida para acceder al dashboard de A -- el problema real
es cross-tenant: nada impedía que un usuario con `profile.client == A`
accediera a vistas de dashboard cuando `request.client == B`).
"""
import functools

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def tenant_member_required(view_func):
    """
    Exige que el usuario autenticado pertenezca al tenant del dominio
    actual (``request.client``), o sea superuser.

    Comportamiento:
    - No autenticado -> redirect a login (delega en `login_required`).
    - Autenticado sin `UserProfile`, con perfil de otro tenant, o sin
      tenant detectado en el request -> 403 (nunca 500).
    - Superuser -> siempre pasa, sin importar el tenant.
    """

    @functools.wraps(view_func)
    def _check_tenant_membership(request, *args, **kwargs):
        user = request.user

        if user.is_superuser:
            return view_func(request, *args, **kwargs)

        client = getattr(request, 'client', None)
        profile = getattr(user, 'profile', None)

        if client is None or profile is None or profile.client_id != client.id:
            return HttpResponseForbidden('No tienes acceso a este sitio.')

        return view_func(request, *args, **kwargs)

    return login_required(login_url='/auth/login/')(_check_tenant_membership)
