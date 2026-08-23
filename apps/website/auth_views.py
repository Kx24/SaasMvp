"""
Vistas de autenticación para clientes
apps/website/auth_views.py
"""
import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

from apps.core.rate_limit import RateLimiter

# #MED-05b: mismo texto para credenciales inválidas y para rate limit —
# el bloqueo no debe filtrar información (ni existencia de usuario ni
# existencia del límite), solo cambia el status code (429 vs 200).
LOGIN_GENERIC_ERROR = 'Usuario o contraseña incorrectos.'


def _login_rate_limiter(request, username):
    # Por IP+username (+tenant, que RateLimiter ya incluye): un atacante
    # distribuido no bloquea a un usuario ajeno desde otra IP, y una IP
    # compartida (NAT) no bloquea a todos los usuarios a la vez.
    username_hash = hashlib.sha256(username.strip().lower().encode()).hexdigest()[:12]
    return RateLimiter(
        request,
        scope='login',
        limit=getattr(settings, 'RATE_LIMIT_LOGIN_LIMIT', 5),
        period=getattr(settings, 'RATE_LIMIT_LOGIN_PERIOD', 300),
        key_extra=username_hash,
    )


def _user_belongs_to_tenant(user, request):
    """
    #AUD-03: además de autenticar, el login debe verificar que el usuario
    pertenezca al tenant del dominio visitado. Superusers y staff (acceso
    de Django admin, no ligado a un tenant) quedan exentos.
    """
    if user.is_superuser or user.is_staff:
        return True

    client = getattr(request, 'client', None)
    profile = getattr(user, 'profile', None)

    return client is not None and profile is not None and profile.client_id == client.id


@never_cache
@ensure_csrf_cookie
def client_login(request):
    """
    Login custom para clientes.

    Fix CSRF-03:
      @ensure_csrf_cookie → emite la cookie `csrftoken` en el GET, sincronizada
          con el token embebido en el form. Mata el caso "form sin cookie" en
          una primera carga limpia.
      @never_cache → impide que bfcache / botón atrás sirvan un formulario con
          token viejo tras la rotación del login. Solo headers → sin coste de
          cómputo ni DB → TTFB intacto.

    Seguridad por diseño:
      login() rota el token CSRF y cicla la clave de sesión → mitiga session
          fixation sin código extra.
      authenticate() corre el password hasher aunque el usuario no exista
          (Django ModelBackend) → timing constante, sin enumeración.
      Mensaje de error único → no revela si el usuario existe.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        limiter = _login_rate_limiter(request, username)
        if limiter.is_exceeded():
            # #MED-05b: bloqueado — ni la contraseña correcta entra (si
            # entrara, el 429 confirmaría credenciales válidas igual).
            messages.error(request, LOGIN_GENERIC_ERROR)
            context = {
                'client': request.client if hasattr(request, 'client') else None,
            }
            return render(request, 'auth/login.html', context, status=429)

        user = authenticate(request, username=username, password=password)

        if user is not None and _user_belongs_to_tenant(user, request):
            login(request, user)  # rota CSRF token + cicla sesión

            if user.is_superuser or user.is_staff:
                next_url = request.GET.get('next')
                if next_url and 'superadmin' in next_url:
                    return redirect('/superadmin/')
                return redirect('home')

            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect('home')

        # Genérico a propósito — no filtra existencia de usuario
        limiter.increment()  # solo los intentos FALLIDOS consumen cupo
        messages.error(request, LOGIN_GENERIC_ERROR)

    context = {
        'client': request.client if hasattr(request, 'client') else None,
    }
    return render(request, 'auth/login.html', context)


@never_cache
@login_required(login_url='/auth/login/')
def client_logout(request):
    """
    Logout custom. @never_cache evita que el botón atrás muestre la página
    post-logout desde caché del navegador.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Hasta pronto, {username}!')

    return redirect('home')