"""
Views para la aplicación website
================================
LIMPIO - Sin duplicados, con EmailDispatcher integrado
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from .models import Section, Service, Testimonial, ContactSubmission
from .forms import SectionForm, ServiceForm, ContactForm
import logging
import json

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

def get_client_ip(request):
    """Obtiene la IP real del cliente considerando proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip[:45] if ip else None


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def home(request):
    """
    Página principal con secciones y servicios
    """
    # Obtener secciones (hero, about, contact)
    sections = Section.objects.filter(
        client=request.client,
        is_active=True
    ).exclude(section_type='service')
    
    # Obtener servicios del modelo Service
    services = Service.objects.filter(
        client=request.client,
        is_active=True
    ).order_by('order')
    
    # Organizar secciones por tipo
    sections_dict = {s.section_type: s for s in sections}
    
    context = {
        'client': request.client,
        'hero': sections_dict.get('hero'),
        'about': sections_dict.get('about'),
        'contact_section': sections_dict.get('contact'),
        'services': services,
        'form': ContactForm(),
    }
    return render(request, 'landing/home.html', context)


# ============================================================
# FORMULARIO DE CONTACTO PÚBLICO
# ============================================================

def contact_submit(request):
    """
    Procesar formulario de contacto público.
    
    Flujo:
    1. Crear ContactSubmission en DB (siempre)
    2. Llamar a EmailDispatcher según configuración del tenant
    3. Retornar respuesta al usuario
    """
    if request.method != 'POST':
        return redirect('home')
    
    # Verificar que hay un cliente asociado
    if not hasattr(request, 'client') or not request.client:
        messages.error(request, 'Error de configuración. Intenta más tarde.')
        return redirect('home')
    
    # 1. Crear registro en base de datos (SIEMPRE)
    contact = ContactSubmission.objects.create(
        client=request.client,
        name=request.POST.get('name', '').strip(),
        email=request.POST.get('email', '').strip(),
        phone=request.POST.get('phone', '').strip(),
        company=request.POST.get('company', '').strip(),
        subject=request.POST.get('subject', '').strip(),
        message=request.POST.get('message', '').strip(),
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )
    
    logger.info(
        f"[Contact] New submission #{contact.id} for {request.client.slug} "
        f"from {contact.email}"
    )
    
    # 2. Dispatch de notificación según configuración
    try:
        from apps.tenants.services.email_dispatcher import EmailDispatcher
        dispatcher = EmailDispatcher(request.client)
        result = dispatcher.send_contact_notification(contact)
        
        logger.info(
            f"[Contact] Dispatch result for #{contact.id}: "
            f"{result.status.value} (email_sent={result.email_sent})"
        )
        
    except Exception as e:
        logger.error(f"[Contact] Dispatch error for #{contact.id}: {e}", exc_info=True)
    
    # 3. Respuesta al usuario
    messages.success(
        request, 
        '¡Gracias por contactarnos! Te responderemos pronto.'
    )
    
    # Si es HTMX, retornar partial
    if request.headers.get('HX-Request'):
        return render(request, 'partials/contact_success.html', {
            'contact': contact
        })
    
    return redirect('home')


# ============================================================
# LOGIN MODAL (HTMX)
# ============================================================

def login_modal(request):
    """Devuelve el modal de login para HTMX."""
    return render(request, 'auth/login_modal.html')


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================

@login_required(login_url='/auth/login/')
def dashboard(request):
    """
    Dashboard principal del cliente.
    """
    services_count = Service.objects.filter(client=request.client).count()
    
    recent_contacts = ContactSubmission.objects.filter(
        client=request.client,
        status='new'
    ).order_by('-created_at')[:5]
    
    context = {
        'client': request.client,
        'sections_count': Section.objects.filter(client=request.client).count(),
        'services_count': services_count,
        'contacts_count': ContactSubmission.objects.filter(client=request.client).count(),
        'new_contacts': ContactSubmission.objects.filter(
            client=request.client,
            status='new'
        ).count(),
        'recent_contacts': recent_contacts,
    }
    return render(request, 'dashboard/index.html', context)


# ============================================================
# DASHBOARD - SECCIONES
# ============================================================

