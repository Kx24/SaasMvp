# apps/orders/signals.py
"""
Signals para la app de órdenes.

Incluye:
- Logging automático de cambios de estado
- Notificaciones (futuro)
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Order, PaymentLog

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def log_order_status_change(sender, instance, **kwargs):
    """
    Loggea cambios de estado en la orden.
    """
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                logger.info(
                    f"[Order {instance.order_number}] "
                    f"Estado cambió: {old_instance.status} → {instance.status}"
                )
                
                # Crear log de pago si el cambio está relacionado con pago
                if instance.status in ['paid', 'failed', 'refunded']:
                    PaymentLog.objects.create(
                        order=instance,
                        action=f'status_change_{instance.status}',
                        mp_payment_id=instance.mp_payment_id,
                        status=instance.mp_status,
                        status_detail=instance.mp_status_detail,
                        amount=instance.amount,
                    )
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """
    Acciones post-guardado de orden.
    """
    if created:
        logger.info(f"[Order] Nueva orden creada: {instance.order_number}")
