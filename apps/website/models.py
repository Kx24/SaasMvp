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
#   + gallery_type: distingue 'hero' (portada) de 'gallery' (sección galería)
#   + is_default:   marca la imagen seed provista al entregar el sitio.
#                   Siempre disponible como fallback — no depende de is_active.
#                   Protegida contra eliminación en la vista del dashboard.
#
# MIGRACIÓN: no destructiva. Los GalleryItem existentes quedan con
#   gallery_type='gallery' (default) e is_default=False (default).
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
        ('gallery', 'Galería de Imágenes'), 
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

    background_image = CloudinaryField(
        'background_image',
        folder=cloudinary_upload_path('sections'),
        blank=True,
        null=True,
        help_text='Imagen de fondo del hero → Cloudinary: tenants/{slug}/sections/',
        )

    # --- CONFIGURACIÓN ---
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    SLOT_KEY_CHOICES = [
        ('hero',    'Hero / Portada'),
        ('gallery', 'Galería de imágenes'),
        ('profile', 'Perfil / Profesionales'),
        ('empty',   'Sin overlay'),
    ]

    slot_key = models.CharField(
        max_length=50,
        choices=SLOT_KEY_CHOICES,
        default='empty',
        help_text='Define qué slot de contenido se renderiza sobre las imágenes.',
    )

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
    
    def get_background_image_url(self, preset='hero'):
        if not self.background_image:
            return None
        from apps.core.cloudinary_utils import get_cloudinary_url
        return get_cloudinary_url(self.background_image, preset)


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
# INSTRUCCIONES DE INTEGRACIÓN:
#
#   Reemplaza SOLO la clase ContactSubmission en tu models.py actual.
#   Los modelos Section, Service y el bloque de ejemplos NO cambian.
#
# CAMBIOS:
#   + form_source:  choices controlados (hero/footer/page/modal)
#   + is_spam:      bool, marcado por honeypot — no elimina, oculta
#   + subject:      ya existía, ahora lo genera el form automáticamente
#   + mark_as_spam: ya existía, ahora también setea is_spam=True
#   + Índice nuevo: (client, is_spam) para queries del dashboard
# =============================================================================
 
 
class ContactSubmission(models.Model):
    """
    Mensajes de contacto recibidos del formulario del sitio.
 
    form_source identifica desde qué sección llegó el mensaje.
    is_spam es seteado por el honeypot del form — el registro se conserva
    para auditoría pero no aparece en el dashboard normal.
    """
 
    STATUS_CHOICES = [
        ('new',     'Nuevo'),
        ('read',    'Leído'),
        ('replied', 'Respondido'),
        ('spam',    'Spam'),
    ]
 
    FORM_SOURCE_CHOICES = [
        ('hero',   'Hero / Banner principal'),
        ('footer', 'Footer del sitio'),
        ('page',   'Página de contacto'),
        ('modal',  'Modal emergente'),
    ]
 
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        related_name='contact_submissions'
    )
 
    # --- DATOS DEL USUARIO ---
    name    = models.CharField(max_length=200)
    email   = models.EmailField()
    phone   = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=300, blank=True)
    message = models.TextField()
 
    # --- ESTADO Y ORIGEN ---
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
 
    # Campo legacy — conservado para compatibilidad
    source = models.CharField(max_length=50, default='website')
 
    # Nuevo: origen específico dentro del sitio
    form_source = models.CharField(
        max_length=20,
        choices=FORM_SOURCE_CHOICES,
        default='page',
        help_text='Sección del sitio desde donde se envió el formulario'
    )
 
    # Nuevo: marcado por honeypot
    is_spam = models.BooleanField(
        default=False,
        help_text='Marcado como spam por el honeypot. Conservado para auditoría.'
    )
 
    # --- METADATA TÉCNICA ---
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
            models.Index(fields=['client', 'is_spam']),   # nuevo
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
        """Marca como spam manual desde el dashboard."""
        self.status = 'spam'
        self.is_spam = True
        self.save(update_fields=['status', 'is_spam', 'updated_at'])

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


