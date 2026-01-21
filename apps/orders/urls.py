# apps/orders/urls.py
"""
URLs para el módulo de órdenes y pagos.

Estructura:
- /checkout/<plan_slug>/ → Página de checkout
- /checkout/process/ → Procesar pago (AJAX/POST)
- /checkout/success/<uuid>/ → Confirmación de pago
- /checkout/error/ → Error de pago
"""

from django.urls import path
from . import views

# IMPORTANTE: Necesario para namespace en config/urls.py
app_name = 'orders'

urlpatterns = [
    # Checkout por plan
    path(
        '<slug:plan_slug>/',
        views.checkout_view,
        name='checkout'
    ),
    # Procesar pago
    path(
        'process/',
        views.process_payment_view,
        name='checkout_process'
    ),
    # Éxito
    path(
        'success/<uuid:order_uuid>/',
        views.checkout_success_view,
        name='checkout_success'
    ),
    # Error
    path(
        'error/',
        views.checkout_error_view,
        name='checkout_error'
    ),
]
