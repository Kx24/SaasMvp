# =============================================================================
# apps/website/views.py — SECCIÓN REEMPLAZADA: contact_submit
# =============================================================================
# INSTRUCCIONES DE INTEGRACIÓN:
#
#   Reemplaza SOLO la función contact_submit en tu views.py actual.
#   El resto del archivo (home, dashboard, edición inline, etc.) NO cambia.
#
#   Además agrega estas dos líneas al bloque de imports del archivo:
#
#       from apps.core.rate_limit import RateLimiter
#       from django.http import JsonResponse   ← ya existe en tu views.py
#
# =============================================================================
#
# CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
#
#   1. Usa ContactForm (forms.Form) en lugar de raw request.POST
#   2. Honeypot: si website != '' → guarda con is_spam=True, responde 200 OK
#   3. Rate limit: 3 envíos / 10 min por IP+tenant → responde JSON 429
#   4. form_source: se asigna desde el form validado al modelo
#   5. subject: se genera automáticamente desde get_subject_by_intent()
#   6. Responde JSON para el fetch() del multi-step (Card #55b)
#      y mantiene compatibilidad HTMX para los formularios actuales
#
# =============================================================================

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views import View
from .models import Section, Service, ContactSubmission
from .forms import SectionForm, ServiceForm, ContactForm
from apps.tenants.forms import BrandingForm
from apps.tenants.models import ClientSettings
import json
from django.utils import timezone
from apps.core.template_resolver import get_tenant_template, render_tenant_template
from apps.core.rate_limit import RateLimiter
 
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
    Página principal con secciones y servicios.
    Usa template específico del tenant según su slug.
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
    
    # ✅ Usar template del tenant
    return render_tenant_template(request, 'landing/home.html', context)


# ============================================================
# FORMULARIO DE CONTACTO PÚBLICO — REESCRITO
# ============================================================
 
