"""
Admin de Website - Filtrado por Tenant
======================================
Los usuarios staff solo ven contenido de su tenant.
Superusers ven todo.
"""
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

# Importar modelos disponibles
from .models import Section, Service, ContactSubmission

# Intentar importar Testimonial (puede no existir)
try:
    from .models import Testimonial
    HAS_TESTIMONIAL = True
except ImportError:
    HAS_TESTIMONIAL = False


@admin.register(Section)
class SectionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin de Secciones filtrado por tenant"""
    
    tenant_field = 'client'
    
    list_display = ['section_type_display', 'title', 'client_display', 'is_active', 'order']
    list_filter = ['section_type', 'is_active']
    search_fields = ['title', 'subtitle']
    list_editable = ['is_active', 'order']
    ordering = ['client', 'order']
    
    fieldsets = (
        ('Seccion', {
            'fields': ('client', 'section_type', 'title', 'subtitle', 'description')
        }),
        ('Imagen', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Configuracion', {
            'fields': (('order', 'is_active'),)
        }),
    )
    
    def section_type_display(self, obj):
        icons = {'hero': '🏠', 'about': 'ℹ️', 'contact': '📧', 'services': '🛠️'}
        icon = icons.get(obj.section_type, '📄')
        return f"{icon} {obj.get_section_type_display()}"
    section_type_display.short_description = 'Tipo'
    
    def client_display(self, obj):
        return obj.client.name if obj.client else '-'
    client_display.short_description = 'Tenant'
    
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


@admin.register(Service)
class ServiceAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin de Servicios filtrado por tenant"""
    
    tenant_field = 'client'
    
    list_display = ['icon_display', 'name', 'client_display', 'price_text', 'is_featured', 'is_active', 'order']
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'is_featured', 'order']
    ordering = ['client', 'order']
    
    fieldsets = (
        ('Servicio', {
            'fields': ('client', 'name', 'icon', 'description')
        }),
        ('Precio', {
            'fields': ('price_text',),
            'classes': ('collapse',)
        }),
        ('Imagen', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Configuracion', {
            'fields': (('order', 'is_active', 'is_featured'),)
        }),
    )
    
    def icon_display(self, obj):
        return format_html('<span style="font-size: 1.5em;">{}</span>', obj.icon or '⚡')
    icon_display.short_description = ''
    
    def client_display(self, obj):
        return obj.client.name if obj.client else '-'
    client_display.short_description = 'Tenant'
    
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


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin de Contactos filtrado por tenant"""
    
    tenant_field = 'client'
    
    list_display = ['name', 'email', 'client_display', 'status_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'created_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Contacto', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Mensaje', {
            'fields': ('subject', 'message')
        }),
        ('Estado', {
            'fields': ('status',)
        }),
        ('Info', {
            'fields': ('created_at',),
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
            '<span style="color: {}; font-weight: bold;">{}</span>',
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
    
    @admin.action(description='Marcar como leido')
    def mark_as_read(self, request, queryset):
        queryset.update(status='read')
    
    @admin.action(description='Marcar como respondido')
    def mark_as_replied(self, request, queryset):
        queryset.update(status='replied')
    
    @admin.action(description='Marcar como spam')
    def mark_as_spam(self, request, queryset):
        queryset.update(status='spam')


# Solo registrar Testimonial si existe
if HAS_TESTIMONIAL:
    @admin.register(Testimonial)
    class TestimonialAdmin(TenantAdminMixin, admin.ModelAdmin):
        tenant_field = 'client'
        
        list_display = ['client_name', 'company', 'client_display', 'rating', 'is_featured', 'is_active']
        list_filter = ['is_active', 'is_featured', 'rating']
        search_fields = ['client_name', 'company', 'content']
        list_editable = ['is_active', 'is_featured']
        
        def client_display(self, obj):
            return obj.client.name if obj.client else '-'
        client_display.short_description = 'Tenant'
        
        def get_list_filter(self, request):
            if request.user.is_superuser:
                return ['is_active', 'is_featured', 'rating', 'client']
            return ['is_active', 'is_featured', 'rating']