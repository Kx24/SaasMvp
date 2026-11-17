"""
Derechos del titular (Ley 21.719, LEY-02 parte 2): exportar, suprimir y bloquear
los datos de una persona, siempre acotado a UN tenant.

    python manage.py data_subject export  --email a@b.cl --tenant <slug> [--output f.json]
    python manage.py data_subject erase   --email a@b.cl --tenant <slug> [--dry-run] [--request-id N]
    python manage.py data_subject block   --email a@b.cl --tenant <slug> [--request-id N]
    python manage.py data_subject unblock --email a@b.cl --tenant <slug>

`erase` es IRREVERSIBLE: borra ContactSubmission y EmailOutbox; Order se conserva
(obligacion legal) pero anonimizada, y PaymentLog pierde los datos personales de
raw_data. Procedimiento completo en Documentacion/SEGURIDAD.md §3.
"""
import hashlib
import hmac
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.models import EmailOutbox
from apps.orders.models import Order, PaymentLog
from apps.tenants.models import Client
from apps.website.models import BlockedSubject, ContactSubmission, DataSubjectRequest

MASK = '[suprimido]'

# Claves de raw_data (payload de Mercado Pago y similares) con datos personales.
PII_KEYS = {
    'email', 'payer', 'first_name', 'last_name', 'name', 'phone', 'identification',
    'ip', 'ip_address', 'address', 'rut', 'buyer_name', 'buyer_phone', 'billing_rut',
    'cardholder', 'card_holder_name',
}

CONTACT_FIELDS = [
    'id', 'name', 'email', 'phone', 'company', 'subject', 'message', 'status',
    'form_source', 'is_spam', 'ip_address', 'consent_at', 'consent_policy_version',
    'created_at',
]
ORDER_FIELDS = [
    'uuid', 'order_number', 'email', 'buyer_name', 'buyer_phone', 'billing_rut',
    'billing_razon_social', 'billing_giro', 'billing_direccion', 'billing_comuna',
    'status', 'ip_address', 'created_at',
]
LOG_FIELDS = ['id', 'action', 'mp_payment_id', 'status', 'status_detail', 'amount',
              'raw_data', 'ip_address', 'created_at']
OUTBOX_FIELDS = ['id', 'to_email', 'reply_to', 'subject', 'text_content', 'status', 'created_at']
DSR_FIELDS = ['id', 'request_type', 'name', 'email', 'detail', 'status', 'received_at',
              'due_at', 'resolved_at', 'response_notes', 'ip_address']


def _rows(qs, fields):
    return list(qs.values(*fields))


def _scoped(client, email):
    """Querysets de la persona dentro de `client` (nunca de otro tenant)."""
    order_filter = Q(client=client)
    if client.slug == getattr(settings, 'PLATFORM_TENANT_SLUG', None):
        # Compras aun sin tenant propio (pre-onboarding) pertenecen a la plataforma.
        order_filter |= Q(client__isnull=True)
    orders = Order.objects.filter(order_filter, email__iexact=email)
    return {
        'contacts': ContactSubmission.objects.filter(client=client, email__iexact=email),
        'orders': orders,
        'payment_logs': PaymentLog.objects.filter(order__in=orders),
        'outbox': EmailOutbox.objects.filter(client=client).filter(
            Q(to_email__iexact=email) | Q(reply_to__iexact=email)),
        'requests': DataSubjectRequest.objects.filter(client=client, email__iexact=email),
    }


def _scrub(value, email):
    """Copia de `value` sin datos personales (conserva montos, estados e ids)."""
    if isinstance(value, dict):
        return {k: (MASK if str(k).lower() in PII_KEYS else _scrub(v, email)) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v, email) for v in value]
    if isinstance(value, str) and value.strip().lower() == email:
        return MASK
    return value


def _anon_email(email):
    digest = hmac.new(settings.SECRET_KEY.encode(), email.encode(), hashlib.sha256).hexdigest()[:10]
    return f'suprimido-{digest}@invalid'


def export_data(client, email):
    s = _scoped(client, email)
    logs = {}
    for log in s['payment_logs'].order_by('id').values('order_id', *LOG_FIELDS):
        logs.setdefault(log.pop('order_id'), []).append(log)
    orders = []
    for order in s['orders'].order_by('created_at').values(*ORDER_FIELDS):
        order['payment_logs'] = logs.get(order['uuid'], [])
        orders.append(order)
    return {
        'email': email,
        'tenant': client.slug,
        'exported_at': timezone.now(),
        'contact_messages': _rows(s['contacts'].order_by('id'), CONTACT_FIELDS),
        'orders': orders,
        'queued_emails': _rows(s['outbox'].order_by('id'), OUTBOX_FIELDS),
        'data_subject_requests': _rows(s['requests'].order_by('id'), DSR_FIELDS),
        'blocked': BlockedSubject.objects.filter(client=client, email=email).exists(),
    }