def contact_submit(request):
    """
    Procesa el formulario de contacto público.
 
    Flujo:
        1. Solo acepta POST
        2. Rate limit: 3 intentos / 10 min por IP+tenant
        3. Valida con ContactForm
        4. Honeypot: si fue activado → guarda como spam silenciosamente
        5. Crea ContactSubmission con todos los campos mapeados
        6. Dispatch de notificación (email / dashboard según config del tenant)
        7. Responde JSON (para fetch() del multi-step) o HTMX partial
 
    Respuestas JSON:
        200 { "ok": true,  "message": "..." }
        400 { "ok": false, "errors": {...} }
        429 { "ok": false, "message": "..." }  ← rate limit
    """
    if request.method != 'POST':
        return redirect('home')
 
    if not hasattr(request, 'client') or not request.client:
        return JsonResponse(
            {'ok': False, 'message': 'Error de configuración. Intenta más tarde.'},
            status=500
        )
 
    # ------------------------------------------------------------------
    # 1. RATE LIMITING
    # ------------------------------------------------------------------
    limiter = RateLimiter(request, scope='contact', limit=3, period=600)
 
    if limiter.is_exceeded():
        logger.warning(
            f"[Contact] Rate limit exceeded for {get_client_ip(request)} "
            f"on tenant {request.client.slug}"
        )
        return JsonResponse(
            {
                'ok': False,
                'message': 'Demasiados intentos. Por favor espera unos minutos antes de reintentar.',
            },
            status=429
        )
 
    # ------------------------------------------------------------------
    # 2. VALIDACIÓN DEL FORM
    # ------------------------------------------------------------------
    form = ContactForm(request.POST)
 
    if not form.is_valid():
        return JsonResponse(
            {
                'ok': False,
                'errors': form.errors,
                'message': 'Por favor revisa los campos marcados.',
            },
            status=400
        )
 
    # ------------------------------------------------------------------
    # 3. HONEYPOT CHECK
    # ------------------------------------------------------------------
    is_spam = form.is_honeypot_triggered()
 
    if is_spam:
        logger.info(
            f"[Contact] Honeypot triggered from {get_client_ip(request)} "
            f"on tenant {request.client.slug} — saving silently as spam"
        )
 
    # ------------------------------------------------------------------
    # 4. CREAR REGISTRO
    # ------------------------------------------------------------------
    cleaned = form.cleaned_data
 
    contact = ContactSubmission.objects.create(
        client=request.client,
        name=cleaned['name'],
        email=cleaned['email'],
        phone=cleaned.get('phone', ''),
        company=cleaned.get('company', ''),
        subject=form.get_subject_by_intent(),
        message=cleaned['message'],
        # Nuevos campos del Card #55a:
        form_source=cleaned.get('form_source', 'page'),
        is_spam=is_spam,
        # Campos existentes:
        source='website',
        status='spam' if is_spam else 'new',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )
 
    logger.info(
        f"[Contact] Submission #{contact.id} for {request.client.slug} "
        f"from {contact.email} | source={contact.form_source} "
        f"| intent={cleaned.get('intent', '?')} | spam={is_spam}"
    )
 
    # ------------------------------------------------------------------
    # 5. INCREMENTAR RATE LIMIT (solo si no es spam — no penalizar al bot)
    # ------------------------------------------------------------------
    if not is_spam:
        limiter.increment()
 
    # ------------------------------------------------------------------
    # 6. DISPATCH DE NOTIFICACIÓN (solo si no es spam)
    # ------------------------------------------------------------------
    if not is_spam:
        try:
            from apps.tenants.services.email_dispatcher import EmailDispatcher
            dispatcher = EmailDispatcher(request.client)
            result = dispatcher.send_contact_notification(contact)
            logger.info(
                f"[Contact] Dispatch #{contact.id}: "
                f"{result.status.value} (email_sent={result.email_sent})"
            )
        except Exception as e:
            logger.error(
                f"[Contact] Dispatch error for #{contact.id}: {e}",
                exc_info=True
            )
 
    # ------------------------------------------------------------------
    # 7. RESPUESTA
    # ------------------------------------------------------------------
    success_message = '✅ Listo, te responderemos en menos de 24 horas.'
 
    # JSON — para el fetch() del componente multi-step (Card #55b)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
       request.content_type == 'application/json' or \
       request.headers.get('Accept') == 'application/json':
        return JsonResponse({'ok': True, 'message': success_message})
 
    # HTMX — para los formularios inline existentes
    if request.headers.get('HX-Request'):
        template = get_tenant_template(request, 'components/contact_success.html')
        return render(request, template, {'contact': contact})
 
    # Fallback — redirect clásico
    messages.success(request, success_message)
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
    Vista principal del dashboard.
    """
    client = request.client
    today = timezone.now().date()
    
    # Métricas
    total_contacts = ContactSubmission.objects.filter(client=client).count()
    contacts_today = ContactSubmission.objects.filter(
        client=client,
        created_at__date=today
    ).count()
    
    total_services = Service.objects.filter(client=client, is_active=True).count()
    total_sections = Section.objects.filter(client=client, is_active=True).count()
    
    # Contactos recientes (últimos 5)
    recent_contacts = ContactSubmission.objects.filter(
        client=client
    ).order_by('-created_at')[:5]
    
    context = {
        'client': client,
        'total_contacts': total_contacts,
        'contacts_today': contacts_today,
        'total_services': total_services,
        'total_sections': total_sections,
        'recent_contacts': recent_contacts,
    }
    
    # Dashboard usa template del tenant si existe
    return render_tenant_template(request, 'dashboard/index.html', context)

@login_required(login_url='/auth/login/')
def dashboard_branding(request):
    """
    Vista de personalización: colores, logo, info empresa, redes sociales, SEO.
    """
    client = request.client

    # Obtener o crear settings del cliente
    settings_obj, created = ClientSettings.objects.get_or_create(client=client)

    if request.method == 'POST':
        form = BrandingForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cambios guardados correctamente')
            return redirect('dashboard_branding')
        else:
            messages.error(request, 'Revisa los campos con errores')
    else:
        form = BrandingForm(instance=settings_obj)

    context = {
        'client': client,
        'settings': settings_obj,
        'form': form,
    }
    return render(request, 'dashboard/branding.html', context)

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
    return render_tenant_template(request, 'dashboard/sections.html', context)


@login_required(login_url='/auth/login/')
def edit_section_dashboard(request, section_id):
    """
    Editar una sección desde el dashboard
    """
    section = get_object_or_404(Section, id=section_id, client=request.client)

    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            section = form.save(commit=False)

            # --- Eliminar imagen ---
            if request.POST.get('clear_image') and section.image:
                try:
                    import cloudinary.uploader
                    cloudinary.uploader.destroy(str(section.image))
                except Exception as e:
                    logger.warning(f"[Section] No se pudo eliminar imagen de Cloudinary: {e}")
                section.image = None

            # --- Subir nueva imagen ---
            elif 'image' in request.FILES:
                try:
                    import cloudinary.uploader
                    uploaded_file = request.FILES['image']
                    folder = f"{request.client.slug}/sections"
                    result = cloudinary.uploader.upload(
                        uploaded_file,
                        folder=folder,
                        resource_type="image"
                    )
                    section.image = result['public_id']
                except Exception as e:
                    logger.error(f"[Section] Error subiendo imagen a Cloudinary: {e}")
                    messages.error(request, 'Error al subir la imagen. Los demás cambios sí fueron guardados.')

            section.save()
            messages.success(
                request,
                f'Sección "{section.get_section_type_display()}" actualizada correctamente'
            )
            return redirect('dashboard_sections')
    else:
        form = SectionForm(instance=section)

    context = {
        'client': request.client,
        'section': section,
        'form': form,
    }
    return render_tenant_template(request, 'dashboard/edit_section.html', context)


# ============================================================
# DASHBOARD - SERVICIOS
# ============================================================

@login_required(login_url='/auth/login/')
def dashboard_services(request):
    """Lista de servicios"""
    services = Service.objects.filter(
        client=request.client
    ).order_by('order')
    
    context = {
        'client': request.client,
        'services': services,
    }
    return render_tenant_template(request, 'dashboard/services.html', context)


@login_required(login_url='/auth/login/')
def create_service_dashboard(request):
    """Crear servicio desde dashboard"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.client = request.client

            # --- Subir imagen manualmente ---
            if 'image' in request.FILES:
                try:
                    import cloudinary.uploader
                    uploaded_file = request.FILES['image']
                    folder = f"{request.client.slug}/services"
                    result = cloudinary.uploader.upload(
                        uploaded_file,
                        folder=folder,
                        resource_type="image"
                    )
                    service.image = result['public_id']
                except Exception as e:
                    logger.error(f"[Service] Error subiendo imagen a Cloudinary: {e}")
                    messages.error(request, 'Error al subir la imagen. El servicio fue creado sin imagen.')

            service.save()
            messages.success(request, f'Servicio "{service.name}" creado correctamente')
            return redirect('dashboard_sections')
    else:
        form = ServiceForm()

    context = {
        'client': request.client,
        'form': form,
    }
    return render_tenant_template(request, 'dashboard/edit_service.html', context)


