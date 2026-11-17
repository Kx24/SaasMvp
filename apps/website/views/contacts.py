import logging

from django.contrib import messages
from django.shortcuts import redirect

from apps.accounts.decorators import tenant_permission_required
from apps.core.template_resolver import render_tenant_template
from apps.core.tenant_objects import tenant_object_or_404

from ..models import ContactSubmission, exclude_blocked

logger = logging.getLogger(__name__)




# ============================================================
# DASHBOARD - CONTACTOS
# ============================================================

@tenant_permission_required('view_contacts')
def dashboard_contacts(request):
    """Lista de mensajes de contacto"""
    contacts = exclude_blocked(
        ContactSubmission.objects.filter(client=request.client, is_spam=False),
        request.client,
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


@tenant_permission_required('manage_contacts')
def mark_contact_read(request, contact_id):
    """Marcar contacto como leído"""
    if request.method == 'POST':
        contact = tenant_object_or_404(request, ContactSubmission, id=contact_id)
        contact.mark_as_read()
        messages.success(request, 'Contacto marcado como leído')
    
    return redirect('dashboard_contacts')


@tenant_permission_required('manage_contacts')
def mark_contact_replied(request, contact_id):
    """Marcar contacto como respondido"""
    if request.method == 'POST':
        contact = tenant_object_or_404(request, ContactSubmission, id=contact_id)
        contact.mark_as_replied()
        messages.success(request, 'Contacto marcado como respondido')
    
    return redirect('dashboard_contacts')
