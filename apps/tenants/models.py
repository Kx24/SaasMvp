"""
Modelos para el sistema Multi-Tenant con soporte Multi-Dominio.

Arquitectura:
- Client: El tenant/cliente principal
- Domain: Múltiples dominios por cliente (subdominios + custom domains)
- ClientSettings: Configuración de branding, SEO, etc.
- ClientEmailSettings: Configuración de email por tenant
- FormConfig: Configuración de formulario de contacto por tenant
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.core.validators import MinValueValidator


# ==============================================================================
# CLIENT - Modelo principal del tenant
# ==============================================================================

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
        # Auto-generar slug si no existe
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Asegurar company_name tenga valor
        if not self.company_name:
            self.company_name = self.name
            
        # Guardar el cliente primero
        super().save(*args, **kwargs)
        
        # NO crear settings aquí - lo hace signals.py
        # Esto evita duplicación
    
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


# ==============================================================================
# DOMAIN - Dominios asociados a un cliente
# ==============================================================================

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
        else:
            self.domain_type = 'custom'
        
        super().save(*args, **kwargs)


# ==============================================================================
# CLIENT SETTINGS - Configuración de branding y SEO
# ==============================================================================

class ClientSettings(models.Model):
    """
    Configuración y branding del cliente.
    
    OneToOne con Client - cada cliente tiene exactamente una configuración.
    """
    
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    
    # ==================== BRANDING ====================
    logo = models.ImageField(
        upload_to='clients/logos/',
        blank=True,
        null=True,
        verbose_name='Logo principal'
    )
    logo_footer = models.ImageField(
        upload_to='clients/logos/',
        blank=True,
        null=True,
        verbose_name='Logo footer (blanco)',
        help_text='Logo alternativo para el footer, preferiblemente en blanco'
    )
    favicon = models.ImageField(
        upload_to='clients/favicons/',
        blank=True,
        null=True,
        verbose_name='Favicon'
    )

    primary_color = models.CharField(max_length=7, default='#3B82F6')
    secondary_color = models.CharField(max_length=7, default='#1E40AF')
    font_family = models.CharField(max_length=100, default='Inter, sans-serif')
    
    # ==================== INFORMACIÓN ====================
    company_name = models.CharField(max_length=200, blank=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
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


# ==============================================================================
# CLIENT EMAIL SETTINGS - Configuración de email
# ==============================================================================

class ClientEmailSettings(models.Model):
    """
    Configuración de email por tenant.
    
    Define cómo cada cliente maneja las notificaciones:
    - SMTP propio (ej: Zoho, Gmail, etc.)
    - Provider externo (SendGrid, Resend, etc.)
    - Solo dashboard (sin email)
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
        Client,
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


# ==============================================================================
# FORM CONFIG - Configuración de formulario de contacto
# ==============================================================================

class FormConfig(models.Model):
    """
    Configuración del formulario de contacto por tenant.
    
    Cada tenant puede activar/desactivar campos y personalizarlos.
    """
    
    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='form_config'
    )
    
    # ==================== CAMPOS BÁSICOS (siempre visibles) ====================
    # Nombre - siempre requerido
    name_label = models.CharField(
        max_length=50, 
        default='Nombre completo',
        help_text="Etiqueta del campo nombre"
    )
    name_placeholder = models.CharField(
        max_length=100, 
        default='Tu nombre',
        blank=True
    )
    
    # Email - siempre requerido
    email_label = models.CharField(
        max_length=50, 
        default='Email',
    )
    email_placeholder = models.CharField(
        max_length=100, 
        default='tu@email.com',
        blank=True
    )
    
    # Mensaje - siempre requerido
    message_label = models.CharField(
        max_length=50, 
        default='Mensaje',
    )
    message_placeholder = models.CharField(
        max_length=200, 
        default='¿En qué podemos ayudarte?',
        blank=True
    )
    message_rows = models.IntegerField(
        default=4,
        help_text="Número de filas del textarea"
    )
    
    # ==================== CAMPOS OPCIONALES ====================
    
    # Teléfono
    show_phone = models.BooleanField(default=True, help_text="Mostrar campo teléfono")
    phone_required = models.BooleanField(default=False, help_text="¿Es obligatorio?")
    phone_label = models.CharField(max_length=50, default='Teléfono')
    phone_placeholder = models.CharField(max_length=100, default='+56 9 1234 5678', blank=True)
    
    # Empresa/Compañía
    show_company = models.BooleanField(default=False, help_text="Mostrar campo empresa")
    company_required = models.BooleanField(default=False)
    company_label = models.CharField(max_length=50, default='Empresa')
    company_placeholder = models.CharField(max_length=100, default='Tu empresa', blank=True)
    
    # Asunto (dropdown)
    show_subject = models.BooleanField(default=True, help_text="Mostrar selector de asunto")
    subject_required = models.BooleanField(default=False)
    subject_label = models.CharField(max_length=50, default='Asunto')
    subject_options = models.TextField(
        default='Consulta general\nSolicitar cotización\nSoporte técnico\nOtro',
        help_text="Opciones del dropdown, una por línea"
    )
    
    # Dirección
    show_address = models.BooleanField(default=False, help_text="Mostrar campo dirección")
    address_required = models.BooleanField(default=False)
    address_label = models.CharField(max_length=50, default='Dirección')
    address_placeholder = models.CharField(max_length=100, default='Tu dirección', blank=True)
    
    # Ciudad/Comuna
    show_city = models.BooleanField(default=False, help_text="Mostrar campo ciudad")
    city_required = models.BooleanField(default=False)
    city_label = models.CharField(max_length=50, default='Ciudad/Comuna')
    city_placeholder = models.CharField(max_length=100, default='', blank=True)
    
    # Presupuesto
    show_budget = models.BooleanField(default=False, help_text="Mostrar selector de presupuesto")
    budget_required = models.BooleanField(default=False)
    budget_label = models.CharField(max_length=50, default='Presupuesto estimado')
    budget_options = models.TextField(
        default='Menos de $100.000\n$100.000 - $500.000\n$500.000 - $1.000.000\nMás de $1.000.000\nNo definido',
        help_text="Opciones del dropdown, una por línea",
        blank=True
    )
    
    # Urgencia
    show_urgency = models.BooleanField(default=False, help_text="Mostrar selector de urgencia")
    urgency_required = models.BooleanField(default=False)
    urgency_label = models.CharField(max_length=50, default='Urgencia')
    urgency_options = models.TextField(
        default='Normal\nUrgente\nMuy urgente (24h)',
        help_text="Opciones del dropdown, una por línea",
        blank=True
    )
    
    # Cómo nos conociste
    show_source = models.BooleanField(default=False, help_text="Mostrar ¿Cómo nos conociste?")
    source_required = models.BooleanField(default=False)
    source_label = models.CharField(max_length=50, default='¿Cómo nos conociste?')
    source_options = models.TextField(
        default='Google\nRedes sociales\nRecomendación\nOtro',
        help_text="Opciones del dropdown, una por línea",
        blank=True
    )
    
    # ==================== CONFIGURACIÓN DEL FORMULARIO ====================
    
    submit_button_text = models.CharField(
        max_length=50, 
        default='Enviar mensaje',
        help_text="Texto del botón de envío"
    )
    
    success_message = models.TextField(
        default='¡Gracias por contactarnos! Te responderemos a la brevedad.',
        help_text="Mensaje mostrado después de enviar"
    )
    
    privacy_text = models.CharField(
        max_length=200,
        default='Al enviar, aceptas nuestra política de privacidad.',
        blank=True,
        help_text="Texto de privacidad bajo el botón"
    )
    
    # ==================== METADATA ====================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Formulario'
        verbose_name_plural = 'Configuraciones de Formularios'
    
    def __str__(self):
        return f"FormConfig - {self.client.name}"
    
    def get_subject_options_list(self):
        """Retorna lista de opciones de asunto."""
        if self.subject_options:
            return [opt.strip() for opt in self.subject_options.strip().split('\n') if opt.strip()]
        return []
    
    def get_budget_options_list(self):
        """Retorna lista de opciones de presupuesto."""
        if self.budget_options:
            return [opt.strip() for opt in self.budget_options.strip().split('\n') if opt.strip()]
        return []
    
    def get_urgency_options_list(self):
        """Retorna lista de opciones de urgencia."""
        if self.urgency_options:
            return [opt.strip() for opt in self.urgency_options.strip().split('\n') if opt.strip()]
        return []
    
    def get_source_options_list(self):
        """Retorna lista de opciones de fuente."""
        if self.source_options:
            return [opt.strip() for opt in self.source_options.strip().split('\n') if opt.strip()]
        return []
    
    def get_active_fields(self):
        """Retorna lista de campos activos para el formulario."""
        fields = ['name', 'email']  # Siempre presentes
        
        if self.show_phone:
            fields.append('phone')
        if self.show_company:
            fields.append('company')
        if self.show_subject:
            fields.append('subject')
        if self.show_address:
            fields.append('address')
        if self.show_city:
            fields.append('city')
        if self.show_budget:
            fields.append('budget')
        if self.show_urgency:
            fields.append('urgency')
        if self.show_source:
            fields.append('source')
        
        fields.append('message')  # Siempre al final
        
        return fields