@login_required(login_url='/auth/login/')
def edit_service_dashboard(request, service_id):
    """Editar servicio desde dashboard"""
    service = get_object_or_404(Service, id=service_id, client=request.client)

    if request.method == 'POST':
        # Excluimos 'image' del form para manejarlo manualmente (evita bug con TemporaryUploadedFile en Cloudinary)
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            service = form.save(commit=False)

            # --- Eliminar imagen ---
            if request.POST.get('clear_image') and service.image:
                try:
                    import cloudinary.uploader
                    cloudinary.uploader.destroy(str(service.image))
                except Exception as e:
                    logger.warning(f"[Service] No se pudo eliminar imagen de Cloudinary: {e}")
                service.image = None

            # --- Subir nueva imagen ---
            elif 'image' in request.FILES:
                try:
                    import cloudinary.uploader
                    uploaded_file = request.FILES['image']
                    folder = f"{request.client.slug}/services"
                    result = cloudinary.uploader.upload(
                        uploaded_file,
                        folder=folder,
                        resource_type="image"
                    )
                    service.image = result['public_id']
                except Exception as e:
                    logger.error(f"[Service] Error subiendo imagen a Cloudinary: {e}")
                    messages.error(request, 'Error al subir la imagen. Los demás cambios sí fueron guardados.')

            service.save()
            messages.success(request, f'Servicio "{service.name}" actualizado correctamente')
            return redirect('dashboard_sections')
    else:
        form = ServiceForm(instance=service)

    context = {
        'client': request.client,
        'service': service,
        'form': form,
    }
    return render_tenant_template(request, 'dashboard/edit_service.html', context)


