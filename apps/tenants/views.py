# apps/tenants/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import transaction
from .forms import TenantOnboardingForm
from .models import Client, Domain
from apps.website.models import Section
import logging


logger = logging.getLogger(__name__)


# --- VISTA 1: ONBOARDING (Corregida) ---
@user_passes_test(lambda u: u.is_staff)
def onboarding_view(request):
    if request.method == 'POST':
        form = TenantOnboardingForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    data = form.cleaned_data
                    
                    # 1. Crear Cliente
                    client = Client.objects.create(
                        name=data['name'],
                        slug=data['slug'],
                        company_name=data['name'],
                        contact_email=data.get('contact_email', ''),
                        template=data['template'],
                        is_active=True
                    )
                    logger.info(f"✅ Cliente creado: {client.name} (tema: {client.template})")
                    
                    # 2. Crear Dominio
                    Domain.objects.create(
                        client=client,
                        domain=data['domain'],
                        is_primary=True,
                        is_active=True
                    )
                    logger.info(f"✅ Dominio creado: {data['domain']}")
                    
                    # 3. Settings (El signal los crea, solo actualizamos)
                    if hasattr(client, 'settings'):
                        settings = client.settings
                        settings.primary_color = data.get('primary_color', '#0ea5e9')
                        settings.secondary_color = data.get('secondary_color', '#0284c7')
                        settings.whatsapp_number = data.get('whatsapp_number', '')
                        settings.contact_email = data.get('contact_email', '')
                        if data.get('logo'):
                            settings.logo = data['logo']
                        settings.save()
                        logger.info(f"✅ Settings actualizados")
                    
                    # 4. Contenido Dummy
                    Section.objects.create(
                        client=client,
                        section_type='hero',
                        title=f'Bienvenido a {client.name}',
                        subtitle='Sitio generado automáticamente',
                        description='Configura este texto desde tu admin.',
                        order=0,
                        is_active=True
                    )
                    logger.info(f"✅ Sección hero creada")

                messages.success(request, f"¡Tenant '{client.name}' creado exitosamente con tema '{client.template}'!")
                return redirect('/tenants/')
                
            except Exception as e:
                logger.error(f"❌ Error creando tenant: {e}")
                messages.error(request, f"Error creando tenant: {e}")
        
        else:
            # ⚠️ MOSTRAR ERRORES DE VALIDACIÓN
            logger.warning(f"⚠️ Errores de validación: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        form = TenantOnboardingForm()

    return render(request, 'tenants/admin/onboarding.html', {'form': form})


# --- VISTA 2: LISTA DE CLIENTES ---
@user_passes_test(lambda u: u.is_staff)
def tenant_list(request):
    clients = Client.objects.all().order_by('-created_at')
    return render(request, 'tenants/admin/tenant_list.html', {'clients': clients})