"""
Admin panel para modelos CMS
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Section, Service, Testimonial, ContactSubmission


class TenantAdminMixin:
    """
    Mixin que asegura que admin filtre por tenant actual.
    
    Auto-asigna el cliente al guardar si no está ya asignado.
    """
    
    def get_queryset(self, request):
        """Filtrar queryset por cliente del request"""
        qs = super().get_queryset(request)
        
        if hasattr(request, 'client'):
            qs = qs.filter(client=request.client)
        
        return qs
    
    def save_model(self, request, obj, form, change):
        """Auto-asignar cliente al guardar"""
        if not obj.client_id and hasattr(request, 'client'):
            obj.client = request.client
        
        super().save_model(request, obj, form, change)


@admin.register(Section)
class SectionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin para editar secciones de página"""
    
    list_display = (
        'slug',
        'client',
        'title',
        'order',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'is_active',
        'client',
        'created_at'
    )
    
    search_fields = (
        'slug',
        'title',
        'content'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Contenido', {
            'fields': (
                'client',
                'slug',
                'title',
                'content',
                'order',
                'is_active'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('order', '-created_at')


@admin.register(Service)
class ServiceAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin para editar servicios"""
    
    list_display = (
        'name',
        'client',
        'order',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'is_active',
        'client',
        'created_at'
    )
    
    search_fields = (
        'name',
        'description'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'client',
                'name',
                'description',
                'order',
                'is_active'
            )
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('order', '-created_at')


@admin.register(Testimonial)
class TestimonialAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin para editar testimonios"""
    
    list_display = (
        'author',
        'client',
        'rating_display',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'is_active',
        'rating',
        'client',
        'created_at'
    )
    
    search_fields = (
        'author',
        'company',
        'text'
    )
    
    readonly_fields = (
        'created_at',
        'updated_at'
    )
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'client',
                'author',
                'company',
                'text',
                'rating',
                'order',
                'is_active'
            )
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rating_display(self, obj):
        """Mostrar rating como estrellas"""
        return format_html(
            '{} <span style="color: #fc9902;">{}</span>',
            obj.get_rating_display(),
            '★' * obj.rating
        )
    rating_display.short_description = 'Rating'
    
    ordering = ('order', '-created_at')


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin para ver contactos (read-only)"""
    
    list_display = (
        'name',
        'client',
        'email',
        'read_status',
        'created_at'
    )
    
    list_filter = (
        'is_read',
        'client',
        'created_at'
    )
    
    search_fields = (
        'name',
        'email',
        'message'
    )
    
    readonly_fields = (
        'created_at',
        'email',
        'name',
        'message'
    )
    
    fieldsets = (
        ('Contacto', {
            'fields': (
                'client',
                'name',
                'email',
                'phone',
                'message'
            )
        }),
        ('Estado', {
            'fields': ('is_read', 'replied_at')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """No permitir crear desde admin"""
        return False
    
    def read_status(self, obj):
        """Mostrar estado de lectura"""
        status = '✅ Leído' if obj.is_read else '⏳ Pendiente'
        color = 'green' if obj.is_read else 'orange'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            status
        )
    read_status.short_description = 'Estado'
    
    ordering = ('-created_at',)