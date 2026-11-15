import logging

from django.contrib import messages
from django.shortcuts import redirect

from apps.accounts.decorators import tenant_member_required
from apps.core.template_resolver import render_tenant_template
from apps.core.tenant_objects import tenant_object_or_404

from ..forms import SectionForm
from ..models import Section, Service
from ._shared import _image_upload_ok

logger = logging.getLogger(__name__)

# ============================================================
# DASHBOARD - SECCIONES
# ============================================================

@tenant_member_required
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


@tenant_member_required
def edit_section_dashboard(request, section_id):
    """
    Editar una sección desde el dashboard
    """
    section = tenant_object_or_404(request, Section, id=section_id)

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
            elif 'image' in request.FILES and _image_upload_ok(request, request.FILES['image']):
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
