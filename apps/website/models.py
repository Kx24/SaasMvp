# =============================================================================
# apps/website/models.py
# =============================================================================
# CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
#
#   - get_section_upload_path / get_service_upload_path ELIMINADOS.
#     Reemplazados por cloudinary_upload_path('resource_type') de cloudinary_utils.
#
#   - CloudinaryField ahora usa folder=cloudinary_upload_path('...') en lugar
#     de upload_to, lo que garantiza la estructura:
#     tenants/{tenant_slug}/{resource_type}/{filename}
#
#   - get_image_url() sin cambios de interfaz — sigue funcionando igual en templates.
#
# PARA AGREGAR NUEVOS MODELOS (Gallery, Catalog, etc.):
#   1. Definir el modelo con CloudinaryField usando cloudinary_upload_path('gallery')
#   2. Si tiene video Cloudinary: CloudinaryField('video', resource_type='video', folder=...)
#   3. Si tiene video externo (YouTube/Vimeo): URLField normal
#   4. No tocar cloudinary_utils.py ni cloudinary_tags.py — ya soportan los nuevos tipos.
# =============================================================================

from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField

from apps.tenants.managers import TenantAwareManager
from apps.core.cloudinary_utils import cloudinary_upload_path


# =============================================================================
# SECTION MODEL
# =============================================================================

class Section(models.Model):
    """
    Secciones de contenido editables del sitio.

    Cada cliente tiene un conjunto fijo de secciones predefinidas.
    No se crean secciones arbitrarias - solo se editan las existentes.

    Estructura en Cloudinary: tenants/{slug}/sections/
    """

    SECTION_TYPES = [
        ('hero',    'Hero / Banner Principal'),
        ('about',   'Sobre Nosotros'),
        ('service', 'Servicio Individual'),
        ('contact', 'Contacto'),
    ]

    # --- CORE ---
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

    # --- CONTENIDO ---
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)

    # --- MULTIMEDIA ---
    # Las imágenes se guardan en: tenants/{tenant_slug}/sections/
    image = CloudinaryField(
        'image',
        folder=cloudinary_upload_path('sections'),
        blank=True,
        null=True,
        help_text="Imagen de la sección → Cloudinary: tenants/{slug}/sections/"
    )

    # --- CONFIGURACIÓN ---
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # --- METADATA ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- MANAGER ---
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
        if not self.order:
            from django.db.models import Max
            max_order = Section.objects.filter(client=self.client).aggregate(
                Max('order')
            )['order__max']
            self.order = (max_order or 0) + 10
        super().save(*args, **kwargs)

    def get_image_url(self, preset='hero'):
        """
        Retorna URL de imagen con transformaciones aplicadas.

        Args:
            preset: Nombre del preset ('hero', 'thumbnail', 'about', 'og_image', etc.)

        Returns:
            URL de Cloudinary transformada o placeholder
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

    Estructura en Cloudinary: tenants/{slug}/services/
    """

    # --- CORE ---
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        related_name='services'
    )

    # --- CONTENIDO ---
    name = models.CharField(max_length=200)

    slug = models.SlugField(
        max_length=250,
        blank=True,
        help_text="URL amigable (se genera automáticamente)"
    )

    description = models.TextField(help_text="Descripción breve del servicio")

    full_description = models.TextField(
        blank=True,
        default='',
        help_text="Descripción completa del servicio"
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        default='⚡',
        help_text="Emoji o clase de icono (ej: 'fa-bolt')"
    )

    # --- MULTIMEDIA ---
    # Las imágenes se guardan en: tenants/{tenant_slug}/services/
    image = CloudinaryField(
        'image',
        folder=cloudinary_upload_path('services'),
        blank=True,
        null=True,
        help_text="Imagen del servicio → Cloudinary: tenants/{slug}/services/"
    )

    # --- PRICING ---
    price_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: 'Desde $50.000' o 'Consultar precio'"
    )

    # --- CONFIGURACIÓN ---
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    # --- METADATA ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- MANAGER ---
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
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Service.objects.filter(
                client=self.client, slug=slug
            ).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if not self.order:
            from django.db.models import Max
            max_order = Service.objects.filter(client=self.client).aggregate(
                Max('order')
            )['order__max']
            self.order = (max_order or 0) + 10

        super().save(*args, **kwargs)

    def get_image_url(self, preset='service_card'):
        """
        Retorna URL de imagen con transformaciones aplicadas.

        Presets recomendados: 'service_card', 'service_detail', 'thumbnail'
        """
        if not self.image:
            return '/static/img/placeholder-service.jpg'
        from apps.core.cloudinary_utils import get_cloudinary_url
        return get_cloudinary_url(self.image, preset)


# =============================================================================
# CONTACT SUBMISSION MODEL
# =============================================================================

class ContactSubmission(models.Model):
    """
    Mensajes de contacto recibidos del formulario del sitio.
    Sin cambios respecto a la versión anterior.
    """

    STATUS_CHOICES = [
        ('new',     'Nuevo'),
        ('read',    'Leído'),
        ('replied', 'Respondido'),
        ('spam',    'Spam'),
    ]

    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        related_name='contact_submissions'
    )

    name    = models.CharField(max_length=200)
    email   = models.EmailField()
    phone   = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=300, blank=True)
    message = models.TextField()

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='new'
    )
    source     = models.CharField(max_length=50, default='website')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
        self.status = 'read'
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_replied(self):
        self.status = 'replied'
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_spam(self):
        self.status = 'spam'
        self.save(update_fields=['status', 'updated_at'])


# =============================================================================
# EJEMPLO: MODELOS FUTUROS
# Copiar este bloque como base para nuevas secciones.
# =============================================================================

# class GalleryItem(models.Model):
#     """
#     Ítem de galería de fotos del cliente.
#     Estructura en Cloudinary: tenants/{slug}/gallery/
#     """
#     client  = models.ForeignKey('tenants.Client', on_delete=models.CASCADE, related_name='gallery')
#     title   = models.CharField(max_length=200, blank=True)
#     caption = models.TextField(blank=True)
#     order   = models.PositiveIntegerField(default=0)
#
#     image = CloudinaryField(
#         'image',
#         folder=cloudinary_upload_path('gallery'),
#         blank=True, null=True,
#     )
#
#     objects = TenantAwareManager()
#
#     def get_image_url(self, preset='gallery_full'):
#         if not self.image:
#             return '/static/img/placeholder.jpg'
#         from apps.core.cloudinary_utils import get_cloudinary_url
#         return get_cloudinary_url(self.image, preset)
#
#     class Meta:
#         ordering = ['order']
#         verbose_name = 'Foto de Galería'


# class CatalogItem(models.Model):
#     """
#     Ítem de catálogo de productos.
#     Estructura en Cloudinary: tenants/{slug}/catalog/
#     """
#     client      = models.ForeignKey('tenants.Client', on_delete=models.CASCADE, related_name='catalog')
#     name        = models.CharField(max_length=200)
#     description = models.TextField(blank=True)
#     price_text  = models.CharField(max_length=100, blank=True)
#     order       = models.PositiveIntegerField(default=0)
#
#     image = CloudinaryField(
#         'image',
#         folder=cloudinary_upload_path('catalog'),
#         blank=True, null=True,
#     )
#
#     objects = TenantAwareManager()
#
#     def get_image_url(self, preset='catalog_card'):
#         if not self.image:
#             return '/static/img/placeholder.jpg'
#         from apps.core.cloudinary_utils import get_cloudinary_url
#         return get_cloudinary_url(self.image, preset)
#
#     class Meta:
#         ordering = ['order', 'name']
#         verbose_name = 'Producto de Catálogo'