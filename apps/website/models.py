"""
Modelos para el CMS Multi-Tenant.

Este módulo contiene los modelos para gestionar el contenido de las landing pages
de cada cliente. Todos los modelos heredan de una clase base que incluye la
relación con el cliente (tenant) y gestión automática de fechas.

Modelos:
    - Section: Secciones editables de la página (hero, about, services, etc)
    - Service: Servicios ofrecidos por el cliente
    - Testimonial: Testimonios de clientes satisfechos
    - ContactSubmission: Formularios de contacto enviados

Todos los modelos usan TenantAwareManager para filtrado automático por cliente.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from ckeditor.fields import RichTextField
from cloudinary.models import CloudinaryField
from apps.tenants.managers import TenantAwareManager


class TenantAwareModel(models.Model):
    """
    Modelo base abstracto para todos los modelos multi-tenant.
    
    Proporciona:
    - Relación ForeignKey con Client (tenant)
    - Campos de auditoría (created_at, updated_at)
    - Manager personalizado con filtrado automático
    
    Todos los modelos CMS deben heredar de esta clase para garantizar
    el aislamiento de datos entre clientes.
    
    Example:
        class MiModelo(TenantAwareModel):
            nombre = models.CharField(max_length=100)
            
            class Meta:
                verbose_name = 'Mi Modelo'
    """
    
    # ==================== RELACIÓN CON TENANT ====================
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,  # Si se borra el cliente, se borra todo su contenido
        related_name='%(class)s_set',  # Acceso reverso: client.section_set.all()
        verbose_name='Cliente',
        help_text='Cliente al que pertenece este registro'
    )
    
    # ==================== AUDITORÍA ====================
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Creado',
        help_text='Fecha y hora de creación (automático)'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Actualizado',
        help_text='Fecha y hora de última actualización (automático)'
    )
    
    # ==================== MANAGER PERSONALIZADO ====================
    objects = TenantAwareManager()
    
    class Meta:
        abstract = True  # No crear tabla en la base de datos
        ordering = ['-created_at']  # Ordenar por más recientes primero


class Section(TenantAwareModel):
    """
    Secciones editables del sitio web.
    
    Cada cliente puede tener múltiples secciones (hero, about, services, etc).
    Las secciones controlan el contenido de diferentes partes de la landing page.
    
    Tipos de secciones:
        - hero: Banner principal de la página
        - about: Sección "Sobre Nosotros"
        - services: Listado de servicios (contenedor)
        - portfolio: Proyectos/trabajos realizados
        - testimonials: Contenedor de testimonios
        - team: Sección del equipo
        - contact: Información de contacto
        - cta: Call to Action (llamada a la acción)
        - footer: Pie de página
        - custom: Sección personalizada
    
    Cada sección puede tener:
        - Título y subtítulo
        - Contenido HTML enriquecido (via CKEditor)
        - Imagen principal y/o imagen de fondo
        - Botón CTA con texto y URL
        - Control de visibilidad y orden
    
    Example:
        # Crear sección Hero para un cliente
        hero = Section.objects.create(
            client=mi_cliente,
            section_type='hero',
            title='Soluciones Eléctricas Profesionales',
            subtitle='Más de 20 años de experiencia',
            cta_text='Solicitar Cotización',
            cta_url='/contacto'
        )
    """
    
    # ==================== TIPO DE SECCIÓN ====================
    SECTION_TYPES = [
        ('hero', 'Hero / Banner Principal'),
        ('about', 'Sobre Nosotros'),
        ('services', 'Servicios'),
        ('portfolio', 'Portafolio / Proyectos'),
        ('testimonials', 'Testimonios'),
        ('team', 'Equipo'),
        ('contact', 'Contacto'),
        ('cta', 'Llamada a la Acción'),
        ('footer', 'Pie de Página'),
        ('custom', 'Sección Personalizada'),
    ]
    
    section_type = models.CharField(
        max_length=50,
        choices=SECTION_TYPES,
        verbose_name='Tipo de Sección',
        help_text='Tipo de sección de la página'
    )
    
    # ==================== CONTENIDO TEXTUAL ====================
    title = models.CharField(
        max_length=200,
        verbose_name='Título',
        help_text='Título principal de la sección'
    )
    
    subtitle = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Subtítulo',
        help_text='Subtítulo o descripción corta (opcional)'
    )
    
    content = RichTextField(
        blank=True,
        verbose_name='Contenido',
        help_text='Contenido HTML enriquecido (opcional)'
    )
    
    # ==================== IMÁGENES (CLOUDINARY) ====================
    image = CloudinaryField(
        'section_image',
        blank=True,
        null=True,
        help_text='Imagen principal de la sección (se guarda en Cloudinary)'
    )

    background_image = CloudinaryField(
        'section_bg',
        blank=True,
        null=True,
        help_text='Imagen de fondo para la sección (opcional)'
    )
    
    # ==================== CALL TO ACTION (CTA) ====================
    cta_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Texto del Botón',
        help_text='Texto del botón de acción (ej: "Contáctanos", "Ver más")'
    )
    
    cta_url = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='URL del Botón',
        help_text='URL a la que dirige el botón (ej: /contacto, https://wa.me/...)'
    )
    
    # ==================== CONFIGURACIÓN ====================
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está inactivo, no se mostrará en el sitio'
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición (menor = primero). Ej: 0, 10, 20, 30...'
    )
    
    class Meta:
        verbose_name = 'Sección'
        verbose_name_plural = 'Secciones'
        ordering = ['client', 'order', 'section_type']
        
        # Índices para mejorar performance de queries
        indexes = [
            models.Index(fields=['client', 'section_type', 'is_active']),
            models.Index(fields=['client', 'order']),
        ]
        
        # Un cliente solo puede tener UNA sección de cada tipo
        # (evita duplicados: no puede haber 2 "hero" para el mismo cliente)
        unique_together = [['client', 'section_type']]
    
    def __str__(self):
        """Representación en string de la sección"""
        return f"{self.client.company_name} - {self.get_section_type_display()}"


class Service(TenantAwareModel):
    """
    Servicios ofrecidos por el cliente.
    
    Cada cliente puede tener múltiples servicios que ofrece.
    Los servicios se muestran típicamente en cards/tarjetas en el sitio.
    
    Características:
        - Nombre y descripción del servicio
        - Icono (clase CSS) o imagen
        - Precio opcional (desde $X)
        - Destacado (featured) para mostrar primero
        - Control de orden y visibilidad
    
    Example:
        # Crear servicio para empresa eléctrica
        servicio = Service.objects.create(
            client=mi_cliente,
            name='Instalaciones Eléctricas Industriales',
            description='<p>Instalación completa de sistemas eléctricos...</p>',
            icon='fa-bolt',
            price=500000,
            is_featured=True
        )
    """
    
    # ==================== INFORMACIÓN BÁSICA ====================
    name = models.CharField(
        max_length=150,
        verbose_name='Nombre',
        help_text='Nombre del servicio (ej: "Instalaciones Eléctricas")'
    )
    
    description = RichTextField(
        verbose_name='Descripción',
        help_text='Descripción detallada del servicio (HTML enriquecido)'
    )
    
    # ==================== VISUAL ====================
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Clase de Icono',
        help_text='Clase de icono Font Awesome o Lucide (ej: "fa-bolt", "lucide-zap")'
    )
    
    image = CloudinaryField(
        'service_image',
        blank=True,
        null=True,
        help_text='Imagen del servicio (alternativa al icono)'
    )
    
    # ==================== PRECIO ====================
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Precio',
        help_text='Precio del servicio en moneda local (opcional)'
    )
    
    price_label = models.CharField(
        max_length=50,
        blank=True,
        default='Desde',
        verbose_name='Etiqueta del Precio',
        help_text='Texto antes del precio (ej: "Desde", "Por proyecto")'
    )
    
    # ==================== CONFIGURACIÓN ====================
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Destacado',
        help_text='Si está marcado, se mostrará primero o con estilo especial'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está inactivo, no se mostrará en el sitio'
    )
    
    order = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de aparición (menor = primero)'
    )
    
    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['client', 'order', '-is_featured', 'name']
        
        indexes = [
            models.Index(fields=['client', 'is_active', 'is_featured']),
            models.Index(fields=['client', 'order']),
        ]
    
    def __str__(self):
        """Representación en string del servicio"""
        featured = '⭐ ' if self.is_featured else ''
        return f"{featured}{self.client.company_name} - {self.name}"


class Testimonial(TenantAwareModel):
    """
    Testimonios de clientes satisfechos.
    
    Los testimonios son opiniones/reviews de clientes que han usado
    los servicios del cliente. Ayudan a generar confianza.
    
    Características:
        - Nombre y cargo del cliente que da el testimonio
        - Texto del testimonio
        - Rating de 1-5 estrellas
        - Foto opcional del cliente
        - Control de visibilidad
    
    Example:
        # Crear testimonio
        testimonio = Testimonial.objects.create(
            client=mi_cliente,
            client_name='Juan Pérez',
            client_role='Gerente de Operaciones, Empresa XYZ',
            testimonial='Excelente servicio, muy profesionales y puntuales.',
            rating=5
        )
    """
    
    # ==================== CLIENTE QUE DA EL TESTIMONIO ====================
    client_name = models.CharField(
        max_length=100,
        verbose_name='Nombre del Cliente',
        help_text='Nombre de la persona que da el testimonio'
    )
    
    client_role = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Cargo / Empresa',
        help_text='Cargo o empresa del cliente (ej: "Gerente, Empresa ABC")'
    )
    
    client_photo = CloudinaryField(
        'testimonial_photo',
        blank=True,
        null=True,
        help_text='Foto de la persona que da el testimonio (opcional)'
    )
    
    # ==================== TESTIMONIO ====================
    testimonial = models.TextField(
        verbose_name='Testimonio',
        help_text='Texto completo del testimonio'
    )
    
    rating = models.IntegerField(
        default=5,
        validators=[
            MinValueValidator(1, message='El rating mínimo es 1 estrella'),
            MaxValueValidator(5, message='El rating máximo es 5 estrellas')
        ],
        verbose_name='Rating',
        help_text='Calificación de 1 a 5 estrellas'
    )
    
    # ==================== CONFIGURACIÓN ====================
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está inactivo, no se mostrará en el sitio'
    )
    
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Destacado',
        help_text='Testimonios destacados se muestran primero'
    )
    
    class Meta:
        verbose_name = 'Testimonio'
        verbose_name_plural = 'Testimonios'
        ordering = ['client', '-is_featured', '-rating', '-created_at']
        
        indexes = [
            models.Index(fields=['client', 'is_active', 'is_featured']),
        ]
    
    def __str__(self):
        """Representación en string del testimonio"""
        stars = '⭐' * self.rating
        return f"{self.client.company_name} - {self.client_name} ({stars})"
    
    def get_rating_display(self):
        """
        Retorna el rating como string de estrellas.
        
        Returns:
            str: String con estrellas (ej: "⭐⭐⭐⭐⭐")
        """
        return '⭐' * self.rating


class ContactSubmission(TenantAwareModel):
    """
    Formularios de contacto enviados por visitantes.
    
    Cuando un visitante llena el formulario de contacto del sitio,
    los datos se guardan aquí. El cliente puede verlos desde el admin.
    
    Características:
        - Datos del visitante (nombre, email, teléfono)
        - Asunto y mensaje
        - Metadata (IP, user agent, fecha)
        - Estado (leído, spam)
        - Fecha de respuesta (opcional)
    
    Flujo típico:
        1. Visitante llena formulario en el sitio
        2. Datos se guardan en ContactSubmission
        3. Se envía email al cliente (opcional)
        4. Cliente ve el formulario en /admin/
        5. Cliente marca como "leído" después de responder
    
    Example:
        # Crear formulario de contacto
        submission = ContactSubmission.objects.create(
            client=mi_cliente,
            name='María González',
            email='maria@example.com',
            phone='+56912345678',
            subject='Cotización de servicios',
            message='Necesito cotizar instalación eléctrica...',
            ip_address='192.168.1.1'
        )
    """
    
    # ==================== DATOS DEL VISITANTE ====================
    name = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre completo del visitante'
    )
    
    email = models.EmailField(
        verbose_name='Email',
        help_text='Email de contacto del visitante'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Teléfono',
        help_text='Teléfono de contacto (opcional)'
    )
    
    # ==================== MENSAJE ====================
    subject = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Asunto',
        help_text='Asunto del mensaje (opcional)'
    )
    
    message = models.TextField(
        verbose_name='Mensaje',
        help_text='Mensaje completo del visitante'
    )
    
    # ==================== METADATA ====================
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Envío',
        help_text='Fecha y hora en que se envió el formulario'
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='Dirección IP',
        help_text='Dirección IP del visitante (para seguridad)'
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent',
        help_text='Navegador y sistema operativo del visitante'
    )
    
    # ==================== ESTADO ====================
    is_read = models.BooleanField(
        default=False,
        verbose_name='Leído',
        help_text='Marca como leído cuando el cliente lo revise'
    )
    
    is_spam = models.BooleanField(
        default=False,
        verbose_name='Spam',
        help_text='Marca como spam si es un mensaje no deseado'
    )
    
    replied_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Respondido',
        help_text='Fecha y hora en que se respondió al cliente (opcional)'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Notas Internas',
        help_text='Notas privadas sobre este contacto (no visibles para el visitante)'
    )
    
    class Meta:
        verbose_name = 'Formulario de Contacto'
        verbose_name_plural = 'Formularios de Contacto'
        ordering = ['client', '-submitted_at']
        
        indexes = [
            models.Index(fields=['client', 'is_read', 'is_spam']),
            models.Index(fields=['client', '-submitted_at']),
        ]
    
    def __str__(self):
        """Representación en string del formulario"""
        status = '✉️' if not self.is_read else '✅'
        spam = ' [SPAM]' if self.is_spam else ''
        return f"{status} {self.client.company_name} - {self.name}{spam}"
    
    def mark_as_read(self):
        """
        Marca el formulario como leído.
        
        Útil para llamar desde el admin o una vista.
        """
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    def mark_as_spam(self):
        """
        Marca el formulario como spam.
        
        Los formularios marcados como spam se pueden ocultar en el admin.
        """
        self.is_spam = True
        self.save(update_fields=['is_spam'])