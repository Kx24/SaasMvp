"""
Modelos para el sistema Multi-Tenant.

Cada Client representa un cliente/tenant del sistema (ej: ServelecPage, tu Portafolio).
Todos los demás modelos del sistema tendrán una ForeignKey a Client para aislar datos.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify


class Client(models.Model):
    """
    Representa un cliente/tenant del sistema.
    
    Cada cliente tiene:
    - Su propio dominio (ej: servelec-ingenieria.cl)
    - Contenido aislado (secciones, servicios, etc.)
    - Configuración independiente
    
    Ejemplo de uso:
        cliente_servelec = Client.objects.create(
            name="Servelec Ingeniería",
            domain="servelec-ingenieria.cl",
            company_name="Servelec Ingeniería SpA"
        )
    """
    
    # ==================== IDENTIFICACIÓN ====================
    name = models.CharField(
        max_length=100,
        help_text="Nombre interno del cliente (ej: 'Servelec Ingeniería')"
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Identificador único generado automáticamente (ej: 'servelec-ingenieria')"
    )
    
    # ==================== DOMINIO ====================
    domain = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,  # Índice para búsquedas rápidas por dominio
        help_text="Dominio completo sin https:// (ej: 'servelec-ingenieria.cl')"
    )
    
    # ==================== INFORMACIÓN EMPRESA ====================
    company_name = models.CharField(
        max_length=200,
        help_text="Nombre legal/comercial de la empresa"
    )
    
    contact_email = models.EmailField(
        help_text="Email principal de contacto del cliente"
    )
    
    contact_phone = models.CharField(
        max_length=20,
        help_text="Teléfono de contacto (ej: +56912345678)"
    )
    
    # ==================== TEMPLATE APLICADO ====================
    template = models.CharField(
        max_length=50,
        choices=[
            ('electricidad', 'Electricidad/Servicios Técnicos'),
            ('construccion', 'Construcción'),
            ('servicios_profesionales', 'Servicios Profesionales'),
            ('portafolio', 'Portafolio Personal'),
            ('custom', 'Personalizado'),
        ],
        default='custom',
        help_text="Template base aplicado a este cliente"
    )
    
    # ==================== ESTADO ====================
    is_active = models.BooleanField(
        default=True,
        help_text="Si está inactivo, el sitio mostrará mensaje de mantenimiento"
    )
    
    setup_completed = models.BooleanField(
        default=False,
        help_text="Marca cuando el cliente complete su configuración inicial"
    )
    
    # ==================== BILLING (Fase 1: Manual) ====================
    setup_fee_paid = models.BooleanField(
        default=False,
        help_text="¿El cliente pagó el fee de setup inicial?"
    )
    
    monthly_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=80.00,
        help_text="Tarifa mensual en USD (default: $80)"
    )
    
    last_payment_date = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha del último pago mensual recibido"
    )
    
    next_payment_due = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha del próximo pago esperado"
    )
    
    # ==================== LÍMITES (Para planes futuros) ====================
    max_images = models.IntegerField(
        default=100,
        help_text="Cantidad máxima de imágenes permitidas en Cloudinary"
    )
    
    max_pages = models.IntegerField(
        default=10,
        help_text="Cantidad máxima de páginas/secciones permitidas"
    )
    
    # ==================== METADATA ====================
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del cliente"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Última actualización"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Notas internas sobre el cliente (no visible para él)"
    )
    
    class Meta:
        ordering = ['-created_at']  # Más recientes primero
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        indexes = [
            models.Index(fields=['domain']),  # Búsqueda rápida por dominio
            models.Index(fields=['is_active']),  # Filtrar activos/inactivos
        ]
    
    def __str__(self):
        """Representación en string del cliente"""
        return f"{self.company_name} ({self.domain})"
    
    def save(self, *args, **kwargs):
        """
        Override del método save para auto-generar slug.
        
        El slug se genera automáticamente desde el 'name' si no existe.
        Ejemplo: "Servelec Ingeniería" → "servelec-ingenieria"
        """
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Validar que el dominio no esté vacío
        if not self.domain:
            raise ValidationError("El dominio es requerido")
        
        super().save(*args, **kwargs)
    
    @property
    def is_payment_current(self):
        """
        Verifica si el cliente está al día con sus pagos.
        
        Returns:
            bool: True si no hay próximo pago o si aún no vence
        """
        if not self.next_payment_due:
            return True
        
        from django.utils import timezone
        return timezone.now().date() <= self.next_payment_due
    
    def get_absolute_url(self):
        """URL completa del sitio del cliente"""
        return f"https://{self.domain}"


class ClientSettings(models.Model):
    """
    Configuraciones específicas por cliente.
    
    Separado de Client para mantener el modelo principal limpio.
    Incluye branding, SEO, redes sociales, etc.
    
    Relación OneToOne: 1 Client = 1 ClientSettings
    """
    
    # ==================== RELACIÓN CON CLIENTE ====================
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,  # Si se borra el cliente, se borran sus settings
        related_name='settings',  # Acceso: client.settings.primary_color
        help_text="Cliente al que pertenecen estas configuraciones"
    )
    
    # ==================== BRANDING ====================
    primary_color = models.CharField(
        max_length=7,
        default='#3B82F6',  # Azul de Tailwind
        help_text="Color primario en formato HEX (ej: #3B82F6)"
    )
    
    secondary_color = models.CharField(
        max_length=7,
        default='#1E40AF',  # Azul oscuro de Tailwind
        help_text="Color secundario en formato HEX"
    )
    
    font_family = models.CharField(
        max_length=100,
        default='Inter, sans-serif',
        help_text="Familia de fuente CSS (ej: 'Roboto, sans-serif')"
    )
    
    # ==================== SEO ====================
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="Título SEO (máx 60 caracteres)"
    )
    
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Descripción SEO (máx 160 caracteres)"
    )
    
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Keywords separadas por comas"
    )
    
    # ==================== ANALYTICS (Fase 2) ====================
    google_analytics_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID de Google Analytics (ej: G-XXXXXXXXXX)"
    )
    
    facebook_pixel_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="ID de Facebook Pixel"
    )
    
    # ==================== REDES SOCIALES ====================
    facebook_url = models.URLField(
        blank=True,
        help_text="URL completa de Facebook (ej: https://facebook.com/empresa)"
    )
    
    instagram_url = models.URLField(
        blank=True,
        help_text="URL completa de Instagram"
    )
    
    twitter_url = models.URLField(
        blank=True,
        help_text="URL completa de Twitter/X"
    )
    
    linkedin_url = models.URLField(
        blank=True,
        help_text="URL completa de LinkedIn"
    )
    
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Número WhatsApp con código país (ej: +56912345678)"
    )
    
    # ==================== FEATURES (Para planes futuros) ====================
    enable_blog = models.BooleanField(
        default=False,
        help_text="Habilitar módulo de blog"
    )
    
    enable_ecommerce = models.BooleanField(
        default=False,
        help_text="Habilitar e-commerce básico"
    )
    
    enable_multilanguage = models.BooleanField(
        default=False,
        help_text="Habilitar soporte multi-idioma"
    )
    
    class Meta:
        verbose_name = 'Configuración del Cliente'
        verbose_name_plural = 'Configuraciones de Clientes'
    
    def __str__(self):
        return f"Settings - {self.client.name}"