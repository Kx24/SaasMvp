"""
Django Admin para Website
Solo lectura - Los clientes gestionan su contenido desde el dashboard
VERSIÓN CORREGIDA - Campo created_at en ContactSubmission
"""
from django.contrib import admin
from .models import Section, Service, Testimonial, ContactSubmission


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    """
    Admin de Secciones - Solo lectura y monitoreo
    """
    list_display = ['title', 'client', 'section_type', 'is_active', 'order']
    list_filter = ['client', 'section_type', 'is_active']
    search_fields = ['title', 'subtitle', 'client__name']
    readonly_fields = ['client', 'created_at', 'updated_at']
    
    fieldsets = (
        ('📄 Información', {
            'fields': ('client', 'section_type', 'title', 'subtitle', 'description', 'image')
        }),
        ('⚙️ Configuración', {
            'fields': ('order', 'is_active')
        }),
        ('📊 Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """
        No permitir crear secciones desde superadmin
        Los clientes las crean desde su dashboard
        """
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        No permitir eliminar desde superadmin
        Para evitar accidentes
        """
        return False


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """
    Admin de Servicios - Solo lectura y monitoreo
    """
    list_display = ['name', 'client', 'is_active', 'is_featured', 'price_text']
    list_filter = ['client', 'is_active', 'is_featured']
    search_fields = ['name', 'description', 'client__name']
    readonly_fields = ['client', 'slug', 'created_at', 'updated_at']
    
    fieldsets = (
        ('🛠️ Información', {
            'fields': ('client', 'name', 'slug', 'icon', 'description', 'image', 'price_text')
        }),
        ('⚙️ Configuración', {
            'fields': ('order', 'is_active', 'is_featured')
        }),
        ('📊 Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """
    Admin de Testimonios - Solo lectura y monitoreo
    """
    list_display = ['client_name', 'client', 'company', 'rating', 'is_active']
    list_filter = ['client', 'is_active', 'is_featured', 'rating']
    search_fields = ['client_name', 'company', 'content', 'client__name']
    readonly_fields = ['client', 'created_at', 'updated_at']
    
    fieldsets = (
        ('👤 Información', {
            'fields': ('client', 'client_name', 'company', 'position', 'avatar')
        }),
        ('💬 Contenido', {
            'fields': ('content', 'rating')
        }),
        ('⚙️ Configuración', {
            'fields': ('order', 'is_active', 'is_featured')
        }),
        ('📊 Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    """
    Admin de Contactos - Solo lectura y monitoreo
    """
    list_display = ['name', 'email', 'client', 'status', 'created_at']
    list_filter = ['client', 'status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message', 'client__name']
    readonly_fields = [
        'client', 'name', 'email', 'phone', 'company', 'subject', 'message',
        'source', 'ip_address', 'user_agent', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('👤 Información del Contacto', {
            'fields': ('client', 'name', 'email', 'phone', 'company')
        }),
        ('💬 Mensaje', {
            'fields': ('subject', 'message')
        }),
        ('📊 Estado y Tracking', {
            'fields': ('status', 'source', 'ip_address', 'user_agent', 'created_at', 'updated_at')
        }),
    )
    
    # Permitir cambiar status desde admin
    def get_readonly_fields(self, request, obj=None):
        """
        Todos los campos readonly excepto 'status'
        """
        if obj:  # Editando
            # Permitir editar solo el status
            return [f for f in self.readonly_fields]
        return self.readonly_fields
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Permitir eliminar contactos (para limpieza)
        return True