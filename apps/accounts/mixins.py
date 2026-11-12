"""
Mixins para Admin Multi-Tenant
==============================
Usar en cualquier ModelAdmin que necesite filtrar por tenant.
"""


class TenantAdminMixin:
    """
    Mixin para filtrar automaticamente por tenant en Django Admin.
    
    Uso:
        class ServiceAdmin(TenantAdminMixin, admin.ModelAdmin):
            tenant_field = 'client'  # Campo FK al tenant
            ...
    
    Comportamiento:
        - Superusers: Ven todos los registros
        - Staff con tenant: Solo ven registros de su tenant
        - Staff sin tenant: No ven nada
    """
    
    # Campo que referencia al tenant (default: 'client'). Admite rutas de
    # relación con '__' para modelos sin FK directa (ej. 'order__client').
    tenant_field = 'client'

    def _user_tenant(self, request):
        profile = getattr(request.user, 'profile', None)
        return getattr(profile, 'client', None)

    def _obj_tenant(self, obj):
        """Recorre `tenant_field` (con '__') sobre el objeto; None si no hay."""
        value = obj
        for part in self.tenant_field.split('__'):
            value = getattr(value, part, None)
            if value is None:
                return None
        return value

    def get_queryset(self, request):
        """Filtra registros por tenant del usuario"""
        qs = super().get_queryset(request)
        
        # Superusers ven todo
        if request.user.is_superuser:
            return qs
        
        # Obtener tenant del usuario
        if hasattr(request.user, 'profile') and request.user.profile.client:
            filter_kwargs = {self.tenant_field: request.user.profile.client}
            return qs.filter(**filter_kwargs)
        
        # Sin tenant asignado = no ve nada
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """Auto-asignar tenant al crear nuevos registros"""
        if not change:  # Solo al crear
            if not request.user.is_superuser:
                if hasattr(request.user, 'profile') and request.user.profile.client:
                    # Asignar tenant del usuario
                    if hasattr(obj, self.tenant_field):
                        setattr(obj, self.tenant_field, request.user.profile.client)
        
        super().save_model(request, obj, form, change)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtrar opciones de FK por tenant"""
        # Si es el campo tenant, solo mostrar el tenant del usuario
        if db_field.name == self.tenant_field:
            if not request.user.is_superuser:
                if hasattr(request.user, 'profile') and request.user.profile.client:
                    from apps.tenants.models import Client
                    kwargs["queryset"] = Client.objects.filter(pk=request.user.profile.client.pk)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def _same_tenant(self, request, obj):
        tenant = self._user_tenant(request)
        return tenant is not None and self._obj_tenant(obj) == tenant

    def has_change_permission(self, request, obj=None):
        """Solo puede editar registros de su tenant (y si Django le da el permiso)."""
        if not super().has_change_permission(request, obj):
            return False
        if request.user.is_superuser or obj is None:
            return True
        return self._same_tenant(request, obj)

    def has_view_permission(self, request, obj=None):
        """Solo puede ver registros de su tenant (y si Django le da el permiso)."""
        if not super().has_view_permission(request, obj):
            return False
        if request.user.is_superuser or obj is None:
            return True
        return self._same_tenant(request, obj)

    def has_delete_permission(self, request, obj=None):
        """Solo puede eliminar registros de su tenant (y si Django le da el permiso)."""
        if not super().has_delete_permission(request, obj):
            return False
        if request.user.is_superuser or obj is None:
            return True
        return self._same_tenant(request, obj)


class TenantAdminReadOnlyMixin(TenantAdminMixin):
    """
    Version de solo lectura para usuarios no-admin del tenant.
    
    Uso para roles tipo 'viewer' o 'editor' limitado.
    """
    
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin
        
        return False
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            if not request.user.profile.can_edit:
                return False
        
        return super().has_change_permission(request, obj)
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile'):
            return request.user.profile.is_admin
        
        return False