"""
Admin para el sistema Multi-Tenant.

Incluye:
- ClientAdmin con inlines para Settings, EmailSettings, FormConfig
- DomainAdmin
- Admins individuales para cada configuración
"""
from django.contrib import admin
from .models import Client, Domain, ClientSettings, ClientEmailSettings, FormConfig


# ==============================================================================
# INLINES
# ==============================================================================

class DomainInline(admin.TabularInline):
    """Inline para gestionar dominios desde el Client."""
    model = Domain
    extra = 1
    fields = ['domain', 'domain_type', 'is_primary', 'is_active', 'is_verified']


class ClientSettingsInline(admin.StackedInline):
    """Inline para configuración de branding."""
    model = ClientSettings
    extra = 0
    max_num = 1
    
    fieldsets = (
        ('Branding', {
            'fields': (
                ('logo', 'favicon'),
                ('primary_color', 'secondary_color'),
                'font_family',
            )
        }),
        ('Información', {
            'fields': (
                'company_name',
                'tagline',
                'description',
                ('contact_email', 'contact_phone'),
                'address',
            )
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': (
                'meta_title',
                'meta_description',
                'meta_keywords',
            )
        }),
        ('Analytics', {
            'classes': ('collapse',),
            'fields': (
                'google_analytics_id',
                'facebook_pixel_id',
            )
        }),
        ('Redes Sociales', {
            'classes': ('collapse',),
            'fields': (
                ('facebook_url', 'instagram_url'),
                ('twitter_url', 'linkedin_url'),
                ('youtube_url', 'whatsapp_number'),
            )
        }),
        ('Features', {
            'classes': ('collapse',),
            'fields': (
                ('enable_blog', 'enable_testimonials', 'enable_contact_form'),
            )
        }),
    )


class ClientEmailSettingsInline(admin.StackedInline):
    """Inline para configuración de email."""
    model = ClientEmailSettings
    extra = 0
    max_num = 1
    
    fieldsets = (
        ('Configuración General', {
            'fields': (
                ('provider', 'notify_mode'),
                'is_active',
            )
        }),
        ('SMTP', {
            'classes': ('collapse',),
            'fields': (
                'smtp_host',
                ('smtp_port', 'smtp_use_tls', 'smtp_use_ssl'),
                ('smtp_username', 'smtp_password'),
            )
        }),
        ('API Providers', {
            'classes': ('collapse',),
            'fields': ('api_key',)
        }),
        ('Emails', {
            'fields': (
                ('from_email', 'from_name'),
                'reply_to',
                'notify_emails',
            )
        }),
        ('Templates', {
            'classes': ('collapse',),
            'fields': (
                'email_subject_template',
                'send_copy_to_sender',
            )
        }),
        ('Testing', {
            'classes': ('collapse',),
            'fields': (
                'test_mode',
                ('last_test_at', 'last_test_success'),
                'last_test_error',
            )
        }),
    )


class FormConfigInline(admin.StackedInline):
    """Inline para configuración del formulario de contacto."""
    model = FormConfig
    extra = 0
    max_num = 1
    
    fieldsets = (
        ('Campos Básicos', {
            'fields': (
                ('name_label', 'name_placeholder'),
                ('email_label', 'email_placeholder'),
                ('message_label', 'message_placeholder', 'message_rows'),
            )
        }),
        ('Teléfono', {
            'classes': ('collapse',),
            'fields': (
                ('show_phone', 'phone_required'),
                ('phone_label', 'phone_placeholder'),
            )
        }),
        ('Empresa', {
            'classes': ('collapse',),
            'fields': (
                ('show_company', 'company_required'),
                ('company_label', 'company_placeholder'),
            )
        }),
        ('Asunto', {
            'classes': ('collapse',),
            'fields': (
                ('show_subject', 'subject_required'),
                'subject_label',
                'subject_options',
            )
        }),
        ('Dirección', {
            'classes': ('collapse',),
            'fields': (
                ('show_address', 'address_required'),
                ('address_label', 'address_placeholder'),
                ('show_city', 'city_required'),
                ('city_label', 'city_placeholder'),
            )
        }),
        ('Presupuesto', {
            'classes': ('collapse',),
            'fields': (
                ('show_budget', 'budget_required'),
                'budget_label',
                'budget_options',
            )
        }),
        ('Urgencia', {
            'classes': ('collapse',),
            'fields': (
                ('show_urgency', 'urgency_required'),
                'urgency_label',
                'urgency_options',
            )
        }),
        ('¿Cómo nos conociste?', {
            'classes': ('collapse',),
            'fields': (
                ('show_source', 'source_required'),
                'source_label',
                'source_options',
            )
        }),
        ('Configuración del Formulario', {
            'fields': (
                'submit_button_text',
                'success_message',
                'privacy_text',
            )
        }),
    )


# ==============================================================================
# CLIENT ADMIN
# ==============================================================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Admin principal para gestionar clientes/tenants."""
    
    list_display = ['name', 'slug', 'template', 'is_active', 'setup_completed', 'created_at']
    list_filter = ['is_active', 'template', 'setup_completed', 'setup_fee_paid']
    search_fields = ['name', 'slug', 'company_name', 'contact_email']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [
        DomainInline,
        ClientSettingsInline,
        ClientEmailSettingsInline,
        FormConfigInline,
    ]
    
    fieldsets = (
        ('Identificación', {
            'fields': (
                ('name', 'slug'),
                'company_name',
                ('contact_email', 'contact_phone'),
            )
        }),
        ('Template', {
            'fields': ('template',)
        }),
        ('Estado', {
            'fields': (
                ('is_active', 'setup_completed'),
            )
        }),
        ('Billing', {
            'classes': ('collapse',),
            'fields': (
                ('setup_fee_paid', 'monthly_fee'),
                ('last_payment_date', 'next_payment_due'),
            )
        }),
        ('Límites', {
            'classes': ('collapse',),
            'fields': (
                ('max_images', 'max_pages', 'max_services'),
            )
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': (
                ('created_at', 'updated_at'),
                'notes',
            )
        }),
    )


# ==============================================================================
# DOMAIN ADMIN
# ==============================================================================

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin para gestionar dominios."""
    
    list_display = ['domain', 'client', 'domain_type', 'is_primary', 'is_active', 'is_verified']
    list_filter = ['domain_type', 'is_primary', 'is_active', 'is_verified']
    search_fields = ['domain', 'client__name']
    raw_id_fields = ['client']


# ==============================================================================
# STANDALONE ADMINS (para acceso directo si es necesario)
# ==============================================================================

@admin.register(ClientSettings)
class ClientSettingsAdmin(admin.ModelAdmin):
    """Admin standalone para ClientSettings."""
    list_display = ['client', 'company_name', 'primary_color']
    search_fields = ['client__name', 'company_name']
    raw_id_fields = ['client']


@admin.register(ClientEmailSettings)
class ClientEmailSettingsAdmin(admin.ModelAdmin):
    """Admin standalone para ClientEmailSettings."""
    list_display = ['client', 'provider', 'notify_mode', 'is_active']
    list_filter = ['provider', 'notify_mode', 'is_active']
    search_fields = ['client__name']
    raw_id_fields = ['client']


@admin.register(FormConfig)
class FormConfigAdmin(admin.ModelAdmin):
    """Admin standalone para FormConfig."""
    list_display = ['client', 'show_phone', 'show_company', 'show_subject', 'updated_at']
    list_filter = ['show_phone', 'show_company', 'show_subject', 'show_budget']
    search_fields = ['client__name', 'client__slug']
    raw_id_fields = ['client']