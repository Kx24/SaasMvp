"""
Modelos para el sistema Multi-Tenant con soporte Multi-Dominio.

Arquitectura:
- Client: El tenant/cliente principal
- Domain: Múltiples dominios por cliente (subdominios + custom domains)
- ClientSettings: Configuración de branding, SEO, etc.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.core.validators import MinValueValidator


class Client(models.Model):
    """
    Representa un cliente/tenant del sistema.
    
    Cada cliente puede tener MÚLTIPLES dominios asociados.
    """
    
    # ==================== IDENTIFICACIÓN ====================
    name = models.CharField(
        max_length=100,
        help_text="Nombre interno del cliente (ej: 'Servelec Ingeniería')"
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="Identificador único (ej: 'servelec-ingenieria')"
    )
    
    # ==================== INFORMACIÓN EMPRESA ====================
    company_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre legal/comercial de la empresa"
    )
    
    contact_email = models.EmailField(
        blank=True,
        help_text="Email principal de contacto"
    )
    
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Teléfono de contacto"
    )
    
    # ==================== TEMPLATE ====================
    TEMPLATE_CHOICES = [
        ('electricidad', 'Electricidad/Servicios Técnicos'),
        ('construccion', 'Construcción'),
        ('servicios_profesionales', 'Servicios Profesionales'),
        ('portafolio', 'Portafolio Personal'),
        ('custom', 'Personalizado'),
    ]
    
    template = models.CharField(
        max_length=50,
        choices=TEMPLATE_CHOICES,
        default='custom',
        help_text="Template base aplicado"
    )
    
    # ==================== ESTADO ====================
    is_active = models.BooleanField(
        default=True,
        help_text="Si está inactivo, muestra mensaje de mantenimiento"
    )
    
    setup_completed = models.BooleanField(
        default=False,
        help_text="¿Completó la configuración inicial?"
    )
    
    # ==================== BILLING ====================
    setup_fee_paid = models.BooleanField(
        default=False,
        help_text="¿Pagó el fee de setup?"
    )
    
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Tarifa mensual en CLP"
    )
    
    last_payment_date = models.DateField(
        null=True,
        blank=True
    )
    
    next_payment_due = models.DateField(
        null=True,
        blank=True
    )
    
    # ==================== LÍMITES ====================
    max_images = models.IntegerField(default=100)
    max_pages = models.IntegerField(default=10)
    max_services = models.IntegerField(default=20)
    
    # ==================== METADATA ====================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, help_text="Notas internas")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return f"{self.name} ({self.slug})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Asegurar company_name tenga valor
        if not self.company_name:
            self.company_name = self.name
            
        super().save(*args, **kwargs)
        
        # Crear ClientSettings si no existe
        if not hasattr(self, 'settings'):
            ClientSettings.objects.create(client=self)
            
        # AGREGAR: Crear ClientEmailSettings si no existe
        if not hasattr(self, 'email_settings'):
            from .models import ClientEmailSettings  # Import local para evitar circular
            ClientEmailSettings.objects.create(client=self)
    
    @property
    def primary_domain(self):
        """Retorna el dominio primario del cliente"""
        domain = self.domains.filter(is_primary=True, is_active=True).first()
        if not domain:
            domain = self.domains.filter(is_active=True).first()
        return domain
    
    @property
    def all_domains(self):
        """Lista de todos los dominios activos"""
        return list(self.domains.filter(is_active=True).values_list('domain', flat=True))
    
    def get_absolute_url(self):
        """URL del sitio del cliente"""
        if self.primary_domain:
            return f"https://{self.primary_domain.domain}"
        return None


class Domain(models.Model):
    """
    Dominios asociados a un cliente.
    
    Permite:
    - Múltiples dominios por cliente
    - Subdominios (cliente.tuapp.cl)
    - Dominios personalizados (www.cliente.com)
    - Marcar dominio primario
    """
    
    DOMAIN_TYPE_CHOICES = [
        ('subdomain', 'Subdominio (*.tuapp.cl)'),
        ('custom', 'Dominio Personalizado'),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='domains',
        help_text="Cliente al que pertenece este dominio"
    )
    
    domain = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Dominio completo (ej: cliente.tuapp.cl o www.cliente.com)"
    )
    
    domain_type = models.CharField(
        max_length=20,
        choices=DOMAIN_TYPE_CHOICES,
        default='subdomain'
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text="¿Es el dominio principal? (usado en emails, SEO, etc.)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿Está activo este dominio?"
    )
    
    ssl_enabled = models.BooleanField(
        default=True,
        help_text="¿SSL configurado?"
    )
    
    # Verificación de dominio (para custom domains)
    is_verified = models.BooleanField(
        default=False,
        help_text="¿Dominio verificado? (DNS configurado)"
    )
    
    verification_token = models.CharField(
        max_length=64,
        blank=True,
        help_text="Token para verificación DNS"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', 'domain']
        verbose_name = 'Dominio'
        verbose_name_plural = 'Dominios'
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['client', 'is_active']),
        ]
    
    def __str__(self):
        primary = " (primario)" if self.is_primary else ""
        return f"{self.domain}{primary}"
    
    def save(self, *args, **kwargs):
        # Si es el primer dominio del cliente, hacerlo primario
        if not self.pk:
            if not self.client.domains.exists():
                self.is_primary = True
        
        # Si se marca como primario, desmarcar los demás
        if self.is_primary:
            Domain.objects.filter(
                client=self.client, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        
        # Auto-detectar tipo de dominio
        from django.conf import settings
        base_domain = getattr(settings, 'BASE_DOMAIN', 'tuapp.cl')
        if self.domain.endswith(f'.{base_domain}'):
            self.domain_type = 'subdomain'
            self.is_verified = True  # Subdominios propios están verificados
        else:
            self.domain_type = 'custom'
        
        super().save(*args, **kwargs)
    
    def generate_verification_token(self):
        """Genera un token único para verificación DNS"""
        import secrets
        self.verification_token = secrets.token_hex(32)
        self.save(update_fields=['verification_token'])
        return self.verification_token


class ClientSettings(models.Model):
    """
    Configuraciones de branding, SEO y features por cliente.
    """
    
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # ==================== BRANDING ====================
    company_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Nombre a mostrar en el sitio"
    )
    
    logo = models.ImageField(
        upload_to='clients/logos/',
        blank=True,
        null=True
    )
    
    favicon = models.ImageField(
        upload_to='clients/favicons/',
        blank=True,
        null=True
    )
    
    primary_color = models.CharField(
        max_length=7,
        default='#2563eb',
        help_text="Color primario HEX"
    )
    
    secondary_color = models.CharField(
        max_length=7,
        default='#1e40af',
        help_text="Color secundario HEX"
    )
    
    font_family = models.CharField(
        max_length=100,
        default='Inter, sans-serif'
    )
    
    # ==================== CONTACTO ====================
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # ==================== SEO ====================
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # ==================== ANALYTICS ====================
    google_analytics_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)
    
    # ==================== REDES SOCIALES ====================
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # ==================== FEATURES ====================
    enable_blog = models.BooleanField(default=False)
    enable_testimonials = models.BooleanField(default=True)
    enable_contact_form = models.BooleanField(default=True)
    
    # Campo legacy para compatibilidad
    social_media = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Configuración del Cliente'
        verbose_name_plural = 'Configuraciones de Clientes'
    
    def __str__(self):
        return f"Settings - {self.client.name}"
    
    def save(self, *args, **kwargs):
        # Sincronizar company_name con cliente si está vacío
        if not self.company_name and self.client:
            self.company_name = self.client.company_name or self.client.name
        super().save(*args, **kwargs)


# ==================== Configuración de Email ====================

class ClientEmailSettings(models.Model):
    """
    Configuración de email por tenant.
    
    Define cómo cada cliente maneja las notificaciones:
    - SMTP propio (ej: Zoho, Gmail, etc.)
    - Provider externo (SendGrid, Resend, etc.)
    - Solo dashboard (sin email)
    
    El formulario de contacto NO decide nada, solo emite eventos.
    Este modelo define el CONTRATO de cómo se procesan.
    """
    
    # ==================== PROVIDERS ====================
    PROVIDER_CHOICES = [
        ('none', 'Sin email (solo dashboard)'),
        ('smtp', 'SMTP personalizado'),
        ('sendgrid', 'SendGrid'),
        ('resend', 'Resend'),
        ('mailgun', 'Mailgun'),
        ('ses', 'Amazon SES'),
    ]
    
    NOTIFY_MODE_CHOICES = [
        ('dashboard', 'Solo dashboard'),
        ('email', 'Solo email'),
        ('both', 'Dashboard + Email'),
    ]
    
    # ==================== RELACIÓN ====================
    client = models.OneToOneField(
        'Client',
        on_delete=models.CASCADE,
        related_name='email_settings'
    )
    
    # ==================== CONFIGURACIÓN GENERAL ====================
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='none',
        help_text="Proveedor de email a utilizar"
    )
    
    notify_mode = models.CharField(
        max_length=20,
        choices=NOTIFY_MODE_CHOICES,
        default='dashboard',
        help_text="Cómo notificar nuevos contactos"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿Está activo el envío de emails?"
    )
    
    # ==================== SMTP CONFIG ====================
    smtp_host = models.CharField(
        max_length=255,
        blank=True,
        help_text="Servidor SMTP (ej: smtp.zoho.com)"
    )
    
    smtp_port = models.IntegerField(
        default=587,
        help_text="Puerto SMTP (587 para TLS, 465 para SSL)"
    )
    
    smtp_username = models.CharField(
        max_length=255,
        blank=True,
        help_text="Usuario SMTP"
    )
    
    smtp_password = models.CharField(
        max_length=255,
        blank=True,
        help_text="Contraseña SMTP (se almacena encriptada)"
    )
    
    smtp_use_tls = models.BooleanField(
        default=True,
        help_text="Usar TLS (recomendado)"
    )
    
    smtp_use_ssl = models.BooleanField(
        default=False,
        help_text="Usar SSL (alternativa a TLS)"
    )
    
    # ==================== API PROVIDERS ====================
    api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text="API Key para SendGrid, Resend, etc."
    )
    
    # ==================== EMAILS ====================
    from_email = models.EmailField(
        blank=True,
        help_text="Email remitente (ej: contacto@empresa.cl)"
    )
    
    from_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre del remitente (ej: 'Servelec Ingeniería')"
    )
    
    reply_to = models.EmailField(
        blank=True,
        help_text="Email para respuestas (si es diferente del remitente)"
    )
    
    # ==================== DESTINATARIOS ====================
    notify_emails = models.TextField(
        blank=True,
        help_text="Emails a notificar (uno por línea). Si está vacío, usa contact_email del cliente."
    )
    
    # ==================== TEMPLATES ====================
    email_subject_template = models.CharField(
        max_length=200,
        default="Nuevo contacto de {name}",
        help_text="Asunto del email. Variables: {name}, {email}, {subject}"
    )
    
    send_copy_to_sender = models.BooleanField(
        default=False,
        help_text="¿Enviar copia al remitente del formulario?"
    )
    
    # ==================== TESTING ====================
    test_mode = models.BooleanField(
        default=False,
        help_text="Modo prueba: loguea pero no envía emails"
    )
    
    last_test_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Última prueba de conexión"
    )
    
    last_test_success = models.BooleanField(
        default=False,
        help_text="¿Última prueba exitosa?"
    )
    
    last_test_error = models.TextField(
        blank=True,
        help_text="Error de la última prueba"
    )
    
    # ==================== METADATA ====================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Email'
        verbose_name_plural = 'Configuraciones de Email'
    
    def __str__(self):
        return f"Email Settings - {self.client.name} ({self.get_provider_display()})"
    
    def get_notify_emails_list(self):
        """Retorna lista de emails a notificar."""
        if self.notify_emails:
            return [e.strip() for e in self.notify_emails.strip().split('\n') if e.strip()]
        # Fallback al email de contacto del cliente
        if self.client.contact_email:
            return [self.client.contact_email]
        return []
    
    def get_from_email(self):
        """Retorna el email remitente con nombre."""
        email = self.from_email or self.client.contact_email or 'noreply@example.com'
        name = self.from_name or self.client.name
        return f'"{name}" <{email}>'
    
    def can_send_email(self):
        """Verifica si está configurado para enviar emails."""
        if not self.is_active:
            return False
        if self.notify_mode == 'dashboard':
            return False
        if self.provider == 'none':
            return False
        if self.provider == 'smtp' and not all([self.smtp_host, self.smtp_username]):
            return False
        if self.provider in ['sendgrid', 'resend', 'mailgun', 'ses'] and not self.api_key:
            return False
        return True


# ============================================================
# MODIFICAR Client.save() para crear EmailSettings automáticamente
# ============================================================
# En el método save() de Client, agregar después de crear ClientSettings:
#
#     # Crear ClientEmailSettings si no existe
#     if not hasattr(self, 'email_settings'):
#         ClientEmailSettings.objects.create(client=self)




