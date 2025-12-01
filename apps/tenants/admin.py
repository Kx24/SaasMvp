"""
Configuración del Django Admin para gestión de clientes/tenants.

Solo los superusuarios pueden ver y gestionar clientes.
Los usuarios normales (clientes) no tienen acceso a esta sección.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Client, ClientSettings


class ClientSettingsInline(admin.StackedInline):
    """
    Inline para editar ClientSettings directamente desde Client.
    
    Esto permite editar la configuración del cliente
    sin tener que ir a otra página.
    """
    model = ClientSettings
    can_delete = False
    verbose_name = 'Configuración'
    verbose_name_plural = 'Configuración'
    
    # Organizar campos en secciones
    fieldsets = (
        ('Branding', {
            'fields': ('primary_color', 'secondary_color', 'font_family'),
            'description': 'Colores y tipografía del sitio'
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',),  # Colapsado por default
            'description': 'Optimización para motores de búsqueda'
        }),
        ('Redes Sociales', {
            'fields': (
                'facebook_url',
                'instagram_url',
                'twitter_url',
                'linkedin_url',
                'whatsapp_number'
            ),
            'classes': ('collapse',),
        }),
        ('Analytics', {
            'fields': ('google_analytics_id', 'facebook_pixel_id'),
            'classes': ('collapse',),
        }),
        ('Features', {
            'fields': ('enable_blog', 'enable_ecommerce', 'enable_multilanguage'),
            'classes': ('collapse',),
            'description': 'Funcionalidades adicionales (próximamente)'
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Administración de Clientes/Tenants.
    
    Muestra información clave y permite gestionar todos
    los aspectos de un cliente desde una sola interfaz.
    """
    
    # ==================== INLINE ====================
    inlines = [ClientSettingsInline]
    
    # ==================== LISTA ====================
    list_display = [
        'company_name',
        'domain_link',
        'template',
        'status_badge',
        'payment_status',
        'created_at',
    ]
    
    list_filter = [
        'template',
        'is_active',
        'setup_completed',
        'setup_fee_paid',
        'created_at',
    ]
    
    search_fields = [
        'company_name',
        'domain',
        'contact_email',
        'notes',
    ]
    
    # Ordenar por más recientes primero
    ordering = ['-created_at']
    
    # Campos de solo lectura
    readonly_fields = ['slug', 'created_at', 'updated_at']
    
    # ==================== FORMULARIO ====================
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'name',
                'slug',
                'domain',
                'company_name',
            )
        }),
        ('Contacto', {
            'fields': (
                'contact_email',
                'contact_phone',
            )
        }),
        ('Configuración del Sitio', {
            'fields': (
                'template',
                'is_active',
                'setup_completed',
            )
        }),
        ('Billing', {
            'fields': (
                'setup_fee_paid',
                'monthly_fee',
                'last_payment_date',
                'next_payment_due',
            ),
            'description': 'Gestión de pagos (manual por ahora)'
        }),
        ('Límites', {
            'fields': (
                'max_images',
                'max_pages',
            ),
            'classes': ('collapse',),
            'description': 'Límites según el plan del cliente'
        }),
        ('Notas Internas', {
            'fields': ('notes',),
            'classes': ('collapse',),
            'description': 'Notas privadas, no visibles para el cliente'
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # ==================== MÉTODOS PERSONALIZADOS ====================
    
    @admin.display(description='Dominio', ordering='domain')
    def domain_link(self, obj):
        """
        Muestra el dominio como un link clickeable.
        
        Abre el sitio del cliente en una nueva pestaña.
        """
        url = obj.get_absolute_url()
        return format_html(
            '<a href="{}" target="_blank">{} ↗</a>',
            url,
            obj.domain
        )
    
    @admin.display(description='Estado', ordering='is_active')
    def status_badge(self, obj):
        """
        Badge visual del estado del cliente.
        
        Verde si está activo, rojo si está inactivo.
        """
        if obj.is_active:
            color = '#10B981'  # Verde
            text = '✓ Activo'
        else:
            color = '#EF4444'  # Rojo
            text = '✗ Inactivo'
        
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            text
        )
    
    @admin.display(description='Pago', ordering='next_payment_due')
    def payment_status(self, obj):
        """
        Indica el estado del pago mensual.
        
        Verde si está al día, amarillo si vence pronto, rojo si venció.
        """
        if not obj.setup_fee_paid:
            return format_html(
                '<span style="color: #EF4444;">⚠ Setup pendiente</span>'
            )
        
        if obj.is_payment_current:
            return format_html(
                '<span style="color: #10B981;">✓ Al día</span>'
            )
        else:
            return format_html(
                '<span style="color: #EF4444;">✗ Vencido</span>'
            )
    
    # ==================== ACCIONES ====================
    
    actions = ['activate_clients', 'deactivate_clients']
    
    @admin.action(description='✓ Activar clientes seleccionados')
    def activate_clients(self, request, queryset):
        """Activa múltiples clientes a la vez"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} cliente(s) activado(s) exitosamente.'
        )
    
    @admin.action(description='✗ Desactivar clientes seleccionados')
    def deactivate_clients(self, request, queryset):
        """Desactiva múltiples clientes a la vez"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} cliente(s) desactivado(s).'
        )
    
    # ==================== PERMISOS ====================
    
    def has_module_permission(self, request):
        """
        Solo superusuarios pueden ver el módulo de Clientes.
        
        Los clientes normales no deben ver otros clientes.
        """
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """Solo superusuarios pueden agregar clientes"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Solo superusuarios pueden editar clientes"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar clientes"""
        return request.user.is_superuser


@admin.register(ClientSettings)
class ClientSettingsAdmin(admin.ModelAdmin):
    """
    Admin standalone para ClientSettings.
    
    Normalmente se edita desde el inline de Client,
    pero esto permite acceso directo si es necesario.
    """
    
    list_display = ['client', 'primary_color', 'enable_blog']
    list_filter = ['enable_blog', 'enable_ecommerce']
    search_fields = ['client__company_name']
    
    def has_module_permission(self, request):
        """Solo superusuarios"""
        return request.user.is_superuser