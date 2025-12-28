"""
Admin para Accounts
===================
Gestion de usuarios y sus perfiles (vinculacion a tenants)

IMPORTANTE: El UserProfile se crea automaticamente via signal.
El inline solo permite EDITAR el perfil existente, no crear uno nuevo.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    """
    Inline para editar perfil desde el usuario.
    
    NOTA: El perfil se crea automaticamente via signal post_save.
    Este inline solo permite editar, no crear.
    """
    model = UserProfile
    can_delete = False
    verbose_name = 'Perfil / Tenant'
    
    fields = ['client', 'role']
    
    # NO agregar extra forms - el perfil ya existe via signal
    extra = 0
    max_num = 1
    min_num = 0
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Solo mostrar clientes activos"""
        if db_field.name == "client":
            from apps.tenants.models import Client
            kwargs["queryset"] = Client.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def get_queryset(self, request):
        """Solo mostrar perfiles existentes"""
        return super().get_queryset(request)
    
    def has_add_permission(self, request, obj=None):
        """
        No permitir agregar desde el inline.
        El perfil se crea automaticamente via signal.
        """
        return False


class CustomUserAdmin(BaseUserAdmin):
    """
    Admin de usuarios extendido con perfil de tenant.
    
    El inline de UserProfile solo aparece para usuarios EXISTENTES,
    no al crear un usuario nuevo (el perfil se crea via signal).
    """
    inlines = [UserProfileInline]
    
    list_display = [
        'username', 
        'email', 
        'get_client', 
        'get_role',
        'is_active',
        'is_staff', 
        'is_superuser',
    ]
    list_filter = [
        'is_active',
        'is_staff', 
        'is_superuser', 
        'profile__client',
        'profile__role',
    ]
    search_fields = ['username', 'email', 'profile__client__name']
    
    def get_client(self, obj):
        if obj.is_superuser:
            return "🔑 Superadmin"
        if hasattr(obj, 'profile') and obj.profile.client:
            return obj.profile.client.name
        return "⚠️ Sin asignar"
    get_client.short_description = 'Tenant'
    get_client.admin_order_field = 'profile__client__name'
    
    def get_role(self, obj):
        if obj.is_superuser:
            return "superuser"
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return "-"
    get_role.short_description = 'Rol'
    
    def get_inline_instances(self, request, obj=None):
        """
        Solo mostrar inline de perfil si el usuario YA EXISTE.
        Al crear usuario nuevo, no mostrar el inline (se crea via signal).
        """
        if obj is None:
            # Usuario nuevo - no mostrar inline
            return []
        return super().get_inline_instances(request, obj)
    
    def get_queryset(self, request):
        """
        Superusers ven todos los usuarios.
        Staff solo ve usuarios de su tenant.
        """
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        # Staff solo ve usuarios de su tenant
        if hasattr(request.user, 'profile') and request.user.profile.client:
            return qs.filter(profile__client=request.user.profile.client)
        
        return qs.none()
    
    def has_change_permission(self, request, obj=None):
        """Solo puede editar usuarios de su tenant"""
        if request.user.is_superuser:
            return True
        
        if obj is None:
            return True
        
        # No puede editar superusers
        if obj.is_superuser:
            return False
        
        # Solo puede editar usuarios de su tenant
        if hasattr(request.user, 'profile') and hasattr(obj, 'profile'):
            if request.user.profile.client == obj.profile.client:
                return True
        
        return False


# Re-registrar User con el admin personalizado
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Admin directo de UserProfile (para superadmin)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'client', 'role', 'created_at']
    list_filter = ['client', 'role']
    search_fields = ['user__username', 'user__email', 'client__name']
    raw_id_fields = ['user', 'client']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        if request.user.is_superuser:
            return qs
        
        if hasattr(request.user, 'profile') and request.user.profile.client:
            return qs.filter(client=request.user.profile.client)
        
        return qs.none()
    
    def has_module_permission(self, request):
        """Solo superusers ven este modulo directamente"""
        return request.user.is_superuser