import logging

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.accounts.decorators import tenant_permission_required
from apps.core.tenant_objects import tenant_object_or_404
from apps.tenants.modules import ModuleLimitReached, check_limit, limit_for, module_required

from ..forms import GalleryItemForm
from ..models import GalleryItem, Section, Service
from ._shared import _image_upload_ok

logger = logging.getLogger(__name__)

# ============================================================
# DASHBOARD - GALERÍA
# ============================================================

def _gallery_item_redirect_url(item):
    """URL (resuelta, usable en redirect() y en templates) a la que volver
    tras editar/eliminar/togglear un GalleryItem, según su dueño
    (#DEUDA-02: reemplaza el switch sobre gallery_type)."""
    if item.role == 'hero':
        return reverse('dashboard_portada')
    if item.service_id:
        return reverse('edit_service_dashboard', kwargs={'service_id': item.service_id})
    return reverse('dashboard_gallery')


@tenant_permission_required('view_dashboard')
@module_required('gallery')
def dashboard_gallery(request):
    """
    Vista de galería de imágenes del sitio.
    Solo gestiona la Section 'gallery' — portada tiene su propia vista.
    """
    client = request.client

    gallery_section, _ = Section.objects.get_or_create(
        client=client,
        section_type='gallery',
        defaults={'title': '', 'subtitle': '', 'description': '', 'order': 0}
    )

    gallery_items = list(
        GalleryItem.objects.filter(
            client=client,
            section=gallery_section,
        ).order_by('order', 'created_at')
    )

    gallery_limit = limit_for(client, 'gallery')

    context = {
        'client':           client,
        'gallery_items':    gallery_items,
        'gallery_limit':    gallery_limit,
        'gallery_at_limit': len(gallery_items) >= gallery_limit,
        'gallery_used':     len(gallery_items),
        'form':             GalleryItemForm(),
    }
    return render(request, 'dashboard/gallery.html', context)
 
 
@tenant_permission_required('edit_content')
@module_required('gallery')
def gallery_item_add(request):
    """
    Subir nueva imagen. Maneja image manualmente via Cloudinary —
    GalleryItemForm excluye image para evitar conflicto con CloudinaryField.
    """
    client = request.client
    settings = client.settings

    if request.method != 'POST':
        return redirect('dashboard_portada')

    service_id = request.POST.get('service_id')
    owner_kwargs = {}
    is_hero = False

    if service_id:
        service = tenant_object_or_404(request, Service, id=service_id)
        owner_kwargs = {'service': service}
        count = GalleryItem.objects.filter(client=client, service=service).count()
        redirect_url = reverse('edit_service_dashboard', kwargs={'service_id': service.id})
        tipo = f'galería de "{service.name}"'
    else:
        gallery_type = request.POST.get('gallery_type', 'gallery')
        if gallery_type not in ('hero', 'gallery'):
            gallery_type = 'gallery'
        section, _ = Section.objects.get_or_create(
            client=client,
            section_type=gallery_type,
            defaults={'title': '', 'subtitle': '', 'description': '', 'order': 0,
                      'slot_key': 'hero' if gallery_type == 'hero' else 'empty'}
        )
        owner_kwargs = {'section': section}

        is_hero = gallery_type == 'hero'
        if is_hero:
            count = GalleryItem.objects.filter(
                client=client, section=section, is_default=False
            ).count()
            limit = settings.hero_images_limit
            redirect_url = 'dashboard_portada'
        else:
            count = GalleryItem.objects.filter(
                client=client, section=section
            ).count()
            redirect_url = 'dashboard_gallery'
        tipo = 'portada' if gallery_type == 'hero' else 'galería'

    if is_hero:
        if count >= limit:
            messages.error(request, f'Has alcanzado el límite de {limit} imágenes de {tipo}.')
            return redirect(redirect_url)
    else:
        try:
            check_limit(client, 'gallery', usage=count)
        except ModuleLimitReached as exc:
            messages.error(request, exc.message)
            return redirect(redirect_url)

    # Verificar que viene imagen
    if 'image' not in request.FILES:
        messages.error(request, 'Selecciona una imagen para subir.')
        return redirect(redirect_url)

    if not _image_upload_ok(request, request.FILES['image']):
        return redirect(redirect_url)

    # Subir a Cloudinary directamente
    try:
        import cloudinary.uploader
        folder = f"{client.slug}/gallery"
        result = cloudinary.uploader.upload(
            request.FILES['image'],
            folder=folder,
            resource_type='image',
            transformation=[{
                'width': 2000,
                'crop': 'limit',
                'fetch_format': 'auto',
                'quality': 'auto',
            }],
        )
        public_id = result['public_id']
    except Exception as e:
        logger.error(f"[Gallery] Error subiendo imagen a Cloudinary: {e}")
        messages.error(request, 'Error al subir la imagen. Intenta nuevamente.')
        return redirect(redirect_url)

    # Crear el item directamente sin pasar por GalleryItemForm
    GalleryItem.objects.create(
        client=client,
        image=public_id,
        title=request.POST.get('title', '').strip(),
        caption=request.POST.get('caption', '').strip(),
        cta_text=request.POST.get('cta_text', '').strip(),
        cta_url=request.POST.get('cta_url', '').strip(),
        is_default=False,
        is_active=True,
        **owner_kwargs,
    )

    messages.success(request, f'Imagen agregada a {tipo}.')
    return redirect(redirect_url)
 
 
@tenant_permission_required('edit_content')
@module_required('gallery')
def gallery_item_edit(request, item_id):
    client = request.client
    item = tenant_object_or_404(request, GalleryItem, id=item_id)
    redirect_url = _gallery_item_redirect_url(item)

    if request.method == 'POST':
        item.title   = request.POST.get('title', '').strip()
        item.caption = request.POST.get('caption', '').strip()
        item.cta_text = request.POST.get('cta_text', '').strip()
        item.cta_url  = request.POST.get('cta_url', '').strip()
        try:
            item.order = int(request.POST.get('order', item.order))
        except ValueError:
            pass

        # Reemplazo de imagen — solo si viene archivo nuevo y es válido
        if 'image' in request.FILES and _image_upload_ok(request, request.FILES['image']):
            try:
                import cloudinary.uploader
                # Eliminar imagen anterior
                if item.image:
                    try:
                        cloudinary.uploader.destroy(str(item.image))
                    except Exception:
                        pass
                folder = f"{client.slug}/gallery"
                result = cloudinary.uploader.upload(
                    request.FILES['image'],
                    folder=folder,
                    resource_type='image',
                    transformation=[{
                        'width': 2000, 'crop': 'limit',
                        'fetch_format': 'auto', 'quality': 'auto',
                    }],
                )
                item.image = result['public_id']
            except Exception as e:
                logger.error(f"[Gallery] Error reemplazando imagen: {e}")
                messages.error(request, 'Error al subir la imagen. Los demás cambios sí fueron guardados.')

        item.save()
        messages.success(request, 'Imagen actualizada correctamente.')
        return redirect(redirect_url)

    context = {
        'client': client,
        'item': item,
        'back_url': redirect_url,
    }
    return render(request, 'dashboard/gallery_item_edit.html', context)
 
 
@tenant_permission_required('delete_content')
@module_required('gallery')
def gallery_item_delete(request, item_id):
    """
    Eliminar ítem. Protege imágenes default contra eliminación.
    """
    item = tenant_object_or_404(request, GalleryItem, id=item_id)

    if item.is_default:
        messages.error(request, 'La imagen por defecto no puede eliminarse.')
        return redirect('dashboard_gallery')
 
    if request.method == 'POST':
        redirect_url = _gallery_item_redirect_url(item)
        item.delete()
        messages.success(request, 'Imagen eliminada.')
        return redirect(redirect_url)

    return redirect('dashboard_gallery')
 
 
@tenant_permission_required('edit_content')
@module_required('gallery')
def gallery_item_toggle(request, item_id):
    """
    Activar/desactivar ítem.
    """
    item = tenant_object_or_404(request, GalleryItem, id=item_id)

    if request.method == 'POST':
        item.is_active = not item.is_active
        item.save(update_fields=['is_active', 'updated_at'])
        estado = 'visible' if item.is_active else 'oculta'
        messages.success(request, f'Imagen marcada como {estado}.')

    return redirect(_gallery_item_redirect_url(item))
 
