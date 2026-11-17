# =============================================================================
# apps/core/management/commands/cloudinary_usage.py
# =============================================================================
# Management command para ver el uso actual de créditos de Cloudinary
# Uso: python manage.py cloudinary_usage
# =============================================================================

import logging
from datetime import datetime

import cloudinary
import cloudinary.api
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


def credits_percent_of(usage):
    """(porcentaje, usados, límite) de créditos según la respuesta de la API."""
    credits = usage.get('credits', {})
    used = credits.get('used', 0)
    limit = credits.get('limit', 25)
    return ((used / limit * 100) if limit > 0 else 0), used, limit


def alert_level(percent):
    """'critical' | 'warning' | None según CLOUDINARY_ALERT_THRESHOLDS."""
    thresholds = settings.CLOUDINARY_ALERT_THRESHOLDS
    if percent >= thresholds['critical']:
        return 'critical'
    if percent >= thresholds['warning']:
        return 'warning'
    return None


def send_credit_alert(percent, used, limit):
    """
    Envía UN correo a PLATFORM_ALERT_EMAIL si el uso cruza un umbral.
    Devuelve el nivel enviado o None. Nunca lanza: un cron no debe fallar por esto.
    """
    level = alert_level(percent)
    if level is None:
        return None
    recipient = getattr(settings, 'PLATFORM_ALERT_EMAIL', '')
    if not recipient:
        logger.warning(
            '[Cloudinary] Créditos al %.1f%% (%s) pero PLATFORM_ALERT_EMAIL no está '
            'configurado: no se envió la alerta.', percent, level,
        )
        return None
    label = 'ALERTA' if level == 'critical' else 'Aviso'
    action = (
        'Reducir uploads o subir de plan cuanto antes.' if level == 'critical'
        else 'Monitorear el uso y revisar los assets más pesados.'
    )
    try:
        send_mail(
            subject=f'[AndesScale] {label}: créditos de Cloudinary al {percent:.0f}%',
            message=(
                f'Nivel: {label.lower()}\n'
                f'Uso de créditos: {percent:.1f}%\n'
                f'Usados / límite: {used:.2f} / {limit}\n\n'
                f'Qué hacer: {action}'
            ),
            from_email=None,
            recipient_list=[recipient],
            fail_silently=False,
        )
    except Exception:
        logger.error('[Cloudinary] No se pudo enviar la alerta de créditos', exc_info=True)
        return None
    return level


def check_credit_alert():
    """Consulta la API y envía la alerta si corresponde. No lanza nunca."""
    try:
        usage = cloudinary.api.usage()
        percent, used, limit = credits_percent_of(usage)
    except Exception as e:
        logger.error('[Cloudinary] Error obteniendo uso: %s', e)
        return None
    return send_credit_alert(percent, used, limit)


class Command(BaseCommand):
    help = 'Muestra el uso actual de créditos y recursos de Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output en formato JSON',
        )
        parser.add_argument(
            '--alert',
            action='store_true',
            help='Envía un correo a PLATFORM_ALERT_EMAIL si el uso supera los umbrales',
        )

    def handle(self, *args, **options):
        output_json = options['json']
        
        try:
            usage = cloudinary.api.usage()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error obteniendo uso: {e}'))
            return
        
        if options['alert']:
            percent, used, limit = credits_percent_of(usage)
            send_credit_alert(percent, used, limit)

        if output_json:
            import json
            self.stdout.write(json.dumps(usage, indent=2, default=str))
            return
        
        # Output formateado
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('☁️  CLOUDINARY USAGE REPORT'))
        self.stdout.write(self.style.HTTP_INFO(f'   Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        
        # Créditos
        credits_percent, credits_used, credits_limit = credits_percent_of(usage)
        thresholds = settings.CLOUDINARY_ALERT_THRESHOLDS
        
        self.stdout.write('\n💰 CRÉDITOS')
        self.stdout.write(f'   Usados:    {credits_used:.2f}')
        self.stdout.write(f'   Límite:    {credits_limit}')
        
        # Barra de progreso visual
        bar_length = 30
        filled = int(bar_length * credits_percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        if credits_percent >= thresholds['critical']:
            style = self.style.ERROR
        elif credits_percent >= thresholds['warning']:
            style = self.style.WARNING
        else:
            style = self.style.SUCCESS
        
        self.stdout.write(style(f'   Uso:       [{bar}] {credits_percent:.1f}%'))
        
        # Transformaciones
        transformations = usage.get('transformations', {})
        self.stdout.write('\n🔄 TRANSFORMACIONES')
        self.stdout.write(f'   Usadas:    {transformations.get("usage", 0):,}')
        self.stdout.write(f'   Límite:    {transformations.get("limit", "N/A")}')
        
        # Storage
        storage = usage.get('storage', {})
        storage_bytes = storage.get('usage', 0)
        storage_mb = storage_bytes / (1024 * 1024)
        self.stdout.write('\n💾 ALMACENAMIENTO')
        self.stdout.write(f'   Usado:     {storage_mb:.2f} MB ({storage_bytes:,} bytes)')
        
        # Bandwidth
        bandwidth = usage.get('bandwidth', {})
        bandwidth_bytes = bandwidth.get('usage', 0)
        bandwidth_mb = bandwidth_bytes / (1024 * 1024)
        self.stdout.write('\n📡 ANCHO DE BANDA')
        self.stdout.write(f'   Usado:     {bandwidth_mb:.2f} MB ({bandwidth_bytes:,} bytes)')
        
        # Requests
        requests = usage.get('requests', 0)
        self.stdout.write('\n🌐 REQUESTS')
        self.stdout.write(f'   Total:     {requests:,}')
        
        # Resources
        resources = usage.get('resources', 0)
        derived = usage.get('derived_resources', 0)
        self.stdout.write('\n📁 RECURSOS')
        self.stdout.write(f'   Originales: {resources:,}')
        self.stdout.write(f'   Derivados:  {derived:,}')
        
        # Alertas
        self.stdout.write('\n' + '=' * 60)
        
        if credits_percent >= thresholds['critical']:
            self.stdout.write(self.style.ERROR(
                f"🚨 ALERTA: Uso crítico de créditos (>{thresholds['critical']}%)"))
            self.stdout.write(self.style.ERROR('   Considerar upgrade o reducir uploads'))
        elif credits_percent >= thresholds['warning']:
            self.stdout.write(self.style.WARNING(
                f"⚠️  AVISO: Uso alto de créditos (>{thresholds['warning']}%)"))
        else:
            self.stdout.write(self.style.SUCCESS('✅ Uso de créditos saludable'))
        
        self.stdout.write('=' * 60 + '\n')
