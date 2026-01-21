# apps/orders/services/order_processor.py
"""
Servicio para procesamiento de órdenes.

Centraliza la lógica de:
- Creación de órdenes
- Validación de datos
- Transiciones de estado
"""

import logging
from typing import Optional, Dict, Any
from django.db import transaction

from ..models import Plan, Order

logger = logging.getLogger(__name__)


class OrderProcessor:
    """
    Procesador de órdenes.
    
    Uso:
        processor = OrderProcessor()
        order = processor.create_order(
            plan_slug='pro',
            email='cliente@email.com',
            ip_address='192.168.1.1'
        )
    """
    
    def create_order(
        self,
        plan_slug: str,
        email: str,
        buyer_name: str = '',
        buyer_phone: str = '',
        ip_address: str = None,
        user_agent: str = '',
        **billing_data
    ) -> Order:
        """
        Crea una nueva orden.
        
        Args:
            plan_slug: Slug del plan a contratar
            email: Email del comprador
            buyer_name: Nombre del comprador (opcional)
            buyer_phone: Teléfono (opcional)
            ip_address: IP del cliente
            user_agent: User agent del navegador
            **billing_data: Datos de facturación
        
        Returns:
            Order: Instancia de la orden creada
        
        Raises:
            Plan.DoesNotExist: Si el plan no existe
        """
        plan = Plan.objects.get(slug=plan_slug, is_active=True)
        
        with transaction.atomic():
            order = Order.objects.create(
                plan=plan,
                email=email.lower().strip(),
                buyer_name=buyer_name,
                buyer_phone=buyer_phone,
                amount=plan.price,
                currency='CLP',
                status='pending',
                ip_address=ip_address,
                user_agent=user_agent,
                billing_rut=billing_data.get('billing_rut', ''),
                billing_razon_social=billing_data.get('billing_razon_social', ''),
                billing_giro=billing_data.get('billing_giro', ''),
                billing_direccion=billing_data.get('billing_direccion', ''),
                billing_comuna=billing_data.get('billing_comuna', ''),
            )
            
            logger.info(
                f"[OrderProcessor] Orden creada: {order.order_number} "
                f"- Plan: {plan.name} - Email: {email}"
            )
            
            return order
    
    def process_successful_payment(
        self,
        order: Order,
        mp_payment_id: str,
        mp_data: Dict[str, Any]
    ) -> Order:
        """
        Procesa un pago exitoso.
        
        Args:
            order: Orden a actualizar
            mp_payment_id: ID del pago en Mercado Pago
            mp_data: Datos completos del pago
        
        Returns:
            Order: Orden actualizada
        """
        with transaction.atomic():
            order.mark_as_paid(mp_payment_id, mp_data)
            
            logger.info(
                f"[OrderProcessor] Pago exitoso: {order.order_number} "
                f"- MP ID: {mp_payment_id}"
            )
            
            # TODO: Enviar email de confirmación (Card A6)
            # self._send_payment_confirmation_email(order)
            
            return order
    
    def process_failed_payment(
        self,
        order: Order,
        mp_data: Dict[str, Any]
    ) -> Order:
        """
        Procesa un pago fallido.
        
        Args:
            order: Orden a actualizar
            mp_data: Datos del intento de pago
        
        Returns:
            Order: Orden actualizada
        """
        with transaction.atomic():
            order.mark_as_failed(mp_data)
            
            logger.warning(
                f"[OrderProcessor] Pago fallido: {order.order_number} "
                f"- Status: {mp_data.get('status')} "
                f"- Detail: {mp_data.get('status_detail')}"
            )
            
            return order
    
    def complete_onboarding(
        self,
        order: Order,
        client
    ) -> Order:
        """
        Completa el proceso de onboarding.
        
        Args:
            order: Orden a completar
            client: Cliente/Tenant creado
        
        Returns:
            Order: Orden completada
        """
        with transaction.atomic():
            order.mark_as_completed(client)
            
            logger.info(
                f"[OrderProcessor] Onboarding completado: {order.order_number} "
                f"- Cliente: {client.name}"
            )
            
            # TODO: Enviar email de sitio listo (Card A6)
            # self._send_site_ready_email(order, client)
            
            return order
    
    def get_order_by_token(self, token: str) -> Optional[Order]:
        """
        Obtiene una orden por su token de onboarding.
        
        Args:
            token: UUID del token
        
        Returns:
            Order o None si no existe o no es válido
        """
        try:
            order = Order.objects.get(onboarding_token=token)
            if order.is_token_valid():
                return order
            return None
        except Order.DoesNotExist:
            return None
    
    def get_order_by_payment_id(self, mp_payment_id: str) -> Optional[Order]:
        """
        Obtiene una orden por su ID de pago en Mercado Pago.
        
        Args:
            mp_payment_id: ID del pago en MP
        
        Returns:
            Order o None si no existe
        """
        try:
            return Order.objects.get(mp_payment_id=mp_payment_id)
        except Order.DoesNotExist:
            return None
