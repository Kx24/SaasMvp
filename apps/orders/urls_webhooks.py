# apps/orders/urls_webhooks.py
"""
URLs para webhooks de pasarelas de pago.

Endpoints seguros que reciben notificaciones de:
- Mercado Pago (IPN)
- Futuro: otros proveedores

NOTA: Estas URLs no usan namespace porque son endpoints públicos
que Mercado Pago llama directamente.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Webhook de Mercado Pago (POST)
    path(
        'mercadopago/',
        views.mercadopago_webhook_view,
        name='mp_webhook'
    ),
    # Verificación GET (MP lo usa para validar endpoint)
    path(
        'mercadopago/verify/',
        views.mercadopago_webhook_get,
        name='mp_webhook_verify'
    ),
]
