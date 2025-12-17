"""
Views para la aplicación website
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from .models import Section, Service, Testimonial, ContactSubmission
from .forms import SectionForm, ServiceForm, TestimonialForm, ContactForm


def home(request):
    """
    Vista principal del sitio público.
    Muestra el home page con todas las secciones.
    """
    from .forms import ContactForm  # Importar aquí si no está arriba
    
    context = {
        'client': request.client if hasattr(request, 'client') else None,
        'form': ContactForm(),  # Agregar form vacío
    }
    return render(request, 'landing/home.html', context)


# ============================================================
# EDICIÓN DE SECCIONES
# ============================================================

@login_required
def edit_section(request, section_id):
    """
    Editar una sección existente con HTMX.
    Devuelve el modal de edición (GET) o el contenido actualizado (POST).
    """
    section = get_object_or_404(Section, id=section_id, client=request.client)
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            
            # Si es petición HTMX, devolver el contenido actualizado
            if request.headers.get('HX-Request'):
                return render(request, 'partials/section_display.html', {
                    'section': section,
                    'can_edit': True
                })
            
            messages.success(request, 'Sección actualizada correctamente')
            return redirect('home')
    else:
        form = SectionForm(instance=section)
    
    # Devolver el modal de edición
    return render(request, 'partials/section_edit.html', {
        'form': form,
        'section': section
    })


@login_required
def cancel_edit_section(request, section_id):
    """
    Cancelar edición y devolver la vista normal de la sección.
    """
    section = get_object_or_404(Section, id=section_id, client=request.client)
    return render(request, 'partials/section_display.html', {
        'section': section,
        'can_edit': True
    })


# ============================================================
# EDICIÓN DE SERVICIOS
# ============================================================

@login_required
def edit_service(request, service_id):
    """
    Editar un servicio existente con HTMX.
    """
    service = get_object_or_404(Service, id=service_id, client=request.client)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            
            # Si es HTMX, devolver la card actualizada
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


@login_required
def add_service(request):
    """
    Agregar un nuevo servicio.
    """
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.client = request.client
            service.save()
            
            # Si es HTMX, devolver la nueva card
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


@login_required
def delete_service(request, service_id):
    """
    Eliminar un servicio.
    """
    service = get_object_or_404(Service, id=service_id, client=request.client)
    
    if request.method == 'POST':
        service.delete()
        
        # Si es HTMX, devolver respuesta vacía
        if request.headers.get('HX-Request'):
            return HttpResponse('')
        
        messages.success(request, 'Servicio eliminado correctamente')
        return redirect('home')
    
    return render(request, 'partials/service_delete_confirm.html', {
        'service': service
    })


@login_required
def cancel_edit_service(request, service_id):
    """
    Cancelar edición de servicio y devolver la card normal.
    """
    service = get_object_or_404(Service, id=service_id, client=request.client)
    return render(request, 'partials/service_card.html', {
        'service': service,
        'can_edit': True
    })


# ============================================================
# LOGIN/LOGOUT
# ============================================================

def login_modal(request):
    """
    Devuelve el modal de login para HTMX.
    """
    return render(request, 'auth/login_modal.html')

"""
Views del dashboard para clientes
"""

@login_required
def dashboard(request):
    """
    Dashboard principal del cliente.
    Vista general con estadísticas y accesos rápidos.
    """
    context = {
        'client': request.client,
        'sections_count': Section.objects.filter(client=request.client).count(),
        'services_count': Service.objects.filter(client=request.client).count(),
        'testimonials_count': Testimonial.objects.filter(client=request.client).count(),
        'contacts_count': ContactSubmission.objects.filter(client=request.client).count(),
        'new_contacts': ContactSubmission.objects.filter(
            client=request.client,
            status='new'
        ).count(),
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def dashboard_sections(request):
    """
    Lista de todas las secciones del cliente.
    """
    sections = Section.objects.filter(
        client=request.client
    ).order_by('section_type', 'order')
    
    context = {
        'client': request.client,
        'sections': sections,
    }
    return render(request, 'dashboard/sections.html', context)


@login_required
def dashboard_services(request):
    """
    Lista de todos los servicios del cliente.
    """
    services = Service.objects.filter(
        client=request.client
    ).order_by('order', 'name')
    
    context = {
        'client': request.client,
        'services': services,
    }
    return render(request, 'dashboard/services.html', context)


@login_required
def dashboard_testimonials(request):
    """
    Lista de todos los testimonios del cliente.
    """
    testimonials = Testimonial.objects.filter(
        client=request.client
    ).order_by('-created_at')
    
    context = {
        'client': request.client,
        'testimonials': testimonials,
    }
    return render(request, 'dashboard/testimonials.html', context)


@login_required
def dashboard_contacts(request):
    """
    Lista de mensajes de contacto recibidos.
    """
    contacts = ContactSubmission.objects.filter(
        client=request.client
    ).order_by('-created_at')
    
    # Filtros opcionales
    status_filter = request.GET.get('status')
    if status_filter:
        contacts = contacts.filter(status=status_filter)
    
    context = {
        'client': request.client,
        'contacts': contacts,
        'status_filter': status_filter,
    }
    return render(request, 'dashboard/contacts.html', context)


@login_required
def mark_contact_read(request, contact_id):
    """
    Marcar un contacto como leído.
    """
    if request.method == 'POST':
        contact = ContactSubmission.objects.get(
            id=contact_id,
            client=request.client
        )
        contact.mark_as_read()
        messages.success(request, 'Contacto marcado como leído')
    
    return redirect('dashboard_contacts')


@login_required
def mark_contact_replied(request, contact_id):
    """
    Marcar un contacto como respondido.
    """
    if request.method == 'POST':
        contact = ContactSubmission.objects.get(
            id=contact_id,
            client=request.client
        )
        contact.mark_as_replied()
        messages.success(request, 'Contacto marcado como respondido')
    
    return redirect('dashboard_contacts')



"""
View para procesar el formulario de contacto
AGREGAR al final de apps/website/views.py
"""

# ============================================================
# FORMULARIO DE CONTACTO (Card #10)
# ============================================================

def contact_submit(request):
    """
    Procesa el formulario de contacto con HTMX.
    Guarda en la base de datos y devuelve mensaje de éxito/error.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        
        if form.is_valid():
            # Guardar el contacto
            contact = form.save(commit=False)
            contact.client = request.client
            
            # Guardar IP y User Agent
            contact.ip_address = get_client_ip(request)
            contact.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            contact.save()
            
            # Si es petición HTMX, devolver mensaje de éxito
            if request.headers.get('HX-Request'):
                return render(request, 'partials/contact_success.html', {
                    'contact': contact
                })
            
            messages.success(request, '¡Mensaje enviado correctamente! Te contactaremos pronto.')
            return redirect('home')
        else:
            # Si hay errores, devolver formulario con errores
            if request.headers.get('HX-Request'):
                return render(request, 'partials/contact_form.html', {
                    'form': form
                })
            
            messages.error(request, 'Por favor corrige los errores en el formulario.')
            return render(request, 'landing/home.html', {'form': form})
    
    # GET request
    form = ContactForm()
    return render(request, 'partials/contact_form.html', {'form': form})


def get_client_ip(request):
    """Helper para obtener la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
