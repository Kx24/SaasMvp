"""
Modelo de Accounts - Vincula usuarios a tenants
================================================

Cada usuario (excepto superusers) pertenece a UN tenant.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class UserProfile(models.Model):
    """
    Extiende el usuario de Django para vincularlo a un tenant.
    
    Reglas:
    - Superusers: client puede ser None (ven todo)
    - Staff/Users: client es obligatorio (solo ven su tenant)
    """
    
    ROLE_CHOICES = [
        ('owner', 'Propietario'),      # Dueno del tenant, acceso total
        ('admin', 'Administrador'),     # Puede gestionar contenido
        ('editor', 'Editor'),           # Solo edita contenido
        ('viewer', 'Visualizador'),     # Solo lectura
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    client = models.ForeignKey(
        'tenants.Client',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        help_text="Tenant al que pertenece este usuario. Null solo para superusers."
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='editor',
        help_text="Rol del usuario en el tenant"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
    
    def __str__(self):
        client_name = self.client.name if self.client else "Sin tenant"
        return f"{self.user.username} ({client_name})"
    
    @property
    def is_owner(self):
        return self.role == 'owner'
    
    @property
    def is_admin(self):
        return self.role in ['owner', 'admin']
    
    @property
    def can_edit(self):
        return self.role in ['owner', 'admin', 'editor']


# ============================================================
# SIGNALS - Crear perfil automaticamente
# ============================================================

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)