# =============================================================================
# apps/website/admin.py - CORREGIDO CON CLOUDINARY
# =============================================================================
# Admin de Website con soporte Cloudinary y filtrado por Tenant
# =============================================================================

from django.contrib import admin
from django.utils.html import format_html

# Importar mixin
try:
    from apps.accounts.mixins import TenantAdminMixin
except ImportError:
    # Fallback si no existe el mixin
    class TenantAdminMixin:
        tenant_field = 'client'
        
        def get_queryset(self, request):
            qs = super().get_queryset(request)
            if request.user.is_superuser:
                return qs
            if hasattr(request.user, 'profile') and request.user.profile.client:
                return qs.filter(**{self.tenant_field: request.user.profile.client})
            return qs.none()
        
        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == 'client' and not request.user.is_superuser:
                if hasattr(request.user, 'profile') and request.user.profile.client:
                    kwargs['queryset'] = db_field.related_model.objects.filter(
                        pk=request.user.profile.client.pk
                    )
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

# Importar modelos
from .models import Section, Service, ContactSubmission


# =============================================================================
# SECTION ADMIN
# =============================================================================

@admin.register(Section)
class SectionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin de Secciones con soporte Cloudinary"""
    
    tenant_field = 'client'
    
    list_display = [
        'section_type_display',
        'title',
        'client_display',
        'image_preview',
        'order',
        'is_active',
        'updated_at'
    ]
    
    list_filter = ['section_type', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'subtitle', 'description']
    ordering = ['client', 'order']
    
    fieldsets = (
        ('Sección', {
            'fields': ('client', 'section_type', 'title', 'subtitle', 'description')
        }),
        ('Imagen', {
            'fields': ('image', 'image_preview_large'),
            'description': 'La imagen se sube automáticamente a Cloudinary'
        }),
        ('Configuración', {
            'fields': (('order', 'is_active'),)
        }),
    )
    
    readonly_fields = ['image_preview_large']

    def save_model(self, request, obj, form, change):
        """Sube imagen a carpeta del tenant."""
        if 'image' in form.changed_data and obj.image:
            # Subir a carpeta del tenant
            import cloudinary.uploader
            folder = f"{obj.client.slug}/sections"
            result = cloudinary.uploader.upload(
                obj.image.file,
                folder=folder,
                resource_type="image"
            )
            obj.image = result['public_id']
        super().save_model(request, obj, form, change)
    
    def section_type_display(self, obj):
        icons = {'hero': '🏠', 'about': 'ℹ️', 'contact': '📧', 'service': '🛠️'}
        icon = icons.get(obj.section_type, '📄')
        return f"{icon} {obj.get_section_type_display()}"
    section_type_display.short_description = 'Tipo'
    
    def client_display(self, obj):
        return obj.client.name if obj.client else '-'
    client_display.short_description = 'Tenant'
    
    def image_preview(self, obj):
        """Miniatura de imagen en listado."""
        if obj.image:
            url = obj.get_image_url('thumbnail')
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: cover; border-radius: 4px;">',
                url
            )
        return '—'
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        """Preview grande en formulario de edición."""
        if obj.image:
            url = obj.get_image_url('service_card')
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 400px; object-fit: cover; border-radius: 8px; margin-top: 10px;">',
                url
            )
        return 'Sin imagen'
    image_preview_large.short_description = 'Vista previa'
    
    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ['section_type', 'is_active', 'client']
        return ['section_type', 'is_active']
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            new_fieldsets = []
            for name, options in fieldsets:
                fields = list(options.get('fields', []))
                if 'client' in fields:
                    fields.remove('client')
                new_options = {**options, 'fields': tuple(fields)}
                new_fieldsets.append((name, new_options))
            return new_fieldsets
        return fieldsets


# =============================================================================
# SERVICE ADMIN
# =============================================================================

@admin.register(Service)
class ServiceAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin de Servicios con soporte Cloudinary"""
    
    tenant_field = 'client'
    
    list_display = [
        'icon_display',
        'name',
        'client_display',
        'image_preview',
        'price_text',
        'order',
        'is_featured',
        'is_active'
    ]
    
    list_filter = ['is_active', 'is_featured']
    list_editable = ['order', 'is_active', 'is_featured']
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['client', 'order']
    
    fieldsets = (
        ('Servicio', {
            'fields': ('client', 'name', 'slug', 'icon')
        }),
        ('Contenido', {
            'fields': ('description', 'full_description')
        }),
        ('Imagen', {
            'fields': ('image', 'image_preview_large'),
            'description': 'La imagen se sube automáticamente a Cloudinary'
        }),
        ('Precio', {
            'fields': ('price_text',),
            'classes': ('collapse',)
        }),
        ('Configuración', {
            'fields': (('order', 'is_active', 'is_featured'),)
        }),
    )
    
    readonly_fields = ['image_preview_large']

    def save_model(self, request, obj, form, change):
        """Sube imagen a carpeta del tenant."""
        if 'image' in form.changed_data and obj.image:
            # Subir a carpeta del tenant
            import cloudinary.uploader
            folder = f"{obj.client.slug}/services"
            result = cloudinary.uploader.upload(
                obj.image.file,
                folder=folder,
                resource_type="image"
            )
            obj.image = result['public_id']
        super().save_model(request, obj, form, change)
    
    def icon_display(self, obj):
        return format_html('<span style="font-size: 1.5em;">{}</span>', obj.icon or '⚡')
    icon_display.short_description = ''
    
    def client_display(self, obj):
        return obj.client.name if obj.client else '-'
    client_display.short_description = 'Tenant'
    
    def image_preview(self, obj):
        """Miniatura de imagen en listado."""
        if obj.image:
            url = obj.get_image_url('thumbnail')
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 80px; object-fit: cover; border-radius: 4px;">',
                url
            )
        return '—'
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        """Preview grande en formulario de edición."""
        if obj.image:
            url = obj.get_image_url('service_card')
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 400px; object-fit: cover; border-radius: 8px; margin-top: 10px;">',
                url
            )
        return 'Sin imagen'
    image_preview_large.short_description = 'Vista previa'
    
    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ['is_active', 'is_featured', 'client']
        return ['is_active', 'is_featured']
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            new_fieldsets = []
            for name, options in fieldsets:
                fields = list(options.get('fields', []))
                if 'client' in fields:
                    fields.remove('client')
                new_options = {**options, 'fields': tuple(fields)}
                new_fieldsets.append((name, new_options))
            return new_fieldsets
        return fieldsets


