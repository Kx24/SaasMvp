import json
import logging

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect

from apps.accounts.decorators import tenant_permission_required
from apps.core.template_resolver import render_tenant_template
from apps.core.tenant_objects import tenant_object_or_404

from ..forms import ServiceForm
from ..models import GalleryItem, Service
from ._shared import _image_upload_ok

logger = logging.getLogger(__name__)

# ============================================================
# DASHBOARD - SERVICIOS
# ============================================================

@tenant_permission_required('edit_content')
def create_service_dashboard(request):
    """Crear servicio desde dashboard"""
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.client = request.client

            # --- Subir imagen manualmente ---
            if 'image' in request.FILES and _image_upload_ok(request, request.FILES['image']):
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


@tenant_permission_required('edit_content')
def edit_service_dashboard(request, service_id):
    """Editar servicio desde dashboard"""
    service = tenant_object_or_404(request, Service, id=service_id)

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
            elif 'image' in request.FILES and _image_upload_ok(request, request.FILES['image']):
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

    settings = getattr(request.client, 'settings', None)
    gallery_enabled = bool(settings and settings.enable_gallery)
    gallery_items = []
    gallery_limit = 0
    if gallery_enabled:
        gallery_items = list(
            GalleryItem.objects.filter(client=request.client, service=service)
            .order_by('order', 'created_at')
        )
        gallery_limit = settings.gallery_images_limit

    context = {
        'client': request.client,
        'service': service,
        'form': form,
        'gallery_enabled': gallery_enabled,
        'gallery_items': gallery_items,
        'gallery_limit': gallery_limit,
        'gallery_used': len(gallery_items),
        'gallery_at_limit': len(gallery_items) >= gallery_limit if gallery_enabled else False,
    }
    return render_tenant_template(request, 'dashboard/edit_service.html', context)


@tenant_permission_required('delete_content')
def delete_service_dashboard(request, service_id):
    """Eliminar servicio desde dashboard"""
    service = tenant_object_or_404(request, Service, id=service_id)
    
    if request.method == 'POST':
        name = service.name
        service.delete()
        messages.success(request, f'Servicio "{name}" eliminado')
        return redirect('dashboard_sections')
    
    context = {
        'client': request.client,
        'service': service,
    }
    return render_tenant_template(request, 'dashboard/service_confirm_delete.html', context)


@tenant_permission_required('edit_content')
def toggle_service(request, service_id):
    """Activar / desactivar un servicio"""
    service = tenant_object_or_404(request, Service, id=service_id)
    service.is_active = not service.is_active
    service.save(update_fields=['is_active'])

    return JsonResponse({
        'success': True,
        'is_active': service.is_active,
        'message': f'Servicio {"activado" if service.is_active else "desactivado"}'
    })


@tenant_permission_required('edit_content')
def toggle_service_featured(request, service_id):
    """Destacar / quitar destacado de un servicio"""
    service = tenant_object_or_404(request, Service, id=service_id)
    service.is_featured = not service.is_featured
    service.save(update_fields=['is_featured'])

    return JsonResponse({
        'success': True,
        'is_featured': service.is_featured,
        'message': f'Servicio {"destacado" if service.is_featured else "no destacado"}'
    })


@tenant_permission_required('edit_content')
def reorder_services(request):
    """Reordenar servicios (drag & drop)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        order_data = data.get('order', [])

        for item in order_data:
            service = tenant_object_or_404(request, Service, id=item['id'])
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


# =============================================================================
# ALIAS PARA COMPATIBILIDAD CON urls.py
# =============================================================================
create_service = create_service_dashboard
toggle_service_active = toggle_service
