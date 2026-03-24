# =============================================================================
# apps/tenants/management/commands/send_contact_digest.py
# =============================================================================
# Envía resumen periódico de mensajes de contacto a cada tenant.
#
# USO:
#   python manage.py send_contact_digest
#       → Procesa todos los tenants con digest_enabled=True
#
#   python manage.py send_contact_digest --tenant servelec-ingenieria
#       → Procesa solo ese tenant (ignora digest_enabled)
#
#   python manage.py send_contact_digest --dry-run
#       → Muestra qué enviaría sin enviar nada
#
# CRON RECOMENDADO EN RENDER:
#   Diario:   0 8 * * *   → python manage.py send_contact_digest
#   Semanal:  0 8 * * 1   → python manage.py send_contact_digest
#   (El command filtra por frequency internamente)
# =============================================================================

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from apps.tenants.models import Client, ClientSettings
from apps.website.models import ContactSubmission

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía resumen de mensajes de contacto a cada tenant configurado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            default=None,
            help='Slug del tenant específico a procesar (ignora digest_enabled)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Muestra qué enviaría sin enviar ni purgar nada',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help='Fuerza el envío ignorando la frecuencia configurada',
        )

    def handle(self, *args, **options):
        dry_run   = options['dry_run']
        tenant_slug = options['tenant']
        force     = options['force']

        self.stdout.write(
            self.style.HTTP_INFO(
                f"\n{'[DRY RUN] ' if dry_run else ''}Iniciando digest de contactos...\n"
            )
        )

        # ── Obtener tenants a procesar ─────────────────────────────────────
        if tenant_slug:
            clients = Client.objects.filter(slug=tenant_slug, is_active=True)
            if not clients.exists():
                self.stderr.write(f"Tenant '{tenant_slug}' no encontrado o inactivo.")
                return
        else:
            # Solo tenants con digest activado
            clients = Client.objects.filter(
                is_active=True,
                settings__digest_enabled=True,
            ).select_related('settings', 'email_settings')

        if not clients.exists():
            self.stdout.write("No hay tenants con digest configurado.")
            return

        sent     = 0
        skipped  = 0
        errors   = 0

        for client in clients:
            try:
                result = self._process_tenant(client, dry_run=dry_run, force=force)
                if result == 'sent':
                    sent += 1
                elif result == 'skipped':
                    skipped += 1
            except Exception as e:
                errors += 1
                logger.error(f"[Digest] Error en tenant {client.slug}: {e}", exc_info=True)
                self.stderr.write(f"  ✗ {client.slug}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nResumen: {sent} enviados · {skipped} omitidos · {errors} errores\n"
            )
        )

    # ── Procesar un tenant ────────────────────────────────────────────────

    def _process_tenant(self, client, dry_run=False, force=False) -> str:
        """
        Procesa el digest para un tenant.

        Returns:
            'sent'    → email enviado
            'skipped' → no había mensajes o no correspondía enviar
        """
        try:
            client_settings = client.settings
        except ClientSettings.DoesNotExist:
            self.stdout.write(f"  · {client.slug}: sin ClientSettings, omitido")
            return 'skipped'

        # Verificar frecuencia (si no es --force)
        if not force and not self._should_send_today(client_settings):
            self.stdout.write(
                f"  · {client.slug}: no corresponde hoy "
                f"(frecuencia={client_settings.digest_frequency})"
            )
            return 'skipped'

        # Determinar período
        period_days = 1 if client_settings.digest_frequency == 'daily' else 7
        since = timezone.now() - timedelta(days=period_days)
        period_label = (
            'últimas 24 horas' if period_days == 1 else 'última semana'
        )

        # Obtener mensajes del período (excluyendo spam)
        base_qs = ContactSubmission.objects.filter(
            client=client,
            is_spam=False,
            created_at__gte=since,
        )

        contacts_new     = list(base_qs.filter(status='new').order_by('-created_at'))
        contacts_read    = list(base_qs.filter(status='read').order_by('-created_at'))
        contacts_replied = list(base_qs.filter(status='replied').order_by('-created_at'))
        total = len(contacts_new) + len(contacts_read) + len(contacts_replied)

        if total == 0:
            self.stdout.write(f"  · {client.slug}: sin mensajes en el período, omitido")
            return 'skipped'

        # Verificar que haya email configurado
        try:
            email_settings = client.email_settings
            to_emails = email_settings.get_notify_emails_list()
        except Exception:
            to_emails = [client.contact_email] if client.contact_email else []

        if not to_emails:
            self.stdout.write(
                f"  · {client.slug}: sin email destino configurado, omitido"
            )
            return 'skipped'

        # Purga (si está configurada)
        purge_info = None
        if client_settings.auto_purge_enabled and not dry_run:
            purge_info = self._purge_old_contacts(client, client_settings)

        # URL del dashboard
        primary_domain = client.primary_domain
        base_url = (
            f"https://{primary_domain.domain}"
            if primary_domain
            else getattr(settings, 'SITE_URL', 'https://andesscale.com')
        )
        dashboard_url = f"{base_url}/dashboard/contacts/"

        # Contexto del template
        context = {
            'client':           client,
            'contacts_new':     contacts_new,
            'contacts_read':    contacts_read,
            'contacts_replied': contacts_replied,
            'period_label':     period_label,
            'total':            total,
            'dashboard_url':    dashboard_url,
            'purge_info':       purge_info,
        }

        if dry_run:
            self.stdout.write(
                f"  [DRY RUN] {client.slug}: "
                f"{total} mensajes → enviaría a {to_emails}"
            )
            return 'sent'

        # Enviar
        self._send_digest_email(client, email_settings, to_emails, context)

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ {client.slug}: digest enviado ({total} mensajes) → {to_emails}"
            )
        )
        return 'sent'

    # ── Verificar si corresponde enviar hoy ──────────────────────────────

    def _should_send_today(self, client_settings) -> bool:
        """
        Determina si hoy corresponde enviar según la frecuencia.

        daily  → siempre True
        weekly → True solo los lunes (weekday == 0)
        """
        if client_settings.digest_frequency == 'daily':
            return True
        if client_settings.digest_frequency == 'weekly':
            return timezone.now().weekday() == 0  # Lunes
        return False

    # ── Enviar email ─────────────────────────────────────────────────────

    def _send_digest_email(self, client, email_settings, to_emails, context):
        """Construye y envía el email de digest."""
        period_label = context['period_label']
        total        = context['total']

        subject = f"[{client.name}] Resumen de contactos — {total} mensaje{'s' if total != 1 else ''} ({period_label})"

        html_content = render_to_string('emails/contact_digest.html', context)

        # Conexión según provider del tenant
        try:
            from apps.tenants.services.email_dispatcher import EmailDispatcher
            dispatcher = EmailDispatcher(client)
            connection = dispatcher._get_email_connection()
        except Exception:
            connection = get_connection()

        from_email = email_settings.get_from_email() if hasattr(email_settings, 'get_from_email') else (
            client.contact_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@andesscale.com')
        )

        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Resumen de {total} mensajes de {period_label}. Ver en: {context['dashboard_url']}",
            from_email=from_email,
            to=to_emails,
            connection=connection,
        )
        email.attach_alternative(html_content, 'text/html')
        email.send(fail_silently=False)

    # ── Purga ─────────────────────────────────────────────────────────────

    def _purge_old_contacts(self, client, client_settings) -> str:
        """
        Elimina mensajes leídos/respondidos más viejos que retention_days.

        Returns:
            Descripción del resultado para incluir en el email.
        """
        retention_days = max(client_settings.inbox_retention_days, 7)  # mínimo 7 días
        cutoff = timezone.now() - timedelta(days=retention_days)

        to_purge = ContactSubmission.objects.filter(
            client=client,
            status__in=['read', 'replied'],
            created_at__lt=cutoff,
            is_spam=False,
        )

        count = to_purge.count()

        if count == 0:
            return None

        to_purge.delete()

        logger.info(
            f"[Digest] Purged {count} old contacts for {client.slug} "
            f"(older than {retention_days} days)"
        )

        return (
            f"Se eliminaron {count} mensaje{'s' if count != 1 else ''} "
            f"con más de {retention_days} días (leídos/respondidos)."
        )