@login_required(login_url='/auth/login/')
def delete_service_dashboard(request, service_id):
    """Eliminar servicio desde dashboard"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    
    if request.method == 'POST':
        name = service.name
        service.delete()
        messages.success(request, f'Servicio "{name}" eliminado')
        return redirect('dashboard_sections')
    
    context = {
        'client': request.client,
        'service': service,
    }
    return render_tenant_template(request, 'dashboard/delete_service.html', context)


@login_required(login_url='/auth/login/')
def toggle_service(request, service_id):
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
                template = get_tenant_template(request, 'partials/section_display.html')
                return render(request, template, {
                    'section': section,
                    'can_edit': True
                })
            
            messages.success(request, 'Sección actualizada correctamente')
            return redirect('home')
    else:
        form = SectionForm(instance=section)
    
    template = get_tenant_template(request, 'partials/section_edit.html')
    return render(request, template, {
        'form': form,
        'section': section
    })


@login_required(login_url='/auth/login/')
def cancel_edit_section(request, section_id):
    """Cancelar edición de sección"""
    section = get_object_or_404(Section, id=section_id, client=request.client)
    template = get_tenant_template(request, 'partials/section_display.html')
    return render(request, template, {
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
                template = get_tenant_template(request, 'partials/service_card.html')
                return render(request, template, {
                    'service': service,
                    'can_edit': True
                })
            
            messages.success(request, 'Servicio actualizado correctamente')
            return redirect('home')
    else:
        form = ServiceForm(instance=service)
    
    template = get_tenant_template(request, 'partials/service_edit.html')
    return render(request, template, {
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
                template = get_tenant_template(request, 'partials/service_card.html')
                return render(request, template, {
                    'service': service,
                    'can_edit': True
                })
            
            messages.success(request, 'Servicio creado correctamente')
            return redirect('home')
    else:
        form = ServiceForm()
    
    template = get_tenant_template(request, 'partials/service_add.html')
    return render(request, template, {
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
    
    template = get_tenant_template(request, 'partials/service_delete_confirm.html')
    return render(request, template, {
        'service': service
    })


@login_required(login_url='/auth/login/')
def cancel_edit_service(request, service_id):
    """Cancelar edición de servicio"""
    service = get_object_or_404(Service, id=service_id, client=request.client)
    template = get_tenant_template(request, 'partials/service_card.html')
    return render(request, template, {
        'service': service,
        'can_edit': True
    })


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
    return render_tenant_template(request, 'dashboard/contacts.html', context)


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
# =============================================================================
# ALIAS PARA COMPATIBILIDAD CON urls.py
# =============================================================================
create_service = create_service_dashboard
toggle_service_active = toggle_service

# ============================================================
# SEO - Pagekey
# ============================================================
class HomeView(View):
    def get(self, request):
            return render(request, 'themes/default/landing/home.html', {
                'page_key': 'home',   # ← AGREGAR
            })

class ContactView(View):
    def get(self, request):
            return render(request, '...', {
                'page_key': 'contact',  # ← AGREGAR
            })    