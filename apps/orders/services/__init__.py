# apps/orders/services/__init__.py
"""
Servicios de la app orders.

- mercadopago_service: Integración con API de Mercado Pago
- order_processor: Lógica de procesamiento de órdenes
- email_service: Envío de emails transaccionales
"""

from .order_processor import OrderProcessor

__all__ = ['OrderProcessor']
