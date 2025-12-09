"""
Modelos CMS para el website multi-tenant - VERSIÓN CORREGIDA
Todos los campos tienen blank=True y default para evitar errores de migración
"""
from django.db import models
from django.utils.text import slugify

from apps.tenants.models import Client
from apps.core.models import BaseModel
from apps.core.managers import TenantAwareManager


class Section(BaseModel):
    """
    Secciones de página (Hero, About, Services, etc).
    
    Ejemplos:
        - hero: Sección principal
        - about: Quiénes somos
        - services: Resumen de servicios
        - testimonials: Testimonios
    """
    
    # ✅ FOREIGN KEY AL CLIENTE
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='sections',
        help_text="Cliente dueño de esta sección"
    )
    
    slug = models.SlugField(
        max_length=100,
        blank=True,              # ← IMPORTANTE
        default="section",       # ← IMPORTANTE
        help_text="Identificador único: 'hero', 'about', 'services'"
    )
    
    title = models.CharField(
        max_length=200,
        blank=True,              # ← IMPORTANTE
        default="Untitled",      # ← IMPORTANTE
        help_text="Título principal de la sección"
    )
    
    content = models.TextField(
        blank=True,              # ← IMPORTANTE
        default="",              # ← IMPORTANTE
        help_text="Contenido HTML o markdown de la sección"
    )
    
    order = models.IntegerField(
        default=0,
        help_text="Orden de visualización en la página"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Mostrar/ocultar la sección"
    )
    
    # ✅ TENANT-AWARE MANAGER
    objects = TenantAwareManager()
    
    class Meta:
        unique_together = ('client', 'slug')
        ordering = ['order', 'created_at']
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        indexes = [
            models.Index(fields=['client', 'slug']),
            models.Index(fields=['client', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.slug}"
    
    def save(self, *args, **kwargs):
        """Auto-generar slug desde título si no existe"""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Service(BaseModel):
    """
    Servicios ofrecidos por el cliente.
    
    Ejemplos:
        - Consultoría Eléctrica
        - Desarrollo Web
        - Capacitación
    """
    
    # ✅ FOREIGN KEY AL CLIENTE
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='services',
        help_text="Cliente que ofrece este servicio"
    )
    
    name = models.CharField(
        max_length=100,
        blank=True,              # ← IMPORTANTE
        default="Service",       # ← IMPORTANTE
        help_text="Nombre del servicio"
    )
    
    description = models.TextField(
        blank=True,              # ← IMPORTANTE
        default="",              # ← IMPORTANTE
        help_text="Descripción detallada del servicio"
    )
    
    image = models.ImageField(
        upload_to='services/%Y/%m/',
        null=True,
        blank=True,
        help_text="Imagen del servicio (Cloudinary en prod)"
    )
    
    order = models.IntegerField(
        default=0,
        help_text="Orden de visualización"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Mostrar/ocultar el servicio"
    )
    
    # ✅ TENANT-AWARE MANAGER
    objects = TenantAwareManager()
    
    class Meta:
        unique_together = ('client', 'name')
        ordering = ['order', 'created_at']
        verbose_name = "Service"
        verbose_name_plural = "Services"
        indexes = [
            models.Index(fields=['client', 'is_active']),
            models.Index(fields=['client', 'order']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.name}"


class Testimonial(BaseModel):
    """
    Testimonios de clientes para el website.
    """
    
    # ✅ FOREIGN KEY AL CLIENTE
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='testimonials',
        help_text="Cliente que recibe este testimonio"
    )
    
    author = models.CharField(
        max_length=100,
        blank=True,              # ← IMPORTANTE
        default="Anonymous",     # ← IMPORTANTE
        help_text="Nombre de la persona que da el testimonio"
    )
    
    company = models.CharField(
        max_length=100,
        blank=True,              # ← IMPORTANTE
        default="",              # ← IMPORTANTE
        help_text="Empresa de la persona (opcional)"
    )
    
    text = models.TextField(
        blank=True,              # ← IMPORTANTE
        default="Great service!", # ← IMPORTANTE
        help_text="Texto del testimonio"
    )
    
    image = models.ImageField(
        upload_to='testimonials/%Y/%m/',
        null=True,
        blank=True,
        help_text="Foto de la persona"
    )
    
    rating = models.IntegerField(
        default=5,
        choices=[(i, f"{i}⭐") for i in range(1, 6)],
        help_text="Calificación del 1-5"
    )
    
    order = models.IntegerField(
        default=0,
        help_text="Orden de visualización"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Mostrar/ocultar el testimonio"
    )
    
    # ✅ TENANT-AWARE MANAGER
    objects = TenantAwareManager()
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
        indexes = [
            models.Index(fields=['client', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.author}"


class ContactSubmission(BaseModel):
    """
    Formularios de contacto enviados por visitantes.
    """
    
    # ✅ FOREIGN KEY AL CLIENTE
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='contact_submissions',
        help_text="Cliente que recibió este contacto"
    )
    
    name = models.CharField(
        max_length=100,
        blank=True,              # ← IMPORTANTE
        default="Visitor",       # ← IMPORTANTE
        help_text="Nombre del visitante"
    )
    
    email = models.EmailField(
        blank=True,              # ← IMPORTANTE
        default="noreply@example.com", # ← IMPORTANTE
        help_text="Email del visitante"
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",              # ← IMPORTANTE
        help_text="Teléfono del visitante (opcional)"
    )
    
    message = models.TextField(
        blank=True,              # ← IMPORTANTE
        default="",              # ← IMPORTANTE
        help_text="Mensaje del formulario"
    )
    
    is_read = models.BooleanField(
        default=False,
        help_text="¿El cliente leyó el mensaje?"
    )
    
    replied_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cuándo se respondió"
    )
    
    # ✅ TENANT-AWARE MANAGER
    objects = TenantAwareManager()
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['client', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.name} ({self.email})"