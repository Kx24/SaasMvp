"""
Email Dispatcher Service
========================

Ruta: apps/tenants/services/email_dispatcher.py

Este servicio maneja el envío de emails según la configuración del tenant.
El formulario de contacto NO decide nada, solo llama a este dispatcher.

Uso:
    from apps.tenants.services.email_dispatcher import EmailDispatcher
    
    dispatcher = EmailDispatcher(client)
    result = dispatcher.send_contact_notification(contact_submission)
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


class NotifyResult(Enum):
    """Resultado del envío de notificación."""
    SUCCESS = "success"
    SKIPPED = "skipped"  # No configurado para enviar
    FAILED = "failed"
    TEST_MODE = "test_mode"


@dataclass
class DispatchResult:
    """Resultado del dispatch de notificación."""
    status: NotifyResult
    email_sent: bool
    dashboard_logged: bool
    message: str
    error: Optional[str] = None


class EmailDispatcher:
    """
    Dispatcher de emails configurado por tenant.
    
    Responsabilidades:
    - Determinar si debe enviar email según configuración
    - Construir conexión SMTP/API según provider
    - Enviar email con template correcto
    - Loguear resultado
    """
    
    def __init__(self, client):
        """
        Inicializa el dispatcher para un cliente específico.
        
        Args:
            client: Instancia de Client (tenant)
        """
        self.client = client
        self._email_settings = None
    
    @property
    def email_settings(self):
        """Obtiene o crea ClientEmailSettings."""
        if self._email_settings is None:
            from apps.tenants.models import ClientEmailSettings
            self._email_settings, created = ClientEmailSettings.objects.get_or_create(
                client=self.client
            )
            if created:
                logger.info(f"[EmailDispatcher] Created default email settings for {self.client.slug}")
        return self._email_settings
    
    def send_contact_notification(self, contact_submission) -> DispatchResult:
        """
        Envía notificación de nuevo contacto según configuración.
        
        Args:
            contact_submission: Instancia de ContactSubmission
            
        Returns:
            DispatchResult con el estado del envío
        """
        settings = self.email_settings
        
        # Dashboard siempre se "notifica" (el registro ya existe)
        dashboard_logged = True
        
        # Determinar si debe enviar email
        should_send_email = (
            settings.notify_mode in ['email', 'both'] and
            settings.can_send_email()
        )
        
        if not should_send_email:
            logger.info(
                f"[EmailDispatcher] Skipping email for {self.client.slug} "
                f"(mode={settings.notify_mode}, can_send={settings.can_send_email()})"
            )
            return DispatchResult(
                status=NotifyResult.SKIPPED,
                email_sent=False,
                dashboard_logged=dashboard_logged,
                message="Email no configurado, solo dashboard"
            )
        
        # Modo test: loguear pero no enviar
        if settings.test_mode:
            logger.info(
                f"[EmailDispatcher] TEST MODE - Would send email for contact "
                f"{contact_submission.id} to {settings.get_notify_emails_list()}"
            )
            return DispatchResult(
                status=NotifyResult.TEST_MODE,
                email_sent=False,
                dashboard_logged=dashboard_logged,
                message="Modo test: email no enviado"
            )
        
        # Intentar enviar email
        try:
            self._send_email(contact_submission)
            
            logger.info(
                f"[EmailDispatcher] Email sent for contact {contact_submission.id} "
                f"from {self.client.slug}"
            )
            
            return DispatchResult(
                status=NotifyResult.SUCCESS,
                email_sent=True,
                dashboard_logged=dashboard_logged,
                message="Email enviado correctamente"
            )
            
        except Exception as e:
            logger.error(
                f"[EmailDispatcher] Failed to send email for {self.client.slug}: {e}",
                exc_info=True
            )
            return DispatchResult(
                status=NotifyResult.FAILED,
                email_sent=False,
                dashboard_logged=dashboard_logged,
                message="Error al enviar email",
                error=str(e)
            )
    
    def _send_email(self, contact_submission):
        """
        Envía el email usando la configuración del tenant.
        
        Args:
            contact_submission: ContactSubmission instance
        """
        es = self.email_settings
        
        # Construir asunto
        subject = es.email_subject_template.format(
            name=contact_submission.name,
            email=contact_submission.email,
            subject=getattr(contact_submission, 'subject', '') or 'Nuevo contacto'
        )
        
        # Destinatarios
        to_emails = es.get_notify_emails_list()
        if not to_emails:
            raise ValueError("No hay emails destinatarios configurados")
        
        # Contexto para template
        context = {
            'contact': contact_submission,
            'client': self.client,
            'settings': self.client.settings if hasattr(self.client, 'settings') else None,
        }
        
        # Renderizar contenido
        html_content = render_to_string(
            'emails/contact_notification.html',
            context
        )
        text_content = render_to_string(
            'emails/contact_notification.txt',
            context
        )
        
        # Construir conexión según provider
        connection = self._get_email_connection()
        
        # Crear email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=es.get_from_email(),
            to=to_emails,
            reply_to=[es.reply_to] if es.reply_to else [contact_submission.email],
            connection=connection
        )
        email.attach_alternative(html_content, "text/html")
        
        # Enviar
        email.send(fail_silently=False)
        
        # Enviar copia al remitente si está configurado
        if es.send_copy_to_sender and contact_submission.email:
            self._send_copy_to_sender(contact_submission, context)
    
    def _get_email_connection(self):
        """
        Construye la conexión de email según el provider configurado.
        
        Returns:
            Email connection object
        """
        es = self.email_settings
        
        if es.provider == 'smtp':
            return get_connection(
                host=es.smtp_host,
                port=es.smtp_port,
                username=es.smtp_username,
                password=es.smtp_password,
                use_tls=es.smtp_use_tls,
                use_ssl=es.smtp_use_ssl,
            )
        
        elif es.provider == 'sendgrid':
            # SendGrid usa SMTP con API key como password
            return get_connection(
                host='smtp.sendgrid.net',
                port=587,
                username='apikey',
                password=es.api_key,
                use_tls=True,
            )
        
        elif es.provider == 'resend':
            # Resend usa SMTP
            return get_connection(
                host='smtp.resend.com',
                port=465,
                username='resend',
                password=es.api_key,
                use_ssl=True,
            )
        
        elif es.provider == 'mailgun':
            # Mailgun SMTP
            return get_connection(
                host='smtp.mailgun.org',
                port=587,
                username=es.smtp_username or 'postmaster@' + es.from_email.split('@')[-1],
                password=es.api_key,
                use_tls=True,
            )
        
        else:
            # Usar configuración por defecto de Django
            return get_connection()
    
    def _send_copy_to_sender(self, contact_submission, context):
        """Envía copia de confirmación al remitente del formulario."""
        try:
            es = self.email_settings
            
            html_content = render_to_string(
                'emails/contact_confirmation.html',
                context
            )
            text_content = render_to_string(
                'emails/contact_confirmation.txt',
                context
            )
            
            connection = self._get_email_connection()
            
            email = EmailMultiAlternatives(
                subject=f"Hemos recibido tu mensaje - {self.client.name}",
                body=text_content,
                from_email=es.get_from_email(),
                to=[contact_submission.email],
                connection=connection
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=True)
            
        except Exception as e:
            logger.warning(f"[EmailDispatcher] Failed to send copy to sender: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión de email.
        
        Returns:
            Dict con resultado del test
        """
        es = self.email_settings
        
        if not es.can_send_email():
            return {
                'success': False,
                'error': 'Email no configurado correctamente'
            }
        
        try:
            connection = self._get_email_connection()
            connection.open()
            connection.close()
            
            # Actualizar estado del test
            es.last_test_at = timezone.now()
            es.last_test_success = True
            es.last_test_error = ''
            es.save(update_fields=['last_test_at', 'last_test_success', 'last_test_error'])
            
            return {
                'success': True,
                'message': 'Conexión exitosa'
            }
            
        except Exception as e:
            # Guardar error
            es.last_test_at = timezone.now()
            es.last_test_success = False
            es.last_test_error = str(e)
            es.save(update_fields=['last_test_at', 'last_test_success', 'last_test_error'])
            
            return {
                'success': False,
                'error': str(e)
            }