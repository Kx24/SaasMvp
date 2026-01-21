# apps/orders/services/mercadopago_service.py
"""
Servicio de integración con Mercado Pago - Checkout API.

Implementa:
- Procesamiento de pagos con token de tarjeta
- Consulta de estado de pagos
- Validación de webhooks

Documentación MP:
- https://www.mercadopago.cl/developers/es/docs/checkout-api/landing
- https://www.mercadopago.cl/developers/es/reference/payments/_payments/post
"""

import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from decimal import Decimal

import mercadopago
from django.conf import settings

logger = logging.getLogger(__name__)


class MercadoPagoError(Exception):
    """Excepción personalizada para errores de Mercado Pago."""
    
    def __init__(self, message: str, code: str = None, status: int = None, details: dict = None):
        self.message = message
        self.code = code
        self.status = status
        self.details = details or {}
        super().__init__(self.message)


class MercadoPagoService:
    """
    Servicio de integración con Mercado Pago.
    
    Uso:
        mp_service = MercadoPagoService()
        result = mp_service.process_payment(
            token='card_token_from_frontend',
            amount=150000,
            email='cliente@email.com',
            description='Plan Pro - Andesscale'
        )
    """
    
    def __init__(self):
        self.access_token = getattr(settings, 'MP_ACCESS_TOKEN', '')
        self.public_key = getattr(settings, 'MP_PUBLIC_KEY', '')
        self.webhook_secret = getattr(settings, 'MP_WEBHOOK_SECRET', '')
        self.sandbox = getattr(settings, 'MP_SANDBOX', True)
        
        if not self.access_token:
            logger.error("[MP Service] MP_ACCESS_TOKEN no configurado")
            raise MercadoPagoError("MP_ACCESS_TOKEN no configurado", code="CONFIG_ERROR")
        
        # Inicializar SDK
        self.sdk = mercadopago.SDK(self.access_token)
        
        logger.info(f"[MP Service] Inicializado (sandbox={self.sandbox})")
    
    def process_payment(
        self,
        token: str,
        amount: int,
        email: str,
        description: str,
        installments: int = 1,
        payment_method_id: str = None,
        external_reference: str = None,
        payer_name: str = None,
        idempotency_key: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Procesa un pago con token de tarjeta.
        
        Args:
            token: Token de tarjeta generado por MP.js en frontend
            amount: Monto en CLP (entero, sin decimales)
            email: Email del pagador
            description: Descripción del pago (aparece en estado de cuenta)
            installments: Número de cuotas (1 = sin cuotas)
            payment_method_id: Método de pago (visa, mastercard, etc)
            external_reference: ID interno (order_number)
            payer_name: Nombre del pagador
            idempotency_key: Clave para evitar pagos duplicados
        
        Returns:
            Dict con resultado:
            {
                'success': bool,
                'payment_id': str,
                'status': str,  # approved, pending, rejected, etc
                'status_detail': str,
                'message': str,
                'raw_response': dict
            }
        
        Raises:
            MercadoPagoError: Si hay error en el procesamiento
        """
        # Validar inputs
        if not token:
            raise MercadoPagoError("Token de tarjeta requerido", code="INVALID_TOKEN")
        
        if not amount or amount <= 0:
            raise MercadoPagoError("Monto inválido", code="INVALID_AMOUNT")
        
        if not email:
            raise MercadoPagoError("Email requerido", code="INVALID_EMAIL")
        
        # Construir payload
        payment_data = {
            "transaction_amount": float(amount),
            "token": token,
            "description": description,
            "installments": installments,
            "payer": {
                "email": email,
            }
        }
        
        # Agregar payment_method_id si viene
        if payment_method_id:
            payment_data["payment_method_id"] = payment_method_id
        
        # Agregar referencia externa (order_number)
        if external_reference:
            payment_data["external_reference"] = external_reference
        
        # Agregar nombre del pagador si viene
        if payer_name:
            payment_data["payer"]["first_name"] = payer_name.split()[0] if payer_name else ""
            if len(payer_name.split()) > 1:
                payment_data["payer"]["last_name"] = " ".join(payer_name.split()[1:])
        
        # Headers
        request_options = {}
        if idempotency_key:
            request_options["idempotency_key"] = idempotency_key
        
        logger.info(f"[MP Service] Procesando pago: ${amount} CLP - {email}")
        logger.debug(f"[MP Service] Payment data: {payment_data}")
        
        try:
            # Llamar a la API
            if request_options:
                response = self.sdk.payment().create(payment_data, request_options)
            else:
                response = self.sdk.payment().create(payment_data)
            
            status_code = response.get("status", 500)
            response_data = response.get("response", {})
            
            logger.info(f"[MP Service] Response status: {status_code}")
            logger.debug(f"[MP Service] Response data: {response_data}")
            
            # Verificar respuesta
            if status_code in [200, 201]:
                payment_status = response_data.get("status", "unknown")
                payment_id = str(response_data.get("id", ""))
                status_detail = response_data.get("status_detail", "")
                
                result = {
                    "success": payment_status == "approved",
                    "payment_id": payment_id,
                    "status": payment_status,
                    "status_detail": status_detail,
                    "message": self._get_status_message(payment_status, status_detail),
                    "payment_method_id": response_data.get("payment_method_id", ""),
                    "payment_type_id": response_data.get("payment_type_id", ""),
                    "raw_response": response_data
                }
                
                logger.info(
                    f"[MP Service] Pago procesado: ID={payment_id}, "
                    f"status={payment_status}, detail={status_detail}"
                )
                
                return result
            
            else:
                # Error de API
                error_message = response_data.get("message", "Error desconocido")
                error_cause = response_data.get("cause", [])
                
                logger.error(f"[MP Service] Error API: {status_code} - {error_message}")
                logger.error(f"[MP Service] Cause: {error_cause}")
                
                raise MercadoPagoError(
                    message=error_message,
                    code=str(status_code),
                    status=status_code,
                    details={"cause": error_cause}
                )
        
        except mercadopago.exceptions.MPException as e:
            logger.error(f"[MP Service] SDK Exception: {e}")
            raise MercadoPagoError(
                message=str(e),
                code="SDK_ERROR"
            )
        
        except Exception as e:
            logger.error(f"[MP Service] Unexpected error: {e}")
            raise MercadoPagoError(
                message=f"Error inesperado: {str(e)}",
                code="UNEXPECTED_ERROR"
            )
    
    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Consulta el estado de un pago.
        
        Args:
            payment_id: ID del pago en Mercado Pago
        
        Returns:
            Dict con datos del pago o None si no existe
        """
        if not payment_id:
            return None
        
        try:
            response = self.sdk.payment().get(payment_id)
            
            status_code = response.get("status", 500)
            response_data = response.get("response", {})
            
            if status_code == 200:
                return {
                    "payment_id": str(response_data.get("id", "")),
                    "status": response_data.get("status", ""),
                    "status_detail": response_data.get("status_detail", ""),
                    "amount": response_data.get("transaction_amount", 0),
                    "email": response_data.get("payer", {}).get("email", ""),
                    "external_reference": response_data.get("external_reference", ""),
                    "payment_method_id": response_data.get("payment_method_id", ""),
                    "payment_type_id": response_data.get("payment_type_id", ""),
                    "date_created": response_data.get("date_created", ""),
                    "date_approved": response_data.get("date_approved", ""),
                    "raw_response": response_data
                }
            
            logger.warning(f"[MP Service] Payment not found: {payment_id}")
            return None
        
        except Exception as e:
            logger.error(f"[MP Service] Error getting payment {payment_id}: {e}")
            return None
    
    def validate_webhook_signature(self, request) -> bool:
        """
        Valida la firma del webhook de Mercado Pago.
        
        Args:
            request: HttpRequest de Django
        
        Returns:
            True si la firma es válida
        
        Nota: MP envía la firma en el header 'x-signature'
        Formato: ts=timestamp,v1=hash
        """
        if not self.webhook_secret:
            logger.warning("[MP Service] Webhook secret no configurado, saltando validación")
            return True  # En desarrollo, permitir sin validación
        
        signature_header = request.headers.get('x-signature', '')
        request_id = request.headers.get('x-request-id', '')
        
        if not signature_header:
            logger.warning("[MP Service] Webhook sin firma")
            return False
        
        try:
            # Parsear header: ts=xxx,v1=yyy
            parts = dict(part.split('=') for part in signature_header.split(','))
            ts = parts.get('ts', '')
            v1 = parts.get('v1', '')
            
            if not ts or not v1:
                logger.warning("[MP Service] Formato de firma inválido")
                return False
            
            # Obtener data_id del query param
            data_id = request.GET.get('data.id', '')
            
            # Construir string para verificar
            # Formato: id:[data.id];request-id:[x-request-id];ts:[ts];
            manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
            
            # Calcular HMAC
            expected_hash = hmac.new(
                self.webhook_secret.encode(),
                manifest.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Comparar
            is_valid = hmac.compare_digest(expected_hash, v1)
            
            if not is_valid:
                logger.warning("[MP Service] Firma de webhook inválida")
            
            return is_valid
        
        except Exception as e:
            logger.error(f"[MP Service] Error validando firma: {e}")
            return False
    
    def refund_payment(
        self,
        payment_id: str,
        amount: int = None
    ) -> Dict[str, Any]:
        """
        Reembolsa un pago (total o parcial).
        
        Args:
            payment_id: ID del pago en MP
            amount: Monto a reembolsar (None = total)
        
        Returns:
            Dict con resultado del reembolso
        """
        try:
            refund_data = {}
            if amount:
                refund_data["amount"] = float(amount)
            
            response = self.sdk.refund().create(payment_id, refund_data)
            
            status_code = response.get("status", 500)
            response_data = response.get("response", {})
            
            if status_code in [200, 201]:
                return {
                    "success": True,
                    "refund_id": str(response_data.get("id", "")),
                    "status": response_data.get("status", ""),
                    "amount": response_data.get("amount", 0),
                    "raw_response": response_data
                }
            
            return {
                "success": False,
                "message": response_data.get("message", "Error en reembolso"),
                "raw_response": response_data
            }
        
        except Exception as e:
            logger.error(f"[MP Service] Error en reembolso: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def _get_status_message(self, status: str, status_detail: str) -> str:
        """
        Retorna mensaje legible según el estado del pago.
        """
        messages = {
            "approved": "¡Pago aprobado!",
            "pending": "Pago pendiente de confirmación",
            "authorized": "Pago autorizado, pendiente de captura",
            "in_process": "Pago en proceso de revisión",
            "in_mediation": "Pago en disputa",
            "rejected": self._get_rejection_message(status_detail),
            "cancelled": "Pago cancelado",
            "refunded": "Pago reembolsado",
            "charged_back": "Contracargo realizado",
        }
        
        return messages.get(status, f"Estado: {status}")
    
    def _get_rejection_message(self, status_detail: str) -> str:
        """
        Retorna mensaje específico de rechazo.
        """
        rejection_messages = {
            "cc_rejected_bad_filled_card_number": "Número de tarjeta incorrecto",
            "cc_rejected_bad_filled_date": "Fecha de vencimiento incorrecta",
            "cc_rejected_bad_filled_other": "Datos de tarjeta incorrectos",
            "cc_rejected_bad_filled_security_code": "Código de seguridad incorrecto",
            "cc_rejected_blacklist": "Tarjeta no permitida",
            "cc_rejected_call_for_authorize": "Debes autorizar el pago con tu banco",
            "cc_rejected_card_disabled": "Tarjeta deshabilitada",
            "cc_rejected_card_error": "Error en la tarjeta",
            "cc_rejected_duplicated_payment": "Pago duplicado",
            "cc_rejected_high_risk": "Pago rechazado por seguridad",
            "cc_rejected_insufficient_amount": "Fondos insuficientes",
            "cc_rejected_invalid_installments": "Cuotas no disponibles",
            "cc_rejected_max_attempts": "Máximo de intentos alcanzado",
            "cc_rejected_other_reason": "Pago rechazado por el banco",
        }
        
        return rejection_messages.get(
            status_detail,
            "Pago rechazado. Intenta con otra tarjeta."
        )
    
    def get_payment_methods(self) -> list:
        """
        Obtiene los métodos de pago disponibles.
        Útil para mostrar íconos de tarjetas aceptadas.
        """
        try:
            response = self.sdk.payment_methods().list_all()
            
            if response.get("status") == 200:
                return response.get("response", [])
            
            return []
        
        except Exception as e:
            logger.error(f"[MP Service] Error obteniendo payment methods: {e}")
            return []
