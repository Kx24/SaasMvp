import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.accounts.decorators import tenant_permission_required
from apps.accounts.permissions import has_dashboard_permission
from apps.core.template_resolver import render_tenant_template
from apps.tenants.fonts import FONT_CHOICES
from apps.tenants.forms import BrandingForm
from apps.tenants.models import ClientSettings

from ..forms import GalleryItemForm
from ..models import ContactSubmission, DataSubjectRequest, GalleryItem, Section, Service
from ._shared import _image_upload_ok

logger = logging.getLogger(__name__)


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================

@tenant_permission_required('view_dashboard')
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
    # (datos personales de terceros: solo para roles con `view_contacts`)
    if has_dashboard_permission(request.user, client, 'view_contacts'):
        recent_contacts = ContactSubmission.objects.filter(
            client=client
        ).order_by('-created_at')[:5]
    else:
        recent_contacts = []

    # Solicitudes de derechos abiertas (LEY-02): mismo permiso que los contactos
    open_data_requests = 0
    next_data_request_due = None
    if has_dashboard_permission(request.user, client, 'view_contacts'):
        open_qs = DataSubjectRequest.objects.filter(
            client=client, status__in=DataSubjectRequest.OPEN_STATUSES,
        )
        open_data_requests = open_qs.count()
        first = open_qs.order_by('due_at').first()
        next_data_request_due = first.due_at if first else None

    context = {
        'open_data_requests': open_data_requests,
        'next_data_request_due': next_data_request_due,
        'client': client,
        'total_contacts': total_contacts,
        'contacts_today': contacts_today,
        'total_services': total_services,
        'total_sections': total_sections,
        'recent_contacts': recent_contacts,
    }
    
    # Dashboard usa template del tenant si existe
    return render_tenant_template(request, 'dashboard/index.html', context)

@tenant_permission_required('manage_branding')
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
        'font_choices': FONT_CHOICES,
    }
    return render(request, 'dashboard/branding.html', context)


@tenant_permission_required('edit_content')
def dashboard_portada(request):
    """
    Vista de Portada: imagen de fondo del hero default + toggle show_default_hero
    + gestión de imágenes hero del cliente.
    """
    client = request.client
    settings = getattr(client, 'settings', None)

    if not settings or not settings.enable_gallery:
        messages.error(request, 'El módulo de imágenes no está activado.')
        return redirect('dashboard')

    hero_section, _ = Section.objects.get_or_create(
        client=client,
        section_type='hero',
        defaults={'title': '', 'subtitle': '', 'description': '', 'order': 0,
                  'slot_key': 'hero'}
    )

    hero_items = list(
        GalleryItem.objects.filter(
            client=client,
            section=hero_section,
        ).order_by('order', 'created_at')
    )

    hero_limit = settings.hero_images_limit
    hero_used = len(hero_items)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Guardar imagen de fondo + toggle ──
        if action == 'save_hero_config':
            # Toggle show_default_hero
            settings.show_default_hero = 'show_default_hero' in request.POST
            settings.save(update_fields=['show_default_hero'])

            # Imagen de fondo — manejo manual Cloudinary
            if 'background_image' in request.FILES and not _image_upload_ok(
                    request, request.FILES['background_image']):
                return redirect('dashboard_portada')
            if 'background_image' in request.FILES:
                try:
                    import cloudinary.uploader
                    if hero_section.background_image:
                        try:
                            cloudinary.uploader.destroy(str(hero_section.background_image))
                        except Exception:
                            pass
                    result = cloudinary.uploader.upload(
                        request.FILES['background_image'],
                        folder=f"{client.slug}/sections",
                        resource_type='image',
                        transformation=[{
                            'width': 2000, 'crop': 'limit',
                            'fetch_format': 'auto', 'quality': 'auto',
                        }],
                    )
                    hero_section.background_image = result['public_id']
                    hero_section.save(update_fields=['background_image'])
                except Exception as e:
                    logger.error(f"[Portada] Error subiendo background: {e}")
                    messages.error(request, 'Error al subir la imagen de fondo.')
                    return redirect('dashboard_portada')

            messages.success(request, 'Configuración de portada guardada.')
            return redirect('dashboard_portada')

    context = {
        'client': client,
        'settings': settings,
        'hero_section': hero_section,
        'hero_items': hero_items,
        'hero_limit': hero_limit,
        'hero_at_limit': hero_used >= hero_limit,
        'hero_used': hero_used,
        'upload_form': GalleryItemForm(),
    }
    return render(request, 'dashboard/portada.html', context)
