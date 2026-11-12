# apps/accounts/views.py
"""
Vistas de autenticación y gestión de cuenta.

Incluye:
- Configurar contraseña (post-onboarding)
- Recuperar contraseña
- Login/Logout
"""

import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render

from apps.core.logging_utils import email_ref

from .forms import LoginForm, RequestPasswordResetForm, SetPasswordForm
from .models import UserProfile

logger = logging.getLogger(__name__)


def set_password_view(request, token):
    """
    Vista para configurar contraseña usando token de invitación.
    
    URL: GET/POST /auth/set-password/<token>/
    
    Usado para:
    - Primera configuración post-onboarding
    - Recuperación de contraseña
    """
    # Buscar profile por token
    try:
        profile = UserProfile.objects.select_related('user', 'client').get(
            invitation_token=token
        )
    except UserProfile.DoesNotExist:
        logger.warning(f"[Auth] Token de invitación no encontrado: {token}")
        return render(request, 'accounts/set_password_invalid.html', {
            'error': 'token_not_found',
            'message': 'El enlace no es válido o ya fue utilizado.'
        })
    
    # Validar expiración
    if not profile.is_invitation_valid():
        logger.warning(f"[Auth] Token expirado para user_id={profile.user_id}")
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
                # Establecer contraseña
                user.set_password(password)
                user.save()
                
                # Limpiar token
                profile.clear_invitation()
                
                logger.info(f"[Auth] Contraseña configurada para user_id={user.pk}")
            
            # Auto-login
            login(request, user)
            
            messages.success(request, '¡Contraseña configurada exitosamente!')
            
            # Redirigir según contexto
            if profile.client:
                return redirect('dashboard')
            else:
                return redirect('home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = SetPasswordForm()
    
    context = {
        'form': form,
        'user': user,
        'client': profile.client,
    }
    
    return render(request, 'accounts/set_password.html', context)


def request_password_reset_view(request):
    """
    Solicitar recuperación de contraseña.
    
    URL: GET/POST /auth/forgot-password/
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RequestPasswordResetForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            
            try:
                user = User.objects.get(email=email)
                profile = user.profile
                
                # Generar nuevo token
                token = profile.generate_invitation_token(days=1)  # 24 horas para reset
                
                # Enviar email
                from apps.orders.services.email_service import send_set_password_email
                send_set_password_email(user, str(token), is_reset=True)
                
                logger.info(f"[Auth] Reset password solicitado: {email_ref(email)}")
                
            except User.DoesNotExist:
                # No revelar si el email existe o no
                logger.info(f"[Auth] Reset password solicitado: {email_ref(email)}")
            except UserProfile.DoesNotExist:
                logger.warning(f"[Auth] Reset password para usuario sin profile: {email_ref(email)}")
            
            # Siempre mostrar mensaje de éxito (seguridad)
            messages.success(
                request, 
                'Si el email existe en nuestro sistema, recibirás instrucciones para recuperar tu contraseña.'
            )
            return redirect('accounts:login')
    else:
        form = RequestPasswordResetForm()
    
    return render(request, 'accounts/request_password_reset.html', {'form': form})


def login_view(request):
    """
    Vista de login.
    
    URL: GET/POST /auth/login/
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    next_url = request.GET.get('next', '')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']
            
            # Buscar usuario por email
            try:
                user = User.objects.get(email=email)
                user = authenticate(request, username=user.username, password=password)
                
                if user is not None:
                    login(request, user)
                    
                    # User.last_login ya lo actualiza login(); UserProfile no
                    # tiene campo last_login_at (BOLT-12, hallazgo incidental).
                    logger.info(f"[Auth] Login exitoso user_id={user.pk}")
                    
                    # Redirigir
                    if next_url:
                        return redirect(next_url)
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Email o contraseña incorrectos.')
                    logger.warning(f"[Auth] Login fallido: {email_ref(email)}")

            except User.DoesNotExist:
                # Mismo mensaje y mismo log que contraseña incorrecta: no revelar
                # si el email tiene cuenta (SEC-07).
                messages.error(request, 'Email o contraseña incorrectos.')
                logger.warning(f"[Auth] Login fallido: {email_ref(email)}")
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url
    })


def logout_view(request):
    """
    Cerrar sesión.
    
    URL: GET/POST /auth/logout/
    """
    if request.user.is_authenticated:
        logger.info(f"[Auth] Logout user_id={request.user.pk}")
        logout(request)
        messages.success(request, 'Has cerrado sesión correctamente.')
    
    return redirect('accounts:login')


@login_required
def change_password_view(request):
    """
    Cambiar contraseña (usuario autenticado).
    
    URL: GET/POST /auth/change-password/
    """
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validar contraseña actual
        if not request.user.check_password(current_password):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return render(request, 'accounts/change_password.html')
        
        # Validar nueva contraseña
        if len(new_password) < 8:
            messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
            return render(request, 'accounts/change_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'accounts/change_password.html')
        
        # Cambiar contraseña
        request.user.set_password(new_password)
        request.user.save()
        
        # Re-autenticar para no cerrar sesión
        login(request, request.user)
        
        messages.success(request, 'Contraseña actualizada correctamente.')
        logger.info(f"[Auth] Contraseña cambiada user_id={request.user.pk}")
        
        return redirect('dashboard')
    
    return render(request, 'accounts/change_password.html')