@login_required(login_url='/auth/login/')
def dashboard_sections(request):
    """
    Lista de secciones editables (hero, about, contact) + servicios
    """
    sections = Section.objects.filter(
        client=request.client
    ).exclude(section_type='service').order_by('order')
    
    services = Service.objects.filter(
        client=request.client
    ).order_by('order')
    
    context = {
        'client': request.client,
        'sections': sections,
        'services': services,
    }
    return render(request, 'dashboard/sections.html', context)


@login_required(login_url='/auth/login/')
def edit_section_dashboard(request, section_id):
    """
    Editar una sección desde el dashboard
    """
    section = get_object_or_404(Section, id=section_id, client=request.client)

    if request.method == 'POST':
        form = SectionForm(request.POST, request.FILES, instance=section)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Sección "{section.get_section_type_display()}" actualizada correctamente'
            )
            return redirect('dashboard_sections')
    else:
        form = SectionForm(instance=section)

    return render(request, 'dashboard/edit_section.html', {
        'client': request.client,
        'section': section,
        'form': form,
    })


# ============================================================
# DASHBOARD - SERVICIOS CRUD
# ============================================================

@login_required(login_url='/auth/login/')
def create_service(request):
    """Crear un nuevo servicio"""
    if request.method == 'POST':
        service = Service.objects.create(
            client=request.client,
            name=request.POST.get('title', ''),
            description=request.POST.get('description', ''),
            icon=request.POST.get('icon', '⚡'),
            price_text=request.POST.get('price_text', ''),
            is_active=request.POST.get('is_active') == 'on',
        )
        
        if request.FILES.get('image'):
            service.image = request.FILES['image']
            service.save()
        
        messages.success(request, f'Servicio "{service.name}" creado correctamente')
        return redirect('dashboard_sections')
    
    context = {
        'client': request.client,
        'action': 'Crear',
    }
    return render(request, 'dashboard/service_form.html', context)


@login_required(login_url='/auth/login/')
def edit_service_dashboard(request, service_id):
    """Editar un servicio existente"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    
    if request.method == 'POST':
        service.name = request.POST.get('title', service.name)
        service.description = request.POST.get('description', '')
        service.icon = request.POST.get('icon', '⚡')
        service.price_text = request.POST.get('price_text', '')
        service.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('image'):
            service.image = request.FILES['image']
        
        service.save()
        messages.success(request, f'Servicio "{service.name}" actualizado correctamente')
        return redirect('dashboard_sections')
    
    context = {
        'client': request.client,
        'service': service,
        'action': 'Editar',
    }
    return render(request, 'dashboard/service_form.html', context)


@login_required(login_url='/auth/login/')
def delete_service_dashboard(request, service_id):
    """Eliminar un servicio"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    
    if request.method == 'POST':
        service_name = service.name
        service.delete()
        messages.success(request, f'Servicio "{service_name}" eliminado correctamente')
        return redirect('dashboard_sections')
    
    context = {
        'client': request.client,
        'service': service,
    }
    return render(request, 'dashboard/service_confirm_delete.html', context)


# ============================================================
# SERVICIOS - AJAX
# ============================================================

@login_required(login_url='/auth/login/')
def toggle_service_active(request, service_id):
    """Activar / desactivar un servicio"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    service.is_active = not service.is_active
    service.save(update_fields=['is_active'])

    return JsonResponse({
        'success': True,
        'is_active': service.is_active,
        'message': f'Servicio {"activado" if service.is_active else "desactivado"}'
    })


@login_required(login_url='/auth/login/')
def toggle_service_featured(request, service_id):
    """Destacar / quitar destacado de un servicio"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    service.is_featured = not service.is_featured
    service.save(update_fields=['is_featured'])

    return JsonResponse({
        'success': True,
        'is_featured': service.is_featured,
        'message': f'Servicio {"destacado" if service.is_featured else "no destacado"}'
    })


