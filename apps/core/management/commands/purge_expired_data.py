"""
Purga de datos vencidos (LEY-03, Ley 21.719 art. 14 d).

- EmailOutbox en estado final (sent/failed) con mas de EMAIL_OUTBOX_RETENTION_DAYS.
- Order con mas de ORDER_RETENTION_DAYS (sus PaymentLog caen en cascada; el
  Client asociado se conserva porque Order.client es SET_NULL y el borrado va
  en la direccion Order -> Client, nunca al reves).

Uso: python manage.py purge_expired_data [--dry-run]
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import EmailOutbox
from apps.orders.models import Order, PaymentLog

logger = logging.getLogger(__name__)


def purge_expired_data(dry_run=False) -> dict:
    """Borra (o cuenta, si dry_run) los datos vencidos. Devuelve conteos por tipo."""
    now = timezone.now()
    outbox = EmailOutbox.objects.filter(
        status__in=['sent', 'failed'],
        created_at__lt=now - timedelta(days=settings.EMAIL_OUTBOX_RETENTION_DAYS),
    )
    orders = Order.objects.filter(
        created_at__lt=now - timedelta(days=settings.ORDER_RETENTION_DAYS),
    )
    counts = {
        'email_outbox': outbox.count(),
        'payment_logs': PaymentLog.objects.filter(order__in=orders).count(),
        'orders': orders.count(),
    }
    if not dry_run:
        outbox.delete()
        orders.delete()  # PaymentLog: on_delete=CASCADE
    logger.info(
        '[Purge] %s email_outbox=%d orders=%d payment_logs=%d',
        'dry-run' if dry_run else 'deleted',
        counts['email_outbox'], counts['orders'], counts['payment_logs'],
    )
    return counts


class Command(BaseCommand):
    help = 'Elimina EmailOutbox (90 dias) y Order/PaymentLog (6 anios) vencidos'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=False,
                            help='Solo cuenta, no borra nada')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        counts = purge_expired_data(dry_run=dry_run)
        verb = 'borraria' if dry_run else 'borro'
        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}{verb}: "
            f"{counts['email_outbox']} emails en cola, "
            f"{counts['orders']} ordenes, {counts['payment_logs']} registros de pago"
        )
