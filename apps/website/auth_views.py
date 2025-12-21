"""
Vistas de autenticación para clientes
apps/website/auth_views.py
"""
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse


def client_login(request):
    """
    Login custom para clientes.
    Después de login exitoso, redirige a home (con botones de edición).
    """
    # Si ya está logueado, redirigir a home
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Autenticar
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login exitoso
            login(request, user)
            
            # Verificar si es superadmin
            if user.is_superuser or user.is_staff:
                # Superadmin va a Django Admin si lo solicita
                next_url = request.GET.get('next')
                if next_url and 'superadmin' in next_url:
                    return redirect('/superadmin/')
                # Si no, va a home como todos
                return redirect('home')
            else:
                # Cliente normal va a home
                messages.success(request, f'¡Bienvenido {user.username}!')
                return redirect('home')
        else:
            # Login fallido
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    # GET request o login fallido
    context = {
        'client': request.client if hasattr(request, 'client') else None,
    }
    return render(request, 'auth/login.html', context)


@login_required(login_url='/auth/login/')
def client_logout(request):
    """
    Logout custom para clientes.
    Redirige a home después de cerrar sesión.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Hasta pronto, {username}!')
    
    return redirect('home')