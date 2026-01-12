# =============================================================================
# apps/website/models.py - ACTUALIZADO CON CLOUDINARY
# =============================================================================
# Card C2: Migración de ImageField a CloudinaryField
# 
# CAMBIOS:
# - ImageField → CloudinaryField
# - upload_to ahora usa función que incluye tenant slug
# - Eliminado modelo Testimonial (según indicación)
# =============================================================================

from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from apps.tenants.managers import TenantAwareManager


# =============================================================================
# HELPERS PARA CLOUDINARY
# =============================================================================

def get_section_upload_path(instance, filename):
    """
    Genera path de upload para Section incluyendo tenant slug.
    Resultado: {tenant_slug}/sections/{filename}
    """
    return f"{instance.client.slug}/sections/{filename}"


def get_service_upload_path(instance, filename):
    """
    Genera path de upload para Service incluyendo tenant slug.
    Resultado: {tenant_slug}/services/{filename}
    """
    return f"{instance.client.slug}/services/{filename}"


# =============================================================================
# SECTION MODEL
# =============================================================================

class Section(models.Model):
    """
    Secciones de contenido editables del sitio.
    
    Cada cliente tiene un conjunto fijo de secciones predefinidas.
    No se crean secciones arbitrarias - solo se editan las existentes.
    """
    
    # Secciones predefinidas disponibles
    SECTION_TYPES = [
        ('hero', 'Hero / Banner Principal'),
        ('about', 'Sobre Nosotros'),
        ('service', 'Servicio Individual'),
        ('contact', 'Contacto'),
    ]
    
    # === CAMPOS CORE ===
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        related_name='sections'
    )
    
    section_type = models.CharField(
        max_length=50,
        choices=SECTION_TYPES,
        help_text="Tipo de sección (predefinido)"
    )
    
    # === CONTENIDO ===
    title = models.CharField(
        max_length=200,
        help_text="Título principal de la sección"
    )
    
    subtitle = models.CharField(
        max_length=300,
        blank=True,
        help_text="Subtítulo o tagline (opcional)"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Descripción larga (para about, generic, etc.)"
    )
    
    # === MULTIMEDIA - CLOUDINARY ===
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        help_text="Imagen de la sección (se sube a Cloudinary)"
    )
    
    # === CONFIGURACIÓN ===
    order = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿Mostrar esta sección en el sitio?"
    )
    
    # === METADATA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # === MANAGER ===
    objects = TenantAwareManager()
    
    class Meta:
        unique_together = [['client', 'section_type']]
        ordering = ['order', 'section_type']
        verbose_name = 'Sección'
        verbose_name_plural = 'Secciones'
        indexes = [
            models.Index(fields=['client', 'section_type']),
            models.Index(fields=['client', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.get_section_type_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-asignar order si no está definido
        if not self.order:
            max_order = Section.objects.filter(client=self.client).aggregate(
                models.Max('order')
            )['order__max']
            self.order = (max_order or 0) + 10
        
        super().save(*args, **kwargs)
    
    def get_image_url(self, preset='hero'):
        """
        Retorna URL de imagen con transformaciones aplicadas.
        
        Args:
            preset: Nombre del preset ('hero', 'thumbnail', etc.)
        
        Returns:
            URL de Cloudinary con transformaciones o placeholder
        """
        if not self.image:
            return '/static/img/placeholder-section.jpg'
        
        from apps.core.cloudinary_utils import get_cloudinary_url
        return get_cloudinary_url(self.image, preset)


# =============================================================================
# SERVICE MODEL
# =============================================================================

class Service(models.Model):
    """
    Servicios ofrecidos por el cliente.
    
    Cada cliente puede tener múltiples servicios.
    Se muestran como cards/tarjetas en el sitio.
    """
    
    # === CAMPOS CORE ===
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        related_name='services'
    )
    
    # === CONTENIDO ===
    name = models.CharField(
        max_length=200,
        help_text="Nombre del servicio"
    )
    
    slug = models.SlugField(
        max_length=250,
        blank=True,
        help_text="URL amigable (se genera automáticamente)"
    )
    
    description = models.TextField(
        help_text="Descripción breve del servicio"
    )

    full_description = models.TextField(
        blank=True,
        default='',
        help_text="Descripción completa del servicio"
    )
       
    # === VISUAL ===
    icon = models.CharField(
        max_length=50,
        default='⚡',
        help_text="Emoji o clase de icono (ej: 'fa-bolt')"
    )
    
    # === MULTIMEDIA - CLOUDINARY ===
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        help_text="Imagen del servicio (se sube a Cloudinary)"
    )
    # === PRICING (opcional para el futuro) ===
    price_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: 'Desde $50.000' o 'Consultar precio'"
    )
    
    # === CONFIGURACIÓN ===
    order = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="¿Mostrar este servicio?"
    )
    
    is_featured = models.BooleanField(
        default=False,
        help_text="¿Es un servicio destacado?"
    )
    
    # === METADATA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # === MANAGER ===
    objects = TenantAwareManager()
    
    class Meta:
        unique_together = [['client', 'slug']]
        ordering = ['order', 'name']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        indexes = [
            models.Index(fields=['client', 'slug']),
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['client', 'is_featured']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Auto-generar slug único si no existe
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Asegurar que el slug sea único para este cliente
            while Service.objects.filter(
                client=self.client, 
                slug=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        # Auto-asignar order si no está definido
        if not self.order:
            max_order = Service.objects.filter(client=self.client).aggregate(
                models.Max('order')
            )['order__max']
            self.order = (max_order or 0) + 10
        
        super().save(*args, **kwargs)
    
    def get_image_url(self, preset='service_card'):
        """
        Retorna URL de imagen con transformaciones aplicadas.
        """
        if not self.image:
            return '/static/img/placeholder-service.jpg'
        
        from apps.core.cloudinary_utils import get_cloudinary_url
        return get_cloudinary_url(self.image, preset)


# =============================================================================
# CONTACT SUBMISSION MODEL (sin cambios)
# =============================================================================

class ContactSubmission(models.Model):
    """
    Mensajes de contacto recibidos del formulario del sitio.
    """
    
    STATUS_CHOICES = [
        ('new', 'Nuevo'),
        ('read', 'Leído'),
        ('replied', 'Respondido'),
        ('spam', 'Spam'),
    ]
    
    # === CAMPOS CORE ===
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        related_name='contact_submissions'
    )
    
    # === INFORMACIÓN DEL CONTACTO ===
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)
    
    # === MENSAJE ===
    subject = models.CharField(
        max_length=300,
        blank=True,
        help_text="Asunto del mensaje"
    )
    
    message = models.TextField(help_text="Mensaje del contacto")
    
    # === METADATA ===
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    
    source = models.CharField(
        max_length=50,
        default='website',
        help_text="Origen: website, landing, form, etc."
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP del visitante"
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text="Navegador del visitante"
    )
    
    # === TIMESTAMPS ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # === MANAGER ===
    objects = TenantAwareManager()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mensaje de Contacto'
        verbose_name_plural = 'Mensajes de Contacto'
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['client', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.created_at.strftime('%d/%m/%Y')}"
    
    def mark_as_read(self):
        """Marcar mensaje como leído"""
        self.status = 'read'
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_as_replied(self):
        """Marcar mensaje como respondido"""
        self.status = 'replied'
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_as_spam(self):
        """Marcar mensaje como spam"""
        self.status = 'spam'
        self.save(update_fields=['status', 'updated_at'])
