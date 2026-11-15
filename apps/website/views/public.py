import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render

from apps.core.logging_utils import email_ref
from apps.core.rate_limit import RateLimiter, get_client_ip
from apps.core.template_resolver import get_tenant_template, render_tenant_template

from ..forms import ContactForm
from ..models import ContactSubmission, Section, Service

logger = logging.getLogger(__name__)




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


def privacy_policy(request):
    """Política de privacidad vigente (LEY-01). Pública, sin login."""
    client = request.client
    if client is None:
        raise Http404('Sin tenant')
    site_settings = client.settings
    context = {
        'company': client.company_name or client.name,
        'contact_email': site_settings.contact_email,
        'contact_phone': site_settings.contact_phone,
        'address': site_settings.address,
        'retention_days': settings.CONTACT_MAX_RETENTION_DAYS,
        'version': settings.PRIVACY_POLICY_VERSION,
        'version_date': settings.PRIVACY_POLICY_DATE,
        'is_platform': client.slug == settings.PLATFORM_TENANT_SLUG,
    }
    return render_tenant_template(request, 'legal/privacy.html', context)


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
        f"from {email_ref(contact.email)} | source={contact.form_source} "
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
