"""
Views para la aplicación website
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from .models import Section, Service, Testimonial
from .forms import SectionForm, ServiceForm, TestimonialForm


def home(request):
    """
    Vista principal del sitio público.
    Muestra el home page con todas las secciones.
    """
    context = {
        'client': request.client if hasattr(request, 'client') else None,
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