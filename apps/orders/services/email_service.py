# apps/orders/services/email_service.py
"""
Servicio de emails transaccionales para el flujo de pagos.

Emails implementados:
1. payment_success - Pago exitoso + link de onboarding
2. welcome - Bienvenida post-onboarding + link para configurar contraseña
3. site_ready - Sitio listo (confirmación final)
4. token_expiring - Recordatorio de token por expirar
5. password_reset - Recuperar/configurar contraseña

Usa Django's send_mail con templates HTML.
"""

import logging
from typing import Optional
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio centralizado para envío de emails transaccionales.
    
    Uso:
        email_service = EmailService()
        email_service.send_payment_success(order)
        email_service.send_welcome(client, user, token)
    """
    
    def __init__(self):
        self.from_email = getattr(
            settings, 
            'DEFAULT_FROM_EMAIL', 
            'Andesscale <no-reply@andesscale.cl>'
        )
        self.base_url = getattr(settings, 'BASE_URL', 'https://andesscale.cl')
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict,
        reply_to: str = None
    ) -> bool:
        """
        Método interno para enviar emails con template HTML.
        
        Args:
            to_email: Destinatario
            subject: Asunto del email
            template_name: Nombre del template (sin extensión)
            context: Contexto para el template
            reply_to: Email de respuesta (opcional)
        
        Returns:
            bool: True si se envió correctamente
        """
        try:
            # Agregar variables comunes al contexto
            context.update({
                'base_url': self.base_url,
                'support_email': getattr(settings, 'SUPPORT_EMAIL', 'soporte@andesscale.cl'),
                'company_name': 'Andesscale',
            })
            
            # Renderizar templates
            html_content = render_to_string(f'emails/{template_name}.html', context)
            text_content = strip_tags(html_content)
            
            # Crear email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=self.from_email,
                to=[to_email],
                reply_to=[reply_to] if reply_to else None
            )
            email.attach_alternative(html_content, "text/html")
            
            # Enviar
            email.send(fail_silently=False)
            
            logger.info(f"[Email] Enviado '{template_name}' a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"[Email] Error enviando '{template_name}' a {to_email}: {e}")
            return False
    
    # =========================================================================
    # EMAIL 1: PAGO EXITOSO
    # =========================================================================
    
    def send_payment_success(self, order) -> bool:
        """
        Envía email de confirmación de pago con link de onboarding.
        
        Se envía inmediatamente después de que el pago es aprobado.
        
        Args:
            order: Instancia de Order con status='paid'
        
        Template: emails/payment_success.html
        """
        if not order.onboarding_token:
            logger.warning(f"[Email] Order {order.order_number} sin token de onboarding")
            return False
        
        onboarding_url = f"{self.base_url}/onboarding/{order.onboarding_token}/"
        
        context = {
            'order': order,
            'plan': order.plan,
            'onboarding_url': onboarding_url,
            'token_expires_hours': 72,
        }
        
        return self._send_email(
            to_email=order.email,
            subject=f"✅ Pago confirmado - {order.plan.name} | Andesscale",
            template_name='payment_success',
            context=context
        )
    
    # =========================================================================
    # EMAIL 2: BIENVENIDA POST-ONBOARDING
    # =========================================================================
    
    def send_welcome(self, client, user, invitation_token: str) -> bool:
        """
        Envía email de bienvenida con link para configurar contraseña.
        
        Se envía después de completar el onboarding.
        
        Args:
            client: Instancia de Client creado
            user: Instancia de User creado
            invitation_token: Token para configurar contraseña
        
        Template: emails/welcome.html
        """
        set_password_url = f"{self.base_url}/auth/set-password/{invitation_token}/"
        site_url = f"https://{client.slug}.andesscale.cl"  # Ajustar según tu config
        
        context = {
            'client': client,
            'user': user,
            'set_password_url': set_password_url,
            'site_url': site_url,
            'dashboard_url': f"{self.base_url}/dashboard/",
        }
        
        return self._send_email(
            to_email=user.email,
            subject=f"🎉 ¡Bienvenido a Andesscale! - Configura tu contraseña",
            template_name='welcome',
            context=context
        )
    
    # =========================================================================
    # EMAIL 3: SITIO LISTO
    # =========================================================================
    
    def send_site_ready(self, client, user) -> bool:
        """
        Envía confirmación de que el sitio está listo.
        
        Se puede enviar después del onboarding o cuando el admin
        hace alguna configuración adicional.
        
        Args:
            client: Instancia de Client
            user: Instancia de User (owner)
        
        Template: emails/site_ready.html
        """
        site_url = f"https://{client.slug}.andesscale.cl"
        
        context = {
            'client': client,
            'user': user,
            'site_url': site_url,
            'dashboard_url': f"{self.base_url}/dashboard/",
        }
        
        return self._send_email(
            to_email=user.email,
            subject=f"🚀 ¡Tu sitio {client.name} está listo!",
            template_name='site_ready',
            context=context
        )
    
    # =========================================================================
    # EMAIL 4: RECORDATORIO DE TOKEN POR EXPIRAR
    # =========================================================================
    
    def send_token_expiring(self, order, hours_remaining: int = 24) -> bool:
        """
        Envía recordatorio de que el token de onboarding está por expirar.
        
        Se envía típicamente 24 horas antes de que expire.
        
        Args:
            order: Instancia de Order
            hours_remaining: Horas restantes para expirar
        
        Template: emails/token_expiring.html
        """
        if not order.onboarding_token:
            return False
        
        onboarding_url = f"{self.base_url}/onboarding/{order.onboarding_token}/"
        
        context = {
            'order': order,
            'plan': order.plan,
            'onboarding_url': onboarding_url,
            'hours_remaining': hours_remaining,
        }
        
        return self._send_email(
            to_email=order.email,
            subject=f"⏰ Tu enlace de configuración expira en {hours_remaining} horas",
            template_name='token_expiring',
            context=context
        )
    
    # =========================================================================
    # EMAIL 5: CONFIGURAR/RECUPERAR CONTRASEÑA
    # =========================================================================
    
    def send_set_password(self, user, token: str, is_reset: bool = False) -> bool:
        """
        Envía link para configurar o recuperar contraseña.
        
        Args:
            user: Instancia de User
            token: Token de invitación/reset
            is_reset: True si es recuperación, False si es configuración inicial
        
        Template: emails/set_password.html
        """
        set_password_url = f"{self.base_url}/auth/set-password/{token}/"
        
        context = {
            'user': user,
            'set_password_url': set_password_url,
            'is_reset': is_reset,
            'expires_hours': 24 if is_reset else 168,  # 24h reset, 7 días inicial
        }
        
        subject = "🔐 Recupera tu contraseña" if is_reset else "🔐 Configura tu contraseña"
        
        return self._send_email(
            to_email=user.email,
            subject=f"{subject} | Andesscale",
            template_name='set_password',
            context=context
        )
    
    # =========================================================================
    # EMAIL 6: CONTACTO RECIBIDO (para el cliente)
    # =========================================================================
    
    def send_contact_received(self, client, contact_data: dict) -> bool:
        """
        Notifica al cliente que recibió un mensaje de contacto.
        
        Args:
            client: Instancia de Client que recibe el contacto
            contact_data: Dict con nombre, email, mensaje, etc.
        
        Template: emails/contact_received.html
        """
        # Obtener email del cliente (settings o admin)
        to_email = client.settings.contact_email if hasattr(client, 'settings') else None
        
        if not to_email:
            logger.warning(f"[Email] Client {client.slug} sin email de contacto configurado")
            return False
        
        context = {
            'client': client,
            'contact': contact_data,
        }
        
        return self._send_email(
            to_email=to_email,
            subject=f"📬 Nuevo mensaje de contacto en {client.name}",
            template_name='contact_received',
            context=context,
            reply_to=contact_data.get('email')
        )


# =========================================================================
# FUNCIONES HELPER (para usar sin instanciar la clase)
# =========================================================================

def send_payment_success_email(order) -> bool:
    """Helper para enviar email de pago exitoso."""
    return EmailService().send_payment_success(order)


def send_welcome_email(client, user, invitation_token: str) -> bool:
    """Helper para enviar email de bienvenida."""
    return EmailService().send_welcome(client, user, invitation_token)


def send_site_ready_email(client, user) -> bool:
    """Helper para enviar email de sitio listo."""
    return EmailService().send_site_ready(client, user)


def send_token_expiring_email(order, hours_remaining: int = 24) -> bool:
    """Helper para enviar recordatorio de token."""
    return EmailService().send_token_expiring(order, hours_remaining)


def send_set_password_email(user, token: str, is_reset: bool = False) -> bool:
    """Helper para enviar email de configurar contraseña."""
    return EmailService().send_set_password(user, token, is_reset)


def send_contact_received_email(client, contact_data: dict) -> bool:
    """Helper para notificar contacto recibido."""
    return EmailService().send_contact_received(client, contact_data)