# =============================================================================
# CONTACT SUBMISSION ADMIN
# =============================================================================

@admin.register(ContactSubmission)
class ContactSubmissionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin de Contactos filtrado por tenant"""
    
    tenant_field = 'client'
    
    list_display = ['name', 'email', 'client_display', 'subject', 'status_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'phone', 'company', 'subject', 'message', 
                       'created_at', 'updated_at', 'ip_address', 'user_agent']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Contacto', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('Mensaje', {
            'fields': ('subject', 'message')
        }),
        ('Estado', {
            'fields': ('status', 'source')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def client_display(self, obj):
        return obj.client.name if obj.client else '-'
    client_display.short_description = 'Tenant'
    
    def status_display(self, obj):
        colors = {
            'new': '#dc2626',
            'read': '#2563eb',
            'replied': '#16a34a',
            'spam': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Estado'
    
    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ['status', 'created_at', 'client']
        return ['status', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_spam']
    
    @admin.action(description='Marcar como leído')
    def mark_as_read(self, request, queryset):
        queryset.update(status='read')
    
    @admin.action(description='Marcar como respondido')
    def mark_as_replied(self, request, queryset):
        queryset.update(status='replied')
    
    @admin.action(description='Marcar como spam')
    def mark_as_spam(self, request, queryset):
        queryset.update(status='spam')