def erase_data(client, email, dry_run=False):
    s = _scoped(client, email)
    counts = {
        'contact_messages': s['contacts'].count(),
        'queued_emails': s['outbox'].count(),
        'orders': s['orders'].count(),
        'payment_logs': s['payment_logs'].count(),
    }
    if dry_run:
        return counts
    with transaction.atomic():
        for log in s['payment_logs']:
            log.raw_data = _scrub(log.raw_data, email)
            log.ip_address = None
            log.save(update_fields=['raw_data', 'ip_address'])
        anon = _anon_email(email)
        for order in list(s['orders']):
            order.email = anon
            order.buyer_name = MASK
            order.buyer_phone = MASK
            order.billing_rut = MASK
            order.billing_razon_social = MASK
            order.billing_direccion = MASK
            order.ip_address = None
            order.save(update_fields=['email', 'buyer_name', 'buyer_phone', 'billing_rut',
                                      'billing_razon_social', 'billing_direccion', 'ip_address'])
        s['contacts'].delete()
        s['outbox'].delete()
    return counts


class Command(BaseCommand):
    help = 'Exporta, suprime o bloquea los datos de una persona en un tenant (Ley 21.719)'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['export', 'erase', 'block', 'unblock'])
        parser.add_argument('--email', required=True)
        parser.add_argument('--tenant', required=True, help='slug del tenant')
        parser.add_argument('--output', help='archivo de salida (solo export)')
        parser.add_argument('--dry-run', action='store_true', default=False)
        parser.add_argument('--request-id', type=int, default=None)

    def handle(self, *args, **options):
        action = options['action']
        email = (options['email'] or '').strip().lower()
        if not email or '@' not in email:
            raise CommandError('--email invalido')
        client = Client.objects.filter(slug=options['tenant']).first()
        if client is None:
            raise CommandError(f"Tenant '{options['tenant']}' no existe")

        dsr = None
        if options['request_id'] is not None:
            dsr = DataSubjectRequest.objects.filter(client=client, pk=options['request_id']).first()
            if dsr is None:
                raise CommandError(
                    f"La solicitud {options['request_id']} no existe en el tenant '{client.slug}'")

        note = None
        if action == 'export':
            payload = json.dumps(export_data(client, email), cls=DjangoJSONEncoder,
                                 ensure_ascii=False, indent=2)
            if options['output']:
                with open(options['output'], 'w', encoding='utf-8') as fh:
                    fh.write(payload)
                self.stdout.write(f"Exportado a {options['output']}")
            else:
                self.stdout.write(payload)
            note = 'exportacion de datos generada'
        elif action == 'erase':
            counts = erase_data(client, email, dry_run=options['dry_run'])
            prefix = '[DRY RUN] ' if options['dry_run'] else ''
            self.stdout.write(
                f"{prefix}{'suprimiria' if options['dry_run'] else 'suprimio'}: "
                f"{counts['contact_messages']} mensajes de contacto, "
                f"{counts['queued_emails']} emails en cola, "
                f"{counts['orders']} ordenes anonimizadas, "
                f"{counts['payment_logs']} registros de pago depurados")
            if options['dry_run']:
                return
            note = (f"supresion: {counts['contact_messages']} mensajes y "
                    f"{counts['queued_emails']} emails borrados, {counts['orders']} ordenes "
                    f"anonimizadas, {counts['payment_logs']} registros de pago depurados")
        elif action == 'block':
            reason = f'Solicitud #{dsr.pk}' if dsr else ''
            _, created = BlockedSubject.objects.get_or_create(
                client=client, email=email, defaults={'reason': reason})
            self.stdout.write('Bloqueado' if created else 'Ya estaba bloqueado')
            note = 'bloqueo temporal aplicado'
        else:
            deleted, _ = BlockedSubject.objects.filter(client=client, email=email).delete()
            self.stdout.write('Desbloqueado' if deleted else 'No estaba bloqueado')
            note = 'bloqueo temporal levantado'

        if dsr and note:
            line = f"[{timezone.now():%Y-%m-%d %H:%M}] data_subject {action}: {note}"
            dsr.response_notes = f"{dsr.response_notes}\n{line}".strip()
            dsr.save(update_fields=['response_notes'])
