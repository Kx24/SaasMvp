# apps/orders/models.py
"""
Modelos para gestión de órdenes y pagos.

Arquitectura:
- Plan: Planes de suscripción disponibles (Essential, Pro, Enterprise)
- Order: Órdenes de compra vinculadas a pagos de Mercado Pago

Desacoplado de tenants para permitir:
- Escalabilidad a suscripciones recurrentes
- Múltiples órdenes por cliente (renovaciones)
- Historial de pagos independiente
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.urls import reverse


# ==============================================================================
# PLAN - Planes de suscripción
# ==============================================================================

class Plan(models.Model):
    """
    Planes disponibles para contratación.
    
    Cada plan define:
    - Precio y características incluidas
    - Temas visuales disponibles
    - Límites de recursos (páginas, servicios, imágenes)
    """
    
    name = models.CharField(
        max_length=50,
        help_text="Nombre del plan (ej: 'Plan Pro')"
    )
    
    slug = models.SlugField(
        max_length=50,
        unique=True,
        help_text="Identificador URL (ej: 'pro')"
    )
    
    # ==================== PRICING ====================
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=0,  # CLP no usa decimales
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Precio en CLP (pago único inicial)"
    )
    
    # Precio de renovación (para futuro modelo de suscripción)
    renewal_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        default=Decimal('0'),
        help_text="Precio mensual de renovación (futuro)"
    )
    
    # ==================== DESCRIPCIÓN ====================
    
    tagline = models.CharField(
        max_length=100,
        blank=True,
        help_text="Subtítulo corto (ej: 'Ideal para emprendedores')"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Descripción completa para landing page"
    )
    
    # Features como JSON para flexibilidad
    # Ejemplo: ["Sitio web profesional", "Hosting 1 año", "Soporte por email"]
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de características incluidas (JSON array)"
    )
    
    # ==================== TEMAS DISPONIBLES ====================
    
    # Temas que puede elegir el cliente con este plan
    # Ejemplo: ["default"] para Essential, ["default", "electricidad", "industrial"] para Pro
    available_themes = models.JSONField(
        default=list,
        blank=True,
        help_text="Temas disponibles para este plan (JSON array de slugs)"
    )
    
    # ==================== LÍMITES ====================
    
    max_pages = models.IntegerField(
        default=5,
        help_text="Máximo de páginas permitidas"
    )
    
    max_services = models.IntegerField(
        default=10,
        help_text="Máximo de servicios en catálogo"
    )
    
    max_images = models.IntegerField(
        default=50,
        help_text="Máximo de imágenes en Cloudinary"
    )
    
    max_storage_mb = models.IntegerField(
        default=100,
        help_text="Almacenamiento máximo en MB"
    )
    
    # ==================== CARACTERÍSTICAS BOOLEANAS ====================
    
    has_custom_domain = models.BooleanField(
        default=False,
        help_text="¿Permite dominio personalizado?"
    )
    
    has_analytics = models.BooleanField(
        default=False,
        help_text="¿Incluye analytics avanzados?"
    )
    
    has_priority_support = models.BooleanField(
        default=False,
        help_text="¿Incluye soporte prioritario?"
    )
    
    has_white_label = models.BooleanField(
        default=False,
        help_text="¿Sin marca Andesscale?"
    )
    
    # ==================== DISPLAY ====================
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿Visible en página de precios?"
    )
    
    is_featured = models.BooleanField(
        default=False,
        help_text="¿Destacar como recomendado?"
    )
    
    display_order = models.IntegerField(
        default=0,
        help_text="Orden de aparición (menor = primero)"
    )
    
    # ==================== METADATA ====================
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'price']
        verbose_name = 'Plan'
        verbose_name_plural = 'Planes'
    
    def __str__(self):
        return f"{self.name} - ${self.price:,.0f} CLP"
    
    def get_features_list(self):
        """Retorna features como lista Python."""
        if isinstance(self.features, list):
            return self.features
        return []
    
    def get_available_themes_list(self):
        """Retorna temas disponibles como lista."""
        if isinstance(self.available_themes, list):
            return self.available_themes
        return ['default']
    
    def get_absolute_url(self):
        """URL del checkout para este plan."""
        return reverse('orders:checkout', kwargs={'plan_slug': self.slug})


# ==============================================================================
# ORDER - Órdenes de compra
# ==============================================================================

class Order(models.Model):
    """
    Orden de compra que rastrea el ciclo completo:
    Creación → Pago → Onboarding → Completado
    
    Separada de Client para:
    - Permitir múltiples órdenes (renovaciones futuras)
    - Mantener historial de pagos
    - Desacoplar billing de identidad
    """
    
    # ==================== ESTADOS ====================
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente de Pago'),
        ('processing', 'Procesando Pago'),
        ('paid', 'Pagado - Pendiente Onboarding'),
        ('onboarding', 'En Proceso de Onboarding'),
        ('completed', 'Completado'),
        ('failed', 'Pago Fallido'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
        ('expired', 'Token Expirado'),
    ]
    
    # ==================== IDENTIFICACIÓN ====================
    
    # UUID como PK pública (no exponer autoincrement)
    uuid = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Identificador público de la orden"
    )
    
    # Número de orden legible (para facturas, soporte)
    order_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Número de orden legible (ej: ORD-2024-0001)"
    )
    
    # ==================== RELACIONES ====================
    
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,  # No borrar planes con órdenes
        related_name='orders',
        help_text="Plan contratado"
    )
    
    # Se llena después del onboarding
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        help_text="Tenant creado (post-onboarding)"
    )
    
    # ==================== DATOS DEL COMPRADOR ====================
    
    email = models.EmailField(
        help_text="Email del comprador"
    )
    
    # Nombre opcional (puede completarse en onboarding)
    buyer_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre del comprador"
    )
    
    buyer_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Teléfono del comprador"
    )
    
    # ==================== FACTURACIÓN (para SII futuro) ====================
    
    billing_rut = models.CharField(
        max_length=12,
        blank=True,
        help_text="RUT para facturación (ej: 12.345.678-9)"
    )
    
    billing_razon_social = models.CharField(
        max_length=200,
        blank=True,
        help_text="Razón social o nombre"
    )
    
    billing_giro = models.CharField(
        max_length=200,
        blank=True,
        help_text="Giro comercial"
    )
    
    billing_direccion = models.CharField(
        max_length=300,
        blank=True,
        help_text="Dirección fiscal"
    )
    
    billing_comuna = models.CharField(
        max_length=100,
        blank=True,
        help_text="Comuna"
    )
    
    # ==================== PAGO ====================
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Monto pagado en CLP"
    )
    
    currency = models.CharField(
        max_length=3,
        default='CLP',
        help_text="Moneda del pago"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text="Estado actual de la orden"
    )
    
    # ==================== MERCADO PAGO ====================
    
    mp_payment_id = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="ID del pago en Mercado Pago"
    )
    
    mp_status = models.CharField(
        max_length=50,
        blank=True,
        help_text="Estado del pago en MP (approved, pending, rejected, etc)"
    )
    
    mp_status_detail = models.CharField(
        max_length=100,
        blank=True,
        help_text="Detalle del estado en MP"
    )
    
    mp_payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text="Método de pago usado (credit_card, debit_card, etc)"
    )
    
    mp_payment_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Tipo de pago (credit_card, bank_transfer, etc)"
    )
    
    # Respuesta completa de MP para debug/auditoría
    mp_response_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Respuesta completa de Mercado Pago (JSON)"
    )
    
    # ==================== ONBOARDING TOKEN ====================
    
    onboarding_token = models.UUIDField(
        unique=True,
        null=True,
        blank=True,
        help_text="Token único para acceso a onboarding"
    )
    
    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de expiración del token"
    )
    
    # ==================== TIMESTAMPS ====================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación de la orden"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última actualización"
    )
    
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha/hora del pago exitoso"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha/hora de finalización del onboarding"
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de expiración de la orden (si no se paga)"
    )
    
    # ==================== NOTAS ====================
    
    notes = models.TextField(
        blank=True,
        help_text="Notas internas (no visibles al cliente)"
    )
    
    # IP y User Agent para auditoría/fraude
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP del comprador"
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text="User Agent del navegador"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email']),
            models.Index(fields=['mp_payment_id']),
            models.Index(fields=['onboarding_token']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.email} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Generar número de orden si no existe
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)
    
    def _generate_order_number(self):
        """Genera número de orden único: ORD-YYYY-NNNN"""
        year = timezone.now().year
        # Contar órdenes del año actual
        count = Order.objects.filter(
            created_at__year=year
        ).count() + 1
        return f"ORD-{year}-{count:04d}"
    
    # ==================== MÉTODOS DE ESTADO ====================
    
    def generate_onboarding_token(self, hours=72):
        """
        Genera token único para acceso a onboarding.
        Por defecto expira en 72 horas.
        """
        self.onboarding_token = uuid.uuid4()
        self.token_expires_at = timezone.now() + timedelta(hours=hours)
        self.save(update_fields=['onboarding_token', 'token_expires_at', 'updated_at'])
        return self.onboarding_token
    
    def is_token_valid(self):
        """Verifica si el token de onboarding es válido."""
        if not self.onboarding_token:
            return False
        if not self.token_expires_at:
            return False
        if timezone.now() > self.token_expires_at:
            return False
        if self.status not in ['paid', 'onboarding']:
            return False
        return True
    
    def mark_as_paid(self, mp_payment_id, mp_data=None):
        """
        Marca la orden como pagada y genera token de onboarding.
        """
        self.status = 'paid'
        self.mp_payment_id = mp_payment_id
        self.paid_at = timezone.now()
        
        if mp_data:
            self.mp_status = mp_data.get('status', '')
            self.mp_status_detail = mp_data.get('status_detail', '')
            self.mp_payment_method = mp_data.get('payment_method_id', '')
            self.mp_payment_type = mp_data.get('payment_type_id', '')
            self.mp_response_data = mp_data
        
        self.save()
        self.generate_onboarding_token()
        
        return self
    
    def mark_as_failed(self, mp_data=None):
        """Marca la orden como fallida."""
        self.status = 'failed'
        if mp_data:
            self.mp_status = mp_data.get('status', '')
            self.mp_status_detail = mp_data.get('status_detail', '')
            self.mp_response_data = mp_data
        self.save()
        return self
    
    def mark_as_completed(self, client):
        """Marca la orden como completada tras el onboarding."""
        self.status = 'completed'
        self.client = client
        self.completed_at = timezone.now()
        self.onboarding_token = None
        self.token_expires_at = None
        self.save()
        return self
    
    def mark_as_expired(self):
        """Marca la orden como expirada (token vencido)."""
        self.status = 'expired'
        self.onboarding_token = None
        self.token_expires_at = None
        self.save()
        return self
    
    def start_onboarding(self):
        """Marca que el cliente comenzó el onboarding."""
        if self.status == 'paid':
            self.status = 'onboarding'
            self.save(update_fields=['status', 'updated_at'])
        return self
    
    # ==================== URLS ====================
    
    def get_onboarding_url(self):
        """Retorna URL completa de onboarding con token."""
        if not self.onboarding_token:
            return None
        base_url = getattr(settings, 'BASE_URL', 'https://andesscale.cl')
        return f"{base_url}/onboarding/{self.onboarding_token}/"
    
    def get_absolute_url(self):
        """URL de detalle de la orden (para admin)."""
        return reverse('admin:orders_order_change', args=[self.uuid])
    
    # ==================== PROPIEDADES ====================
    
    @property
    def is_paid(self):
        return self.status in ['paid', 'onboarding', 'completed']
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def can_start_onboarding(self):
        """Verifica si puede iniciar onboarding."""
        return self.status == 'paid' and self.is_token_valid()
    
    @property
    def days_until_token_expires(self):
        """Días restantes hasta que expire el token."""
        if not self.token_expires_at:
            return None
        delta = self.token_expires_at - timezone.now()
        return max(0, delta.days)


# ==============================================================================
# PAYMENT LOG - Historial de intentos de pago
# ==============================================================================

class PaymentLog(models.Model):
    """Log de todos los intentos de pago para auditoría."""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payment_logs'
    )
    
    action = models.CharField(
        max_length=50,
        help_text="Acción realizada (create, approve, reject, refund, etc)"
    )
    
    mp_payment_id = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=50, blank=True)
    status_detail = models.CharField(max_length=100, blank=True)
    
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True
    )
    
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos crudos del evento"
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log de Pago'
        verbose_name_plural = 'Logs de Pagos'
    
    def __str__(self):
        return f"{self.order.order_number} - {self.action} - {self.created_at}"