class GalleryItem(models.Model):
    """
    Ítem de imagen para portada (hero) o galería de sección.
 
    gallery_type distingue el uso:
      'hero'    → slideshow de fondo en la portada del sitio
      'gallery' → sección galería de la página
 
    is_default=True marca la imagen seed entregada al provisionar el sitio.
    Esta imagen siempre está disponible como fallback del hero,
    independientemente de is_active. El cliente puede ocultarla
    (is_active=False) pero no eliminarla desde el dashboard.
 
    Los límites de imágenes por tipo se controlan desde:
      ClientSettings.hero_images_limit    (default: 3)
      ClientSettings.gallery_images_limit (default: 20)
 
    Estructura en Cloudinary: tenants/{slug}/gallery/
 
    Uso en template — portada:
        {% get_hero_images as hero_items %}
        Hero slideshow con hero_items, fallback al default si está vacío.
 
    Uso en template — galería:
        {% get_gallery as gallery_items %}
        {% include 'components/hero_gallery.html' with items=gallery_items mode="gallery" layout="grid" %}
    """
 
    GALLERY_TYPE_CHOICES = [
        ('hero',    'Portada del sitio'),
        ('gallery', 'Galería de imágenes'),
    ]
 
    # --- CORE ---
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        related_name='gallery',
        verbose_name='Cliente',
    )
 
    # --- TIPO ---
    gallery_type = models.CharField(
        max_length=20,
        choices=GALLERY_TYPE_CHOICES,
        default='gallery',
        verbose_name='Tipo',
        help_text='Portada: imagen de fondo del hero. Galería: sección de imágenes.',
    )
 
    is_default = models.BooleanField(
        default=False,
        verbose_name='Imagen por defecto',
        help_text='Imagen seed entregada al provisionar el sitio. '
                  'Siempre disponible como fallback. No eliminable desde el dashboard.',
    )
 
    # --- CONTENIDO ---
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Título',
        help_text='Título opcional visible en la galería o sobre la imagen.',
    )
 
    caption = models.TextField(
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción breve visible bajo la imagen o en overlay.',
    )
 
    # --- MULTIMEDIA ---
    image = CloudinaryField(
        'Imagen',
        folder=cloudinary_upload_path('gallery'),
        blank=False,
        null=False,
        help_text='Imagen → Cloudinary: tenants/{slug}/gallery/',
    )


    # --- CONFIGURACIÓN ---
    cta_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Texto del botón',
        help_text='Ej: "Solicitar cotización", "Ver servicios". Solo aplica en portada.',
        )

    cta_url = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='URL del botón',
        help_text='Ancla interna: "#contacto". URL relativa: "/servicios/". '
                'URL externa: "https://...". Vacío = botón no se renderiza.',
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Menor número aparece primero.',
    )
 
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa',
        help_text='Desactiva para ocultar esta imagen sin eliminarla.',
    )
 
    # --- METADATA ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creado')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Actualizado')
 
    # --- MANAGER ---
    objects = TenantAwareManager()
 
    class Meta:
        ordering = ['gallery_type', 'order', 'created_at']
        verbose_name = 'Imagen'
        verbose_name_plural = 'Imágenes del sitio'
        indexes = [
            models.Index(fields=['client', 'gallery_type', 'is_active']),
            models.Index(fields=['client', 'gallery_type', 'order']),
            models.Index(fields=['client', 'is_default']),
        ]
 
    def __str__(self):
        tipo = self.get_gallery_type_display()
        label = self.title if self.title else f'Imagen #{self.pk}'
        default_tag = ' [default]' if self.is_default else ''
        return f"{self.client.name} — {tipo} — {label}{default_tag}"
 
    def save(self, *args, **kwargs):
        # Auto-asignar order al final dentro del mismo tipo si no se especifica
        if not self.order:
            from django.db.models import Max
            max_order = GalleryItem.objects.filter(
                client=self.client,
                gallery_type=self.gallery_type,
            ).aggregate(Max('order'))['order__max']
            self.order = (max_order or 0) + 10
        super().save(*args, **kwargs)
 
    def get_image_url(self, preset='gallery_card'):
        """
        Retorna URL de imagen con transformaciones Cloudinary aplicadas.
 
        Args:
            preset: 'gallery_card'  → 800×600, fill, auto quality  (grillas)
                    'gallery_full'  → 1920×1080, limit, auto quality (hero/lightbox)
                    'thumbnail'     → tamaño reducido (dashboard, previews)
 
        Returns:
            URL transformada de Cloudinary o placeholder estático
        """
        if not self.image:
            return '/static/img/placeholder-gallery.jpg'
        from apps.core.cloudinary_utils import get_cloudinary_url
        return get_cloudinary_url(self.image, preset)