"""
Django Admin para Tenants - CORREGIDO
=====================================
SOLO SUPERUSERS pueden gestionar tenants.

FIX: Inlines con extra=0 y max_num=1 evitan duplicados.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from .models import Client, Domain, ClientSettings, ClientEmailSettings


# ============================================================
# FORMULARIO
# ============================================================

class ClientAdminForm(forms.ModelForm):
    """Formulario extendido para crear tenant completo"""
    
    primary_domain = forms.CharField(
        max_length=255,
        required=False,
        label="Dominio Principal",
        help_text="Ej: miempresa.tuapp.cl"
    )
    
    primary_color = forms.CharField(
        max_length=7,
        initial='#2563eb',
        required=False,
        label="Color Primario",
        widget=forms.TextInput(attrs={'type': 'color', 'style': 'width: 80px; height: 35px;'})
    )
    secondary_color = forms.CharField(
        max_length=7,
        initial='#1e40af',
        required=False,
        label="Color Secundario",
        widget=forms.TextInput(attrs={'type': 'color', 'style': 'width: 80px; height: 35px;'})
    )
    
    settings_email = forms.EmailField(required=False, label="Email Publico")
    settings_phone = forms.CharField(max_length=20, required=False, label="Telefono")
    whatsapp_number = forms.CharField(max_length=20, required=False, label="WhatsApp")
    
    facebook_url = forms.URLField(required=False, label="Facebook")
    instagram_url = forms.URLField(required=False, label="Instagram")
    linkedin_url = forms.URLField(required=False, label="LinkedIn")
    
    meta_title = forms.CharField(max_length=60, required=False, label="Titulo SEO")
    meta_description = forms.CharField(max_length=160, required=False, label="Descripcion SEO",
                                        widget=forms.Textarea(attrs={'rows': 2}))
    google_analytics_id = forms.CharField(max_length=50, required=False, label="Google Analytics")
    
    create_initial_content = forms.BooleanField(
        initial=True,
        required=False,
        label="Crear contenido inicial"
    )
    
    class Meta:
        model = Client
        fields = ['name', 'slug', 'company_name', 'contact_email', 'contact_phone',
                  'template', 'is_active', 'notes']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        if instance and instance.pk:
            # Cargar datos existentes
            primary_domain = instance.domains.filter(is_primary=True).first()
            if primary_domain:
                self.fields['primary_domain'].initial = primary_domain.domain
            
            if hasattr(instance, 'settings'):
                s = instance.settings
                self.fields['primary_color'].initial = s.primary_color
                self.fields['secondary_color'].initial = s.secondary_color
                self.fields['settings_email'].initial = s.contact_email
                self.fields['settings_phone'].initial = s.contact_phone
                self.fields['whatsapp_number'].initial = s.whatsapp_number
                self.fields['facebook_url'].initial = s.facebook_url
                self.fields['instagram_url'].initial = s.instagram_url
                self.fields['linkedin_url'].initial = s.linkedin_url
                self.fields['meta_title'].initial = s.meta_title
                self.fields['meta_description'].initial = s.meta_description
                self.fields['google_analytics_id'].initial = s.google_analytics_id
            
            self.fields['create_initial_content'].widget = forms.HiddenInput()


# ============================================================
# INLINES - CORREGIDOS
# ============================================================

class DomainInline(admin.TabularInline):
    model = Domain
    extra = 0
    fields = ['domain', 'domain_type', 'is_primary', 'is_active', 'ssl_enabled']
    readonly_fields = ['domain_type']


class ClientSettingsInline(admin.StackedInline):
    """
    Inline para ClientSettings.
    extra=0 y max_num=1 evitan crear duplicados.
    """
    model = ClientSettings
    can_delete = False
    extra = 0
    max_num = 1
    
    fieldsets = (
        ('Avanzado', {
            'fields': ('font_family', 'meta_keywords', 'facebook_pixel_id'),
            'classes': ('collapse',)
        }),
        ('RRSS Extra', {
            'fields': ('twitter_url', 'youtube_url'),
            'classes': ('collapse',)
        }),
        ('Features', {
            'fields': (('enable_blog', 'enable_testimonials', 'enable_contact_form'),),
            'classes': ('collapse',)
        }),
    )


class ClientEmailSettingsInline(admin.StackedInline):
    """
    Inline para ClientEmailSettings.
    extra=0 y max_num=1 evitan crear duplicados.
    """
    model = ClientEmailSettings
    can_delete = False
    extra = 0
    max_num = 1
    verbose_name = "Configuración de Email"
    
    fieldsets = (
        ('Modo de Notificación', {
            'fields': ('provider', 'notify_mode', 'is_active', 'test_mode'),
        }),
        ('SMTP', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_use_tls', 'smtp_use_ssl'),
            'classes': ('collapse',),
        }),
        ('API Key', {
            'fields': ('api_key',),
            'classes': ('collapse',),
        }),
        ('Remitente', {
            'fields': ('from_email', 'from_name', 'reply_to'),
        }),
        ('Destinatarios', {
            'fields': ('notify_emails', 'send_copy_to_sender'),
        }),
    )


# ============================================================
# CLIENT ADMIN - SOLO SUPERUSERS
# ============================================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    form = ClientAdminForm
    inlines = [DomainInline, ClientSettingsInline, ClientEmailSettingsInline]
    
    list_display = ['name', 'domain_display', 'status_display', 'users_count', 'content_count', 'site_link']
    list_filter = ['is_active', 'template', 'created_at']
    search_fields = ['name', 'slug', 'domains__domain']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informacion', {
            'fields': (('name', 'slug'), 'company_name', ('contact_email', 'contact_phone'), 'template')
        }),
        ('Dominio', {
            'fields': ('primary_domain',)
        }),
        ('Estado', {
            'fields': (('is_active', 'setup_completed'),)
        }),
        ('Branding', {
            'fields': (('primary_color', 'secondary_color'),),
            'classes': ('collapse',)
        }),
        ('Contacto Publico', {
            'fields': (('settings_email', 'settings_phone'), 'whatsapp_number'),
            'classes': ('collapse',)
        }),
        ('Redes Sociales', {
            'fields': (('facebook_url', 'instagram_url'), 'linkedin_url'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'google_analytics_id'),
            'classes': ('collapse',)
        }),
        ('Opciones', {
            'fields': ('create_initial_content', 'notes'),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # ============================================================
    # PERMISOS - SOLO SUPERUSERS
    # ============================================================
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    # ============================================================
    # SAVE - CORREGIDO
    # ============================================================
    
    def save_model(self, request, obj, form, change):
        """
        Guarda el cliente. NO crea Settings aquí porque
        el modelo Client.save() ya lo hace.
        """
        super().save_model(request, obj, form, change)
        
        # Dominio
        domain_value = form.cleaned_data.get('primary_domain', '').lower().strip()
        if domain_value:
            from django.conf import settings as django_settings
            base_domain = getattr(django_settings, 'BASE_DOMAIN', 'localhost')
            domain_type = 'subdomain' if domain_value.endswith(f'.{base_domain}') else 'custom'
            
            primary_domain = obj.domains.filter(is_primary=True).first()
            if primary_domain:
                if primary_domain.domain != domain_value:
                    primary_domain.domain = domain_value
                    primary_domain.domain_type = domain_type
                    primary_domain.save()
            else:
                Domain.objects.create(
                    client=obj, domain=domain_value, domain_type=domain_type,
                    is_primary=True, is_active=True
                )
        
        # Settings - get_or_create (el modelo ya lo creó, solo actualizamos)
        settings_obj, _ = ClientSettings.objects.get_or_create(client=obj)
        settings_obj.primary_color = form.cleaned_data.get('primary_color') or '#2563eb'
        settings_obj.secondary_color = form.cleaned_data.get('secondary_color') or '#1e40af'
        settings_obj.contact_email = form.cleaned_data.get('settings_email') or ''
        settings_obj.contact_phone = form.cleaned_data.get('settings_phone') or ''
        settings_obj.whatsapp_number = form.cleaned_data.get('whatsapp_number') or ''
        settings_obj.facebook_url = form.cleaned_data.get('facebook_url') or ''
        settings_obj.instagram_url = form.cleaned_data.get('instagram_url') or ''
        settings_obj.linkedin_url = form.cleaned_data.get('linkedin_url') or ''
        settings_obj.meta_title = form.cleaned_data.get('meta_title') or ''
        settings_obj.meta_description = form.cleaned_data.get('meta_description') or ''
        settings_obj.google_analytics_id = form.cleaned_data.get('google_analytics_id') or ''
        settings_obj.company_name = obj.company_name or obj.name
        settings_obj.save()
        
        # EmailSettings - asegurar que existe
        ClientEmailSettings.objects.get_or_create(client=obj)
        
        # Contenido inicial (solo al crear)
        if not change and form.cleaned_data.get('create_initial_content', True):
            self._create_initial_content(obj)
    
    def _create_initial_content(self, client):
        from apps.website.models import Section, Service
        
        for i, (stype, title, sub) in enumerate([
            ('hero', f'Bienvenido a {client.name}', 'Soluciones profesionales'),
            ('about', 'Quienes Somos', 'Nuestra historia'),
            ('contact', 'Contactanos', 'Estamos para ayudarte'),
        ], 1):
            Section.objects.get_or_create(
                client=client, section_type=stype,
                defaults={'title': title, 'subtitle': sub, 'order': i*10, 'is_active': True}
            )
        
        templates = {
            'electricidad': [('Instalaciones', '⚡'), ('Mantencion', '🔧'), ('Emergencias', '🚨')],
            'construccion': [('Construccion', '🏠'), ('Remodelacion', '🔨'), ('Obras', '🧱')],
            'servicios_profesionales': [('Consultoria', '💼'), ('Capacitacion', '📚'), ('Soporte', '🛠️')],
            'portafolio': [('Desarrollo', '🌐'), ('Diseno', '🎨'), ('Marketing', '📱')],
        }
        services = templates.get(client.template, [('Servicio 1', '⭐'), ('Servicio 2', '✨')])
        
        for i, (name, icon) in enumerate(services, 1):
            Service.objects.get_or_create(
                client=client, name=name,
                defaults={'icon': icon, 'description': name, 'order': i*10, 'is_active': True}
            )
    
    # ============================================================
    # DISPLAY
    # ============================================================
    
    def domain_display(self, obj):
        d = obj.domains.filter(is_primary=True).first()
        if d:
            return format_html('<a href="https://{0}" target="_blank">{0}</a>', d.domain)
        return format_html('<span style="color:#dc2626;">Sin dominio</span>')
    domain_display.short_description = 'Dominio'
    
    def status_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:#16a34a;">● Activo</span>')
        return format_html('<span style="color:#dc2626;">● Inactivo</span>')
    status_display.short_description = 'Estado'
    
    def users_count(self, obj):
        from apps.accounts.models import UserProfile
        count = UserProfile.objects.filter(client=obj).count()
        return f'👤 {count}'
    users_count.short_description = 'Usuarios'
    
    def content_count(self, obj):
        from apps.website.models import Service, ContactSubmission
        services = Service.objects.filter(client=obj).count()
        new_contacts = ContactSubmission.objects.filter(client=obj, status='new').count()
        html = f'🛠️ {services}'
        if new_contacts:
            html += f' <span style="color:#dc2626;">📧 {new_contacts}</span>'
        return format_html(html)
    content_count.short_description = 'Contenido'
    
    def site_link(self, obj):
        d = obj.domains.filter(is_primary=True).first()
        if d:
            return format_html(
                '<a href="https://{}" target="_blank" style="padding:3px 8px;background:#2563eb;'
                'color:white;border-radius:3px;text-decoration:none;font-size:11px;">Visitar</a>',
                d.domain
            )
        return '-'
    site_link.short_description = ''


# ============================================================
# DOMAIN ADMIN - SOLO SUPERUSERS
# ============================================================

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'client', 'is_primary', 'is_active']
    list_filter = ['is_primary', 'is_active', 'domain_type']
    search_fields = ['domain', 'client__name']
    raw_id_fields = ['client']
    
    def has_module_permission(self, request):
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ============================================================
# ADMIN CONFIG
# ============================================================

admin.site.site_header = "SaaS MVP - Panel de Control"
admin.site.site_title = "SaaS Admin"
admin.site.index_title = "Administracion"