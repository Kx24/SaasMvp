# apps/accounts/views.py
"""
Vistas de autenticación y gestión de cuenta.
Login canónico por EMAIL, aislado por tenant (request.client).
"""

import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import UserProfile
from .forms import SetPasswordForm, LoginForm, RequestPasswordResetForm

logger = logging.getLogger(__name__)

REMEMBER_ME_AGE = 60 * 60 * 24 * 14  # 14 días


# ============================================================
# HELPER: autenticación aislada por tenant
# ============================================================
def _authenticate_tenant_user(request, tenant, email, password):
    """
    Resuelve y autentica un usuario DENTRO del tenant activo.

    Seguridad:
      - Aislamiento: solo considera UserProfile cuyo client == request.client.
        Un usuario de otro tenant NO puede entrar aunque el email/clave existan.
      - Anti-enumeración por timing: si no hay candidato, se corre igualmente un
        hash dummy para equiparar el tiempo de respuesta (evita distinguir
        "email no existe" de "clave incorrecta" por latencia).
    """
    if tenant is None:
        User().set_password(password)  # equaliza timing
        return None

    profile = (
        UserProfile.objects
        .select_related('user')
        .filter(user__email__iexact=email, client=tenant)
        .first()
    )

    if profile is None:
        User().set_password(password)  # equaliza timing, no revela existencia
        return None

    user = authenticate(request, username=profile.user.username, password=password)

    # Doble verificación de aislamiento
    if user is not None and user.pk == profile.user.pk:
        return user
    return None


# ============================================================
# LOGIN / LOGOUT
# ============================================================
@never_cache
@ensure_csrf_cookie
def login_view(request):
    """
    Login por email, aislado por tenant.

    Decoradores (heredan el fix CSRF-03 de client_login):
      @ensure_csrf_cookie → cookie csrftoken emitida en el GET.
      @never_cache → evita form 'stale' vía bfcache/botón atrás.

    Seguridad por diseño:
      login() rota el token CSRF y cicla la sesión → mitiga session fixation.
      Mensaje de error único → sin enumeración.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    tenant = getattr(request, 'client', None)
    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember_me', False)

            user = _authenticate_tenant_user(request, tenant, email, password)

            if user is not None:
                login(request, user)  # rota CSRF + cicla sesión

                # D4: remember_me funcional
                request.session.set_expiry(REMEMBER_ME_AGE if remember else 0)

                if hasattr(user, 'profile'):
                    user.profile.last_login_at = timezone.now()
                    user.profile.save(update_fields=['last_login_at'])

                logger.info(f"[Auth] Login OK: {email} @ {tenant.slug if tenant else '?'}")

                if next_url:
                    return redirect(next_url)
                return redirect('dashboard')

            # Genérico a propósito (anti-enumeración)
            messages.error(request, 'Email o contraseña incorrectos.')
            logger.warning(f"[Auth] Login fallido: {email} @ {tenant.slug if tenant else '?'}")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


@never_cache
def logout_view(request):
    """Cerrar sesión. Redirige al login."""
    if request.user.is_authenticated:
        logger.info(f"[Auth] Logout: {request.user.email}")
        logout(request)
        messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('accounts:login')


# ============================================================
# SET PASSWORD (token de invitación / reset)
# ============================================================
def set_password_view(request, token):
    """Configurar contraseña usando token de invitación. GET/POST /auth/set-password/<token>/"""
    try:
        profile = UserProfile.objects.select_related('user', 'client').get(
            invitation_token=token
        )
    except UserProfile.DoesNotExist:
        logger.warning(f"[Auth] Token no encontrado: {token}")
        return render(request, 'accounts/set_password_invalid.html', {
            'error': 'token_not_found',
            'message': 'El enlace no es válido o ya fue utilizado.'
        })

    if not profile.is_invitation_valid():
        logger.warning(f"[Auth] Token expirado: {profile.user.email}")
        return render(request, 'accounts/set_password_expired.html', {
            'email': profile.user.email,
            'message': 'El enlace ha expirado. Solicita uno nuevo.'
        })

    user = profile.user

    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            with transaction.atomic():
                user.set_password(password)
                user.save()
                profile.clear_invitation()
                logger.info(f"[Auth] Contraseña configurada: {user.email}")
            login(request, user)
            messages.success(request, '¡Contraseña configurada exitosamente!')
            return redirect('dashboard') if profile.client else redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SetPasswordForm()

    return render(request, 'accounts/set_password.html', {
        'form': form, 'user': user, 'client': profile.client,
    })


# ============================================================
# RESET PASSWORD (solicitud)
# ============================================================
def request_password_reset_view(request):
    """Solicitar recuperación. GET/POST /auth/forgot-password/"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RequestPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            tenant = getattr(request, 'client', None)
            try:
                # Aislado por tenant: solo resetea usuarios del tenant activo
                profile = UserProfile.objects.select_related('user').get(
                    user__email__iexact=email, client=tenant
                )
                user = profile.user
                token = profile.generate_invitation_token(days=1)
                from apps.orders.services.email_service import send_set_password_email
                send_set_password_email(user, str(token), is_reset=True)
                logger.info(f"[Auth] Reset solicitado: {email} @ {tenant.slug if tenant else '?'}")
            except UserProfile.DoesNotExist:
                logger.info(f"[Auth] Reset para email inexistente en tenant: {email}")

            # Mensaje único siempre (no revela existencia)
            messages.success(
                request,
                'Si el email existe en nuestro sistema, recibirás instrucciones para recuperar tu contraseña.'
            )
            return redirect('accounts:login')
    else:
        form = RequestPasswordResetForm()

    return render(request, 'accounts/request_password_reset.html', {'form': form})


# ============================================================
# CHANGE PASSWORD (autenticado)
# ============================================================
@login_required
def change_password_view(request):
    """Cambiar contraseña. GET/POST /auth/change-password/"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not request.user.check_password(current_password):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return render(request, 'accounts/change_password.html')

        if len(new_password) < 8:
            messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
            return render(request, 'accounts/change_password.html')

        if new_password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'accounts/change_password.html')

        request.user.set_password(new_password)
        request.user.save()
        login(request, request.user)  # re-autenticar para no cerrar sesión
        messages.success(request, 'Contraseña actualizada correctamente.')
        logger.info(f"[Auth] Contraseña cambiada: {request.user.email}")
        return redirect('dashboard')

    return render(request, 'accounts/change_password.html')