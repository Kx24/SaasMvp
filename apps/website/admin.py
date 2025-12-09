"""
Configuración del Django Admin para la app Website
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Section, Service, Testimonial, ContactSubmission


class TenantAdminMixin:
    """
    Mixin para filtrar automáticamente por el tenant actual.
    
    IMPORTANTE: Requiere que el middleware inyecte request.client
    """
    
    def get_queryset(self, request):
        """Filtrar queryset por el cliente actual"""
        qs = super().get_queryset(request)
        
        # Si hay un cliente en el request (middleware), filtrar por él
        if hasattr(request, 'client'):
            return qs.filter(client=request.client)
        
        # Si es superuser, mostrar todo
        if request.user.is_superuser:
            return qs
        
        # Por defecto, no mostrar nada
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """Auto-asignar el cliente al guardar"""
        if hasattr(request, 'client') and not obj.pk:
            obj.client = request.client
        super().save_model(request, obj, form, change)


@admin.register(Section)
class SectionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    Admin para Secciones del sitio.
    """
    
    list_display = [
        'section_type_display',
        'title',
        'client_name',
        'order',
        'is_active',
        'updated_at'
    ]
    
    list_filter = [
        'section_type',
        'is_active',
        'created_at'
    ]
    
    search_fields = [
        'title',
        'subtitle',
        'content',
        'client__name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('client', 'section_type', 'order')
        }),
        ('Contenido', {
            'fields': ('title', 'subtitle', 'content', 'image')
        }),
        ('Configuración', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_editable = ['order', 'is_active']
    
    ordering = ['client', 'order', 'section_type']
    
    # Solo lectura para superusers (clientes no pueden cambiar cliente)
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            readonly.append('client')
        return readonly
    
    # Métodos personalizados para list_display
    def section_type_display(self, obj):
        """Mostrar tipo de sección con icono"""
        icons = {
            'hero': '🎯',
            'about': '👋',
            'services': '⚙️',
            'features': '✨',
            'testimonials': '💬',
            'contact': '📧',
            'cta': '🚀',
            'footer': '📄',
        }
        icon = icons.get(obj.section_type, '📌')
        return format_html(
            '{} <strong>{}</strong>',
            icon,
            obj.get_section_type_display()
        )
    section_type_display.short_description = 'Tipo de Sección'
    section_type_display.admin_order_field = 'section_type'
    
    def client_name(self, obj):
        """Mostrar nombre del cliente"""
        return obj.client.name
    client_name.short_description = 'Cliente'
    client_name.admin_order_field = 'client__name'


@admin.register(Service)
class ServiceAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    Admin para Servicios.
    """
    
    list_display = [
        'icon_display',
        'name',
        'client_name',
        'slug',
        'is_featured',
        'is_active',
        'order'
    ]
    
    list_filter = [
        'is_active',
        'is_featured',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'description',
        'full_description',
        'slug',
        'client__name'
    ]
    
    readonly_fields = [
        'slug',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('client', 'name', 'slug')
        }),
        ('Contenido', {
            'fields': ('description', 'full_description', 'image')
        }),
        ('Visual', {
            'fields': ('icon',)
        }),
        ('Precio', {
            'fields': ('price_text',),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': ('order', 'is_active', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_editable = ['order', 'is_active', 'is_featured']
    
    prepopulated_fields = {'slug': ('name',)}
    
    ordering = ['client', 'order', 'name']
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            readonly.append('client')
        # Slug es readonly siempre (se auto-genera)
        return readonly
    
    # Métodos personalizados
    def icon_display(self, obj):
        """Mostrar icono del servicio"""
        return format_html(
            '<span style="font-size: 1.5em;">{}</span>',
            obj.icon
        )
    icon_display.short_description = 'Icono'
    
    def client_name(self, obj):
        """Mostrar nombre del cliente"""
        return obj.client.name
    client_name.short_description = 'Cliente'
    client_name.admin_order_field = 'client__name'


@admin.register(Testimonial)
class TestimonialAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    Admin para Testimonios.
    """
    
    list_display = [
        'client_name_display',
        'company',
        'rating_display',
        'client_owner',
        'is_featured',
        'is_active',
        'order'
    ]
    
    list_filter = [
        'rating',
        'is_active',
        'is_featured',
        'created_at'
    ]
    
    search_fields = [
        'client_name',
        'company',
        'position',
        'content',
        'client__name'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('client', 'client_name', 'company', 'position', 'avatar')
        }),
        ('Testimonio', {
            'fields': ('content', 'rating')
        }),
        ('Configuración', {
            'fields': ('order', 'is_active', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    list_editable = ['order', 'is_active', 'is_featured']
    
    ordering = ['client', 'order', '-created_at']
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            readonly.append('client')
        return readonly
    
    # Métodos personalizados
    def client_name_display(self, obj):
        """Mostrar nombre del cliente con avatar"""
        if obj.avatar:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 8px;">'
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover;"/>'
                '<strong>{}</strong>'
                '</div>',
                obj.avatar.url,
                obj.client_name
            )
        return format_html('<strong>{}</strong>', obj.client_name)
    client_name_display.short_description = 'Cliente que opina'
    client_name_display.admin_order_field = 'client_name'
    
    def rating_display(self, obj):
        """Mostrar rating con estrellas"""
        stars = '⭐' * obj.rating
        return format_html('<span title="{}/5">{}</span>', obj.rating, stars)
    rating_display.short_description = 'Calificación'
    rating_display.admin_order_field = 'rating'
    
    def client_owner(self, obj):
        """Mostrar dueño (tenant)"""
        return obj.client.name
    client_owner.short_description = 'Sitio'
    client_owner.admin_order_field = 'client__name'


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    Admin para Mensajes de Contacto.
    """
    
    list_display = [
        'name',
        'email',
        'status_display',
        'client_name',
        'created_at',
        'source'
    ]
    
    list_filter = [
        'status',
        'source',
        'created_at'
    ]
    
    search_fields = [
        'name',
        'email',
        'phone',
        'company',
        'subject',
        'message',
        'client__name'
    ]
    
    readonly_fields = [
        'client',
        'ip_address',
        'user_agent',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Información del Contacto', {
            'fields': ('client', 'name', 'email', 'phone', 'company')
        }),
        ('Mensaje', {
            'fields': ('subject', 'message')
        }),
        ('Estado', {
            'fields': ('status', 'source')
        }),
        ('Metadata Técnica', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']
    
    date_hierarchy = 'created_at'
    
    # Acciones personalizadas
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_spam']
    
    def mark_as_read(self, request, queryset):
        """Marcar mensajes como leídos"""
        updated = queryset.update(status='read')
        self.message_user(
            request,
            f'{updated} mensaje(s) marcado(s) como leído(s).'
        )
    mark_as_read.short_description = "Marcar como leído"
    
    def mark_as_replied(self, request, queryset):
        """Marcar mensajes como respondidos"""
        updated = queryset.update(status='replied')
        self.message_user(
            request,
            f'{updated} mensaje(s) marcado(s) como respondido(s).'
        )
    mark_as_replied.short_description = "Marcar como respondido"
    
    def mark_as_spam(self, request, queryset):
        """Marcar mensajes como spam"""
        updated = queryset.update(status='spam')
        self.message_user(
            request,
            f'{updated} mensaje(s) marcado(s) como spam.'
        )
    mark_as_spam.short_description = "Marcar como spam"
    
    # Métodos personalizados
    def status_display(self, obj):
        """Mostrar estado con color"""
        colors = {
            'new': '#3b82f6',      # Azul
            'read': '#8b5cf6',     # Púrpura
            'replied': '#10b981',  # Verde
            'spam': '#ef4444',     # Rojo
        }
        icons = {
            'new': '🆕',
            'read': '👁️',
            'replied': '✅',
            'spam': '🚫',
        }
        color = colors.get(obj.status, '#6b7280')
        icon = icons.get(obj.status, '📧')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    status_display.short_description = 'Estado'
    status_display.admin_order_field = 'status'
    
    def client_name(self, obj):
        """Mostrar nombre del cliente (tenant)"""
        return obj.client.name
    client_name.short_description = 'Sitio'
    client_name.admin_order_field = 'client__name'
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusers pueden eliminar mensajes"""
        return request.user.is_superuser