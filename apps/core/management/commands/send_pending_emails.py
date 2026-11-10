"""
Envía los emails encolados en EmailOutbox (#MED-01).

Pensado para correr por cron cada 5 minutos (ver render.yaml). Reintenta
hasta EmailOutbox.max_attempts veces -- el "backoff" es el propio
intervalo del cron: un fallo deja el registro en 'pending' para el
próximo ciclo, no reintenta en el mismo proceso.

Uso:
    python manage.py send_pending_emails
"""
import logging

from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import EmailOutbox

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía los emails pendientes en la cola (EmailOutbox)'

    def handle(self, *args, **options):
        pending = list(EmailOutbox.objects.filter(status='pending').order_by('created_at'))

        sent_count = 0
        failed_count = 0

        for outbox_email in pending:
            try:
                email = EmailMultiAlternatives(
                    subject=outbox_email.subject,
                    body=outbox_email.text_content,
                    from_email=outbox_email.from_email,
                    to=[outbox_email.to_email],
                    reply_to=[outbox_email.reply_to] if outbox_email.reply_to else None,
                )
                email.attach_alternative(outbox_email.html_content, 'text/html')
                email.send(fail_silently=False)

                outbox_email.status = 'sent'
                outbox_email.sent_at = timezone.now()
                outbox_email.save(update_fields=['status', 'sent_at', 'updated_at'])
                sent_count += 1

            except Exception as e:
                outbox_email.attempts += 1
                outbox_email.last_error = str(e)[:2000]

                update_fields = ['attempts', 'last_error', 'updated_at']
                if outbox_email.attempts >= outbox_email.max_attempts:
                    outbox_email.status = 'failed'
                    outbox_email.failed_at = timezone.now()
                    update_fields += ['status', 'failed_at']
                    failed_count += 1

                outbox_email.save(update_fields=update_fields)
                logger.error(
                    f"[EmailOutbox] Error enviando a {outbox_email.to_email} "
                    f"(intento {outbox_email.attempts}/{outbox_email.max_attempts}): {e}"
                )

        still_pending = len(pending) - sent_count - failed_count
        self.stdout.write(self.style.SUCCESS(
            f"Enviados: {sent_count}, fallidos definitivos: {failed_count}, "
            f"pendientes (reintentarán): {still_pending}"
        ))
