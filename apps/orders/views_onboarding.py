# apps/orders/views_onboarding.py
"""
Vistas para el onboarding post-pago.

Flujo:
1. Cliente paga → recibe email con link de onboarding
2. Cliente accede a /onboarding/{token}/
3. Sistema valida token y muestra formulario
4. Cliente completa datos → se crea Tenant + Usuario
5. Redirect a página de éxito con credenciales
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.contrib import messages
import uuid

from .models import Order, Plan
from .forms import ClientOnboardingForm
from apps.tenants.models import Client, Domain, ClientSettings
from apps.website.models import Section
from apps.accounts.models import UserProfile

logger = logging.getLogger(__name__)


def onboarding_view(request, token):
    """
    Vista principal de onboarding post-pago.
    
    URL: GET/POST /onboarding/{token}/
    
    Flujo:
    1. Validar token
    2. GET: Mostrar formulario
    3. POST: Procesar y crear tenant
    """
    # Buscar orden por token
    try:
        order = Order.objects.select_related('plan').get(onboarding_token=token)
    except Order.DoesNotExist:
        logger.warning(f"[Onboarding] Token no encontrado: {token}")
        return render(request, 'orders/onboarding_invalid.html', {
            'error': 'token_not_found',
            'message': 'El enlace no es válido o ha expirado.'
        })
    
    # Validar estado de la orden
    if order.status == 'completed':
        logger.info(f"[Onboarding] Orden ya completada: {order.order_number}")
        return render(request, 'orders/onboarding_completed.html', {
            'order': order,
            'client': order.client
        })
    
    if order.status not in ['paid', 'onboarding']:
        logger.warning(f"[Onboarding] Estado inválido: {order.order_number} - {order.status}")
        return render(request, 'orders/onboarding_invalid.html', {
            'error': 'invalid_status',
            'message': 'Esta orden no está lista para configuración.'
        })
    
    # Validar expiración del token
    if not order.is_token_valid():
        logger.warning(f"[Onboarding] Token expirado: {order.order_number}")
        order.mark_as_expired()
        return render(request, 'orders/onboarding_expired.html', {
            'order': order,
            'message': 'El enlace ha expirado. Por favor contacta a soporte.'
        })
    
    # Marcar que comenzó el onboarding
    if order.status == 'paid':
        order.start_onboarding()
    
    # Obtener temas disponibles según el plan
    available_themes = order.plan.get_available_themes_list()
    if not available_themes:
        available_themes = ['default']
    
    if request.method == 'POST':
        form = ClientOnboardingForm(
            request.POST,
            request.FILES,
            available_themes=available_themes
        )
        
        if form.is_valid():
            try:
                # Procesar onboarding
                client, user = process_onboarding(order, form.cleaned_data)
                
                logger.info(
                    f"[Onboarding] Completado: {order.order_number} - "
                    f"Client: {client.slug} - User: {user.email}"
                )
                
                # Redirigir a página de éxito
                return redirect('orders:onboarding_success', token=token)
                
            except Exception as e:
                logger.exception(f"[Onboarding] Error procesando: {e}")
                messages.error(
                    request,
                    'Ocurrió un error al crear tu sitio. Por favor intenta nuevamente.'
                )
        else:
            # Mostrar errores del formulario
            logger.warning(f"[Onboarding] Errores de validación: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # GET - mostrar formulario vacío
        form = ClientOnboardingForm(available_themes=available_themes)
    
    context = {
        'form': form,
        'order': order,
        'plan': order.plan,
        'available_themes': available_themes,
    }
    
    return render(request, 'orders/onboarding.html', context)


def onboarding_success_view(request, token):
    """
    Página de éxito post-onboarding.
    
    Muestra:
    - Confirmación de que el sitio está listo
    - URL del sitio
    - Instrucciones para configurar contraseña
    
    URL: GET /onboarding/{token}/success/
    """
    try:
        order = Order.objects.select_related('plan', 'client').get(
            onboarding_token=token
        )
    except Order.DoesNotExist:
        # Buscar por token anterior (puede haber sido limpiado)
        # Intentar buscar la orden completada más reciente para este email
        raise Http404("Orden no encontrada")
    
    if order.status != 'completed' or not order.client:
        return redirect('orders:onboarding', token=token)
    
    # Obtener el usuario creado
    user_profile = UserProfile.objects.filter(client=order.client).first()
    
    context = {
        'order': order,
        'client': order.client,
        'user_profile': user_profile,
        'site_url': order.client.get_absolute_url(),
        'dashboard_url': f"/dashboard/",  # Ajustar según tu URL
    }
    
    return render(request, 'orders/onboarding_success.html', context)


@transaction.atomic
def process_onboarding(order: Order, data: dict) -> tuple:
    """
    Procesa el onboarding y crea todos los recursos necesarios.
    
    Args:
        order: Orden pagada
        data: Datos del formulario limpiados
    
    Returns:
        tuple: (Client, User)
    
    Crea:
    1. Client (tenant)
    2. Domain (subdominio)
    3. ClientSettings
    4. User (owner del tenant)
    5. UserProfile
    6. Secciones iniciales
    """
    plan = order.plan
    
    # =========================================================================
    # 1. CREAR CLIENTE (TENANT)
    # =========================================================================
    
    client = Client.objects.create(
        name=data['company_name'],
        slug=data['slug'],
        company_name=data['company_name'],
        contact_email=order.email,
        contact_phone=data.get('contact_phone', ''),
        template=data['template'],
        plan=plan.slug,  # Guardar referencia al plan
        is_active=True,
        setup_completed=True,
        # Límites del plan
        max_pages=plan.max_pages,
        max_services=plan.max_services,
        max_images=plan.max_images,
    )
    
    logger.info(f"[Onboarding] Client creado: {client.slug}")
    
    # =========================================================================
    # 2. CREAR DOMINIO (SUBDOMINIO AUTOMÁTICO)
    # =========================================================================
    
    base_domain = getattr(settings, 'BASE_DOMAIN', 'andesscale.cl')
    subdomain = f"{client.slug}.{base_domain}"
    
    Domain.objects.create(
        client=client,
        domain=subdomain,
        domain_type='subdomain',
        is_primary=True,
        is_active=True,
        is_verified=True,  # Subdominio propio, siempre verificado
    )
    
    logger.info(f"[Onboarding] Domain creado: {subdomain}")
    
    # =========================================================================
    # 3. ACTUALIZAR CLIENT SETTINGS
    # =========================================================================
    
    # El signal debería crear ClientSettings automáticamente
    # Si no existe, crearlo
    try:
        client_settings = client.settings
    except ClientSettings.DoesNotExist:
        client_settings = ClientSettings.objects.create(client=client)
    
    client_settings.primary_color = data.get('primary_color', '#2563eb')
    client_settings.secondary_color = data.get('secondary_color', '#1e40af')
    client_settings.whatsapp_number = data.get('whatsapp_number', '')
    client_settings.contact_email = order.email
    client_settings.contact_phone = data.get('contact_phone', '')
    
    # Logo si se subió
    if data.get('logo'):
        client_settings.logo = data['logo']
    
    client_settings.save()
    
    logger.info(f"[Onboarding] Settings actualizados: {client.slug}")
    
    # =========================================================================
    # 4. CREAR USUARIO (OWNER DEL TENANT)
    # =========================================================================
    
    # Generar username único basado en email
    email = order.email.lower().strip()
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=data.get('company_name', '')[:30],  # Usar nombre de empresa
        is_active=True,
    )
    
    # Establecer contraseña inutilizable (se configura por email)
    user.set_unusable_password()
    user.save()
    
    logger.info(f"[Onboarding] User creado: {user.email}")
    
    # =========================================================================
    # 5. CREAR USER PROFILE
    # =========================================================================
    
    # Generar token para configurar contraseña
    invitation_token = uuid.uuid4()
    
    profile = UserProfile.objects.create(
        user=user,
        client=client,
        role='owner',
        invitation_token=invitation_token,
        invitation_expires_at=timezone.now() + timezone.timedelta(days=7),
    )
    
    logger.info(f"[Onboarding] UserProfile creado: {user.email} -> {client.slug}")
    
    # =========================================================================
    # 6. CREAR CONTENIDO INICIAL
    # =========================================================================
    
    # Sección Hero
    Section.objects.create(
        client=client,
        section_type='hero',
        title=f'Bienvenido a {client.name}',
        subtitle=data.get('tagline', 'Tu empresa de confianza'),
        description=data.get('about_text', 'Configura este texto desde tu panel de administración.'),
        order=0,
        is_active=True,
    )
    
    # Sección About (si hay descripción)
    if data.get('about_text'):
        Section.objects.create(
            client=client,
            section_type='about',
            title='Sobre Nosotros',
            description=data['about_text'],
            order=1,
            is_active=True,
        )
    
    # Sección Contact
    Section.objects.create(
        client=client,
        section_type='contact',
        title='Contáctanos',
        subtitle='Estamos aquí para ayudarte',
        order=10,
        is_active=True,
    )
    
    logger.info(f"[Onboarding] Secciones creadas para: {client.slug}")
    
    # =========================================================================
    # 7. MARCAR ORDEN COMO COMPLETADA
    # =========================================================================
    
    order.mark_as_completed(client)
    
    logger.info(f"[Onboarding] Orden completada: {order.order_number}")
    
    # =========================================================================
    # 8. TODO: ENVIAR EMAILS
    # =========================================================================
    
    # TODO Card A6: Enviar email de bienvenida
    # send_welcome_email(client, user, profile.invitation_token)
    
    # TODO Card A6: Enviar email para configurar contraseña
    # send_set_password_email(user, profile.invitation_token)
    
    return client, user
