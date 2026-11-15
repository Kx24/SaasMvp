"""
Modelo de Accounts - Vincula usuarios a tenants
================================================

Cada usuario (excepto superusers) pertenece a UN tenant.
"""
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

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

    # Agregar al modelo UserProfile existente:

    invitation_token = models.UUIDField(
        null=True,
        blank=True,
        unique=True,
    )

    invitation_expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    invited_at = models.DateTimeField(
        null=True,
        blank=True,
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

    # --- Invitación / recuperación de contraseña -----------------------
    # apps/accounts/views.py (set_password_view, request_password_reset_view)
    # llamaba estos tres métodos sin que existieran: AttributeError -> 500 en
    # el enlace del correo de bienvenida y en "olvidé mi contraseña" para
    # cualquier email registrado (BOLT-12, hallazgo incidental).

    def generate_invitation_token(self, days=7):
        """Genera un token nuevo de un solo uso, válido `days` días. Devuelve el UUID."""
        now = timezone.now()
        self.invitation_token = uuid.uuid4()
        self.invitation_expires_at = now + timedelta(days=days)
        self.invited_at = now
        self.save(update_fields=['invitation_token', 'invitation_expires_at', 'invited_at', 'updated_at'])
        return self.invitation_token

    def is_invitation_valid(self):
        """True si hay token y no expiró. Sin fecha de expiración se considera inválido."""
        return bool(
            self.invitation_token
            and self.invitation_expires_at
            and self.invitation_expires_at > timezone.now()
        )

    def clear_invitation(self):
        """Invalida el token (se usa una sola vez)."""
        self.invitation_token = None
        self.invitation_expires_at = None
        self.save(update_fields=['invitation_token', 'invitation_expires_at', 'updated_at'])


# ============================================================
# SIGNALS - Crear perfil automaticamente
# ============================================================

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)