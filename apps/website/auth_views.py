"""
Vistas de autenticación para clientes
apps/website/auth_views.py
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie


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

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)  # rota CSRF token + cicla sesión

            if user.is_superuser or user.is_staff:
                next_url = request.GET.get('next')
                if next_url and 'superadmin' in next_url:
                    return redirect('/superadmin/')
                return redirect('home')

            messages.success(request, f'¡Bienvenido {user.username}!')
            return redirect('home')

        # Genérico a propósito — no filtra existencia de usuario
        messages.error(request, 'Usuario o contraseña incorrectos.')

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