# apps/orders/views.py
"""
Vistas para checkout y procesamiento de pagos.

Flujo completo:
1. checkout_view: Muestra formulario de pago con MP Brick
2. process_payment_view: Recibe datos de MP y procesa pago
3. checkout_success_view: Confirmación post-pago
4. checkout_error_view: Error de pago
5. mercadopago_webhook_view: Recibe notificaciones IPN
"""

import json
import logging
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.db import transaction

from .models import Plan, Order, PaymentLog
from .services.mercadopago_service import MercadoPagoService, MercadoPagoError

logger = logging.getLogger(__name__)


# ==============================================================================
# CHECKOUT VIEWS
# ==============================================================================

def checkout_view(request, plan_slug):
    """
    Página de checkout con formulario de Mercado Pago embebido.
    
    URL: GET /checkout/<plan_slug>/
    """
    plan = get_object_or_404(Plan, slug=plan_slug, is_active=True)
    
    context = {
        'plan': plan,
        'mp_public_key': getattr(settings, 'MP_PUBLIC_KEY', ''),
    }
    
    return render(request, 'orders/checkout.html', context)


@require_POST
def process_payment_view(request):
    """
    Procesa el pago recibido desde el frontend.
    
    Recibe (JSON):
    - token: Token de tarjeta generado por MP.js
    - payment_method_id: Método de pago (visa, master, etc)
    - installments: Número de cuotas
    - email: Email del comprador
    - plan_slug: Plan seleccionado
    - payer_name: Nombre del pagador (opcional)
    
    Retorna JSON:
    - success: true/false
    - order_uuid: UUID de la orden (si éxito)
    - redirect_url: URL para redirigir (si éxito)
    - error: mensaje de error (si falla)
    
    URL: POST /checkout/process/
    """
    try:
        # Parsear JSON del body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Datos inválidos',
                'code': 'INVALID_JSON'
            }, status=400)
        
        # Extraer datos
        token = data.get('token', '')
        payment_method_id = data.get('payment_method_id', '')
        installments = data.get('installments', 1)
        email = data.get('email', '').lower().strip()
        plan_slug = data.get('plan_slug', '')
        payer_name = data.get('payer_name', '')
        
        # Validaciones básicas
        if not token:
            return JsonResponse({
                'success': False,
                'error': 'Token de tarjeta requerido',
                'code': 'MISSING_TOKEN'
            }, status=400)
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email requerido',
                'code': 'MISSING_EMAIL'
            }, status=400)
        
        if not plan_slug:
            return JsonResponse({
                'success': False,
                'error': 'Plan no especificado',
                'code': 'MISSING_PLAN'
            }, status=400)
        
        # Obtener plan
        try:
            plan = Plan.objects.get(slug=plan_slug, is_active=True)
        except Plan.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Plan no encontrado',
                'code': 'INVALID_PLAN'
            }, status=400)
        
        # Crear orden en estado pending
        with transaction.atomic():
            order = Order.objects.create(
                plan=plan,
                email=email,
                buyer_name=payer_name,
                amount=plan.price,
                currency='CLP',
                status='processing',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            # Log del intento
            PaymentLog.objects.create(
                order=order,
                action='payment_attempt',
                amount=plan.price,
                ip_address=get_client_ip(request),
                raw_data={
                    'email': email,
                    'plan': plan_slug,
                    'payment_method_id': payment_method_id,
                    'installments': installments
                }
            )
        
        logger.info(f"[Checkout] Orden creada: {order.order_number} - Plan: {plan.name}")
        
        # Procesar pago con Mercado Pago
        try:
            mp_service = MercadoPagoService()
            
            result = mp_service.process_payment(
                token=token,
                amount=int(plan.price),
                email=email,
                description=f"{plan.name} - Andesscale",
                installments=installments,
                payment_method_id=payment_method_id,
                external_reference=order.order_number,
                payer_name=payer_name,
                idempotency_key=str(order.uuid)
            )
            
            # Actualizar orden según resultado
            with transaction.atomic():
                if result['success']:
                    # Pago aprobado
                    order.mark_as_paid(
                        mp_payment_id=result['payment_id'],
                        mp_data=result['raw_response']
                    )
                    
                    PaymentLog.objects.create(
                        order=order,
                        action='payment_approved',
                        mp_payment_id=result['payment_id'],
                        status=result['status'],
                        status_detail=result['status_detail'],
                        amount=plan.price,
                        ip_address=get_client_ip(request),
                        raw_data=result['raw_response']
                    )
                    
                    logger.info(
                        f"[Checkout] Pago aprobado: {order.order_number} - "
                        f"MP ID: {result['payment_id']}"
                    )
                    
                    # URL de éxito
                    success_url = f"/checkout/success/{order.uuid}/"
                    
                    return JsonResponse({
                        'success': True,
                        'order_uuid': str(order.uuid),
                        'order_number': order.order_number,
                        'redirect_url': success_url,
                        'message': result['message']
                    })
                
                else:
                    # Pago rechazado o pendiente
                    order.status = 'failed' if result['status'] == 'rejected' else 'pending'
                    order.mp_payment_id = result.get('payment_id', '')
                    order.mp_status = result['status']
                    order.mp_status_detail = result['status_detail']
                    order.mp_response_data = result['raw_response']
                    order.save()
                    
                    PaymentLog.objects.create(
                        order=order,
                        action=f"payment_{result['status']}",
                        mp_payment_id=result.get('payment_id', ''),
                        status=result['status'],
                        status_detail=result['status_detail'],
                        amount=plan.price,
                        ip_address=get_client_ip(request),
                        raw_data=result['raw_response']
                    )
                    
                    logger.warning(
                        f"[Checkout] Pago no aprobado: {order.order_number} - "
                        f"Status: {result['status']} - Detail: {result['status_detail']}"
                    )
                    
                    return JsonResponse({
                        'success': False,
                        'error': result['message'],
                        'code': result['status_detail'],
                        'status': result['status']
                    }, status=400)
        
        except MercadoPagoError as e:
            # Error de Mercado Pago
            order.status = 'failed'
            order.notes = f"Error MP: {e.message}"
            order.save()
            
            PaymentLog.objects.create(
                order=order,
                action='payment_error',
                status='error',
                status_detail=e.code or 'MP_ERROR',
                ip_address=get_client_ip(request),
                raw_data={'error': e.message, 'code': e.code, 'details': e.details}
            )
            
            logger.error(f"[Checkout] Error MP: {e.message}")
            
            return JsonResponse({
                'success': False,
                'error': e.message,
                'code': e.code or 'MP_ERROR'
            }, status=400)
    
    except Exception as e:
        logger.exception(f"[Checkout] Error inesperado: {e}")
        
        return JsonResponse({
            'success': False,
            'error': 'Error procesando el pago. Intenta nuevamente.',
            'code': 'UNEXPECTED_ERROR'
        }, status=500)


def checkout_success_view(request, order_uuid):
    """
    Página de confirmación post-pago exitoso.
    
    URL: GET /checkout/success/<order_uuid>/
    """
    order = get_object_or_404(Order, uuid=order_uuid)
    
    # Solo mostrar si el pago fue exitoso
    if order.status not in ['paid', 'onboarding', 'completed']:
        return redirect('orders:checkout_error')
    
    context = {
        'order': order,
        'onboarding_url': order.get_onboarding_url(),
    }
    
    return render(request, 'orders/checkout_success.html', context)


def checkout_error_view(request):
    """
    Página de error de pago.
    
    URL: GET /checkout/error/
    """
    error_code = request.GET.get('code', '')
    error_message = request.GET.get('message', '')
    
    context = {
        'error_code': error_code,
        'error_message': error_message,
    }
    
    return render(request, 'orders/checkout_error.html', context)


# ==============================================================================
# WEBHOOK VIEWS
# ==============================================================================

@csrf_exempt
@require_POST
def mercadopago_webhook_view(request):
    """
    Webhook para recibir notificaciones de Mercado Pago (IPN).
    
    MP envía notificaciones cuando cambia el estado de un pago.
    
    URL: POST /webhook/mercadopago/
    
    Query params que envía MP:
    - type: tipo de notificación (payment, merchant_order, etc)
    - data.id: ID del recurso
    """
    try:
        # Obtener parámetros
        notification_type = request.GET.get('type', '')
        data_id = request.GET.get('data.id', '')
        
        logger.info(f"[MP Webhook] Recibido: type={notification_type}, data_id={data_id}")
        
        # Solo procesar notificaciones de pago
        if notification_type != 'payment':
            logger.info(f"[MP Webhook] Ignorando tipo: {notification_type}")
            return HttpResponse(status=200)
        
        if not data_id:
            logger.warning("[MP Webhook] data.id vacío")
            return HttpResponse(status=200)
        
        # Validar firma (opcional pero recomendado)
        mp_service = MercadoPagoService()
        
        # En producción, descomentar validación:
        # if not mp_service.validate_webhook_signature(request):
        #     logger.warning("[MP Webhook] Firma inválida")
        #     return HttpResponse(status=401)
        
        # Consultar estado real del pago en MP
        payment_data = mp_service.get_payment(data_id)
        
        if not payment_data:
            logger.warning(f"[MP Webhook] Pago no encontrado: {data_id}")
            return HttpResponse(status=200)
        
        payment_status = payment_data['status']
        external_reference = payment_data.get('external_reference', '')
        
        logger.info(
            f"[MP Webhook] Pago {data_id}: status={payment_status}, "
            f"ref={external_reference}"
        )
        
        # Buscar orden por external_reference (order_number)
        if external_reference:
            try:
                order = Order.objects.get(order_number=external_reference)
            except Order.DoesNotExist:
                logger.warning(f"[MP Webhook] Orden no encontrada: {external_reference}")
                return HttpResponse(status=200)
        else:
            # Buscar por mp_payment_id
            try:
                order = Order.objects.get(mp_payment_id=data_id)
            except Order.DoesNotExist:
                logger.warning(f"[MP Webhook] Orden no encontrada para pago: {data_id}")
                return HttpResponse(status=200)
        
        # Actualizar orden según estado
        with transaction.atomic():
            # Evitar procesar si ya está en estado final
            if order.status in ['completed', 'refunded']:
                logger.info(f"[MP Webhook] Orden ya finalizada: {order.order_number}")
                return HttpResponse(status=200)
            
            # Log
            PaymentLog.objects.create(
                order=order,
                action=f'webhook_{payment_status}',
                mp_payment_id=data_id,
                status=payment_status,
                status_detail=payment_data.get('status_detail', ''),
                amount=payment_data.get('amount'),
                raw_data=payment_data.get('raw_response', {})
            )
            
            if payment_status == 'approved' and order.status not in ['paid', 'onboarding', 'completed']:
                # Pago aprobado (por si el webhook llega antes de la respuesta directa)
                order.mark_as_paid(data_id, payment_data.get('raw_response', {}))
                logger.info(f"[MP Webhook] Orden marcada como pagada: {order.order_number}")
                
                # TODO: Enviar email de confirmación (Card A6)
            
            elif payment_status == 'rejected':
                order.status = 'failed'
                order.mp_status = payment_status
                order.mp_status_detail = payment_data.get('status_detail', '')
                order.save()
                logger.info(f"[MP Webhook] Orden marcada como fallida: {order.order_number}")
            
            elif payment_status == 'refunded':
                order.status = 'refunded'
                order.mp_status = payment_status
                order.save()
                logger.info(f"[MP Webhook] Orden marcada como reembolsada: {order.order_number}")
        
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.exception(f"[MP Webhook] Error: {e}")
        # Siempre retornar 200 para que MP no reintente
        return HttpResponse(status=200)


@csrf_exempt
def mercadopago_webhook_get(request):
    """
    MP hace GET para verificar que el endpoint existe.
    """
    return HttpResponse("OK", status=200)


# ==============================================================================
# HELPERS
# ==============================================================================

def get_client_ip(request):
    """Obtiene la IP real del cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