@login_required(login_url='/auth/login/')
def reorder_services(request):
    """Reordenar servicios (drag & drop)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        order_data = data.get('order', [])

        for item in order_data:
            service = get_object_or_404(
                Service,
                id=item['id'],
                client=request.client
            )
            service.order = item['order']
            service.save(update_fields=['order'])

        return JsonResponse({
            'success': True,
            'message': 'Orden actualizado'
        })

    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    })


# ============================================================
# EDICIÓN INLINE (HTMX)
# ============================================================

@login_required(login_url='/auth/login/')
def edit_section(request, section_id):
    """Editar sección con HTMX"""
    section = get_object_or_404(Section, id=section_id, client=request.client)
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            
            if request.headers.get('HX-Request'):
                return render(request, 'partials/section_display.html', {
                    'section': section,
                    'can_edit': True
                })
            
            messages.success(request, 'Sección actualizada correctamente')
            return redirect('home')
    else:
        form = SectionForm(instance=section)
    
    return render(request, 'partials/section_edit.html', {
        'form': form,
        'section': section
    })


@login_required(login_url='/auth/login/')
def cancel_edit_section(request, section_id):
    """Cancelar edición de sección"""
    section = get_object_or_404(Section, id=section_id, client=request.client)
    return render(request, 'partials/section_display.html', {
        'section': section,
        'can_edit': True
    })


@login_required(login_url='/auth/login/')
def edit_service(request, service_id):
    """Editar servicio con HTMX"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            
            if request.headers.get('HX-Request'):
                return render(request, 'partials/service_card.html', {
                    'service': service,
                    'can_edit': True
                })
            
            messages.success(request, 'Servicio actualizado correctamente')
            return redirect('home')
    else:
        form = ServiceForm(instance=service)
    
    return render(request, 'partials/service_edit.html', {
        'form': form,
        'service': service
    })


@login_required(login_url='/auth/login/')
def add_service(request):
    """Agregar servicio con HTMX"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.client = request.client
            service.save()
            
            if request.headers.get('HX-Request'):
                return render(request, 'partials/service_card.html', {
                    'service': service,
                    'can_edit': True
                })
            
            messages.success(request, 'Servicio creado correctamente')
            return redirect('home')
    else:
        form = ServiceForm()
    
    return render(request, 'partials/service_add.html', {
        'form': form
    })


@login_required(login_url='/auth/login/')
def delete_service(request, service_id):
    """Eliminar servicio con HTMX"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    
    if request.method == 'POST':
        service.delete()
        
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        
        messages.success(request, 'Servicio eliminado correctamente')
        return redirect('home')
    
    return render(request, 'partials/service_delete_confirm.html', {
        'service': service
    })


@login_required(login_url='/auth/login/')
def cancel_edit_service(request, service_id):
    """Cancelar edición de servicio"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    return render(request, 'partials/service_card.html', {
        'service': service,
        'can_edit': True
    })


# ============================================================
# DASHBOARD - TESTIMONIOS
# ============================================================

@login_required(login_url='/auth/login/')
def dashboard_testimonials(request):
    """Lista de testimonios"""
    testimonials = Testimonial.objects.filter(
        client=request.client
    ).order_by('-created_at')
    
    context = {
        'client': request.client,
        'testimonials': testimonials,
    }
    return render(request, 'dashboard/testimonials.html', context)


# ============================================================
# DASHBOARD - CONTACTOS
# ============================================================

@login_required(login_url='/auth/login/')
def dashboard_contacts(request):
    """Lista de mensajes de contacto"""
    contacts = ContactSubmission.objects.filter(
        client=request.client
    ).order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        contacts = contacts.filter(status=status_filter)
    
    context = {
        'client': request.client,
        'contacts': contacts,
        'status_filter': status_filter,
    }
    return render(request, 'dashboard/contacts.html', context)


@login_required(login_url='/auth/login/')
def mark_contact_read(request, contact_id):
    """Marcar contacto como leído"""
    if request.method == 'POST':
        contact = get_object_or_404(
            ContactSubmission,
            id=contact_id,
            client=request.client
        )
        contact.mark_as_read()
        messages.success(request, 'Contacto marcado como leído')
    
    return redirect('dashboard_contacts')


@login_required(login_url='/auth/login/')
def mark_contact_replied(request, contact_id):
    """Marcar contacto como respondido"""
    if request.method == 'POST':
        contact = get_object_or_404(
            ContactSubmission,
            id=contact_id,
            client=request.client
        )
        contact.mark_as_replied()
        messages.success(request, 'Contacto marcado como respondido')
    
    return redirect('dashboard_contacts')