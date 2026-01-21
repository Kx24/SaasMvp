# apps/orders/admin.py
"""
Admin para gestión de Planes y Órdenes.

Incluye:
- Gestión completa de planes
- Vista de órdenes con filtros y acciones
- Inline de logs de pago
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from .models import Plan, Order, PaymentLog


# ==============================================================================
# PLAN ADMIN
# ==============================================================================

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Admin para gestión de planes de suscripción."""
    
    list_display = [
        'name',
        'slug',
        'formatted_price',
        'is_active',
        'is_featured',
        'display_order',
        'orders_count',
    ]
    
    list_filter = [
        'is_active',
        'is_featured',
        'has_custom_domain',
        'has_priority_support',
    ]
    
    search_fields = ['name', 'slug', 'description']
    
    list_editable = ['is_active', 'is_featured', 'display_order']
    
    prepopulated_fields = {'slug': ('name',)}
    
    readonly_fields = ['created_at', 'updated_at', 'orders_count']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('name', 'slug', 'tagline', 'description')
        }),
        ('Precios', {
            'fields': ('price', 'renewal_price')
        }),
        ('Características', {
            'fields': ('features', 'available_themes'),
            'description': 'Ingresa como JSON array. Ej: ["Feature 1", "Feature 2"]'
        }),
        ('Límites', {
            'fields': (
                'max_pages',
                'max_services', 
                'max_images',
                'max_storage_mb'
            )
        }),
        ('Opciones Incluidas', {
            'fields': (
                'has_custom_domain',
                'has_analytics',
                'has_priority_support',
                'has_white_label'
            )
        }),
        ('Display', {
            'fields': ('is_active', 'is_featured', 'display_order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_price(self, obj):
        """Muestra precio formateado."""
        return f"${obj.price:,.0f} CLP"
    formatted_price.short_description = 'Precio'
    formatted_price.admin_order_field = 'price'
    
    def orders_count(self, obj):
        """Cuenta órdenes de este plan."""
        total = obj.orders.count()
        completed = obj.orders.filter(status='completed').count()
        return f"{completed}/{total}"
    orders_count.short_description = 'Completadas/Total'


# ==============================================================================
# PAYMENT LOG INLINE
# ==============================================================================

class PaymentLogInline(admin.TabularInline):
    """Inline para ver logs de pago en Order."""
    
    model = PaymentLog
    extra = 0
    readonly_fields = [
        'action',
        'mp_payment_id',
        'status',
        'status_detail',
        'amount',
        'ip_address',
        'created_at'
    ]
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# ==============================================================================
# ORDER ADMIN
# ==============================================================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin para gestión de órdenes."""
    
    list_display = [
        'order_number',
        'email',
        'plan',
        'formatted_amount',
        'status_badge',
        'client_link',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'plan',
        'created_at',
        'paid_at',
        'completed_at',
    ]
    
    search_fields = [
        'order_number',
        'email',
        'buyer_name',
        'mp_payment_id',
        'billing_rut',
    ]
    
    readonly_fields = [
        'uuid',
        'order_number',
        'created_at',
        'updated_at',
        'paid_at',
        'completed_at',
        'onboarding_url_display',
        'token_status',
        'mp_response_data',
    ]
    
    raw_id_fields = ['client']
    
    date_hierarchy = 'created_at'
    
    inlines = [PaymentLogInline]
    
    fieldsets = (
        ('Orden', {
            'fields': (
                'uuid',
                'order_number',
                'status',
                'plan',
                'client',
            )
        }),
        ('Comprador', {
            'fields': (
                'email',
                'buyer_name',
                'buyer_phone',
            )
        }),
        ('Pago', {
            'fields': (
                'amount',
                'currency',
                'mp_payment_id',
                'mp_status',
                'mp_status_detail',
                'mp_payment_method',
                'mp_payment_type',
            )
        }),
        ('Onboarding', {
            'fields': (
                'onboarding_token',
                'token_expires_at',
                'token_status',
                'onboarding_url_display',
            )
        }),
        ('Facturación', {
            'fields': (
                'billing_rut',
                'billing_razon_social',
                'billing_giro',
                'billing_direccion',
                'billing_comuna',
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'ip_address',
                'user_agent',
                'notes',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'paid_at',
                'completed_at',
                'expires_at',
            ),
            'classes': ('collapse',)
        }),
        ('Debug MP', {
            'fields': ('mp_response_data',),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_expired',
        'resend_onboarding_email',
        'regenerate_token',
    ]
    
    def formatted_amount(self, obj):
        """Muestra monto formateado."""
        return f"${obj.amount:,.0f}"
    formatted_amount.short_description = 'Monto'
    formatted_amount.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """Muestra estado con colores."""
        colors = {
            'pending': '#6c757d',      # Gris
            'processing': '#17a2b8',   # Cyan
            'paid': '#28a745',         # Verde
            'onboarding': '#007bff',   # Azul
            'completed': '#28a745',    # Verde
            'failed': '#dc3545',       # Rojo
            'cancelled': '#6c757d',    # Gris
            'refunded': '#ffc107',     # Amarillo
            'expired': '#dc3545',      # Rojo
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def client_link(self, obj):
        """Link al cliente si existe."""
        if obj.client:
            url = reverse('admin:tenants_client_change', args=[obj.client.pk])
            return format_html('<a href="{}">{}</a>', url, obj.client.name)
        return '-'
    client_link.short_description = 'Cliente'
    
    def token_status(self, obj):
        """Muestra estado del token."""
        if not obj.onboarding_token:
            return format_html('<span style="color: #6c757d;">Sin token</span>')
        
        if obj.is_token_valid():
            days = obj.days_until_token_expires
            return format_html(
                '<span style="color: #28a745;">✓ Válido ({} días restantes)</span>',
                days
            )
        else:
            return format_html('<span style="color: #dc3545;">✗ Expirado</span>')
    token_status.short_description = 'Estado Token'
    
    def onboarding_url_display(self, obj):
        """Muestra URL de onboarding clickeable."""
        url = obj.get_onboarding_url()
        if url:
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return '-'
    onboarding_url_display.short_description = 'URL Onboarding'
    
    # ==================== ACTIONS ====================
    
    @admin.action(description='Marcar como expiradas')
    def mark_as_expired(self, request, queryset):
        """Marca órdenes seleccionadas como expiradas."""
        updated = 0
        for order in queryset.filter(status__in=['paid', 'onboarding']):
            order.mark_as_expired()
            updated += 1
        self.message_user(request, f'{updated} órdenes marcadas como expiradas.')
    
    @admin.action(description='Reenviar email de onboarding')
    def resend_onboarding_email(self, request, queryset):
        """Reenvía email de onboarding (placeholder)."""
        # TODO: Implementar cuando tengamos email dispatcher
        count = queryset.filter(status='paid').count()
        self.message_user(
            request,
            f'Se reenviarían {count} emails (funcionalidad pendiente).'
        )
    
    @admin.action(description='Regenerar token de onboarding')
    def regenerate_token(self, request, queryset):
        """Regenera tokens de onboarding."""
        updated = 0
        for order in queryset.filter(status__in=['paid', 'onboarding']):
            order.generate_onboarding_token()
            updated += 1
        self.message_user(request, f'{updated} tokens regenerados.')


# ==============================================================================
# PAYMENT LOG ADMIN (standalone para auditoría)
# ==============================================================================

@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    """Admin para auditoría de logs de pago."""
    
    list_display = [
        'order',
        'action',
        'status',
        'amount',
        'ip_address',
        'created_at',
    ]
    
    list_filter = [
        'action',
        'status',
        'created_at',
    ]
    
    search_fields = [
        'order__order_number',
        'mp_payment_id',
    ]
    
    readonly_fields = [
        'order',
        'action',
        'mp_payment_id',
        'status',
        'status_detail',
        'amount',
        'raw_data',
        'ip_address',
        'created_at',
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
