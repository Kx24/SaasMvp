"""
Django Admin para gestión de Tenants
Enfocado en crear y gestionar clientes, no en su contenido
"""
from django.contrib import admin
from .models import Client, ClientSettings


class ClientSettingsInline(admin.StackedInline):
    """
    Inline para editar ClientSettings desde el Cliente
    """
    model = ClientSettings
    can_delete = False
    verbose_name = 'Configuración del Cliente'
    verbose_name_plural = 'Configuración del Cliente'
    
    fields = [
        'company_name',
        ('primary_color', 'secondary_color'),
        'logo',
        ('contact_email', 'contact_phone'),
        'social_media',
    ]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Admin para gestión de Clientes (Tenants)
    """
    list_display = ['name', 'domain', 'is_active', 'created_at', 'content_summary']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'domain', 'slug']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('🏢 Información del Cliente', {
            'fields': ('name', 'slug', 'domain', 'is_active')
        }),
        ('📝 Notas Internas', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('📊 Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ClientSettingsInline]
    
    def content_summary(self, obj):
        """
        Muestra resumen del contenido del cliente
        """
        from apps.website.models import Section, Service, ContactSubmission
        
        sections = Section.objects.filter(client=obj).count()
        services = Service.objects.filter(client=obj).count()
        contacts = ContactSubmission.objects.filter(client=obj).count()
        
        return f"📄 {sections} secciones | 🛠️ {services} servicios | 📧 {contacts} contactos"
    
    content_summary.short_description = 'Contenido'
    
    def save_model(self, request, obj, form, change):
        """
        Al crear un nuevo cliente, asegurar que se cree su slug
        """
        if not obj.slug:
            from django.utils.text import slugify
            obj.slug = slugify(obj.name)
        
        super().save_model(request, obj, form, change)


# NO registrar ClientSettings directamente
# Solo se edita a través del inline en Client