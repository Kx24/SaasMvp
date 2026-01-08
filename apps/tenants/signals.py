"""
Signals para automatizar la creación de objetos relacionados.

Cuando se crea un Client, automáticamente se crean:
- ClientSettings
- ClientEmailSettings
- FormConfig

Usa get_or_create para evitar duplicados.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Client, ClientSettings, ClientEmailSettings, FormConfig


@receiver(post_save, sender=Client)
def create_client_related_objects(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un Client.
    
    Crea ClientSettings, ClientEmailSettings y FormConfig si no existen.
    Usa get_or_create para ser idempotente (evita duplicados).
    """
    # Crear o obtener ClientSettings
    settings, settings_created = ClientSettings.objects.get_or_create(
        client=instance,
        defaults={
            'primary_color': '#3B82F6',
            'secondary_color': '#1E40AF',
            'font_family': 'Inter, sans-serif',
            'company_name': instance.company_name or instance.name,
        }
    )
    
    if settings_created:
        print(f"✅ ClientSettings creado para {instance.name}")
    
    # Crear o obtener ClientEmailSettings
    email_settings, email_created = ClientEmailSettings.objects.get_or_create(
        client=instance,
        defaults={
            'provider': 'none',
            'notify_mode': 'dashboard',
        }
    )
    
    if email_created:
        print(f"✅ ClientEmailSettings creado para {instance.name}")
    
    # Crear o obtener FormConfig
    form_config, form_created = FormConfig.objects.get_or_create(
        client=instance,
        defaults={
            'show_phone': True,
            'show_subject': True,
        }
    )
    
    if form_created:
        print(f"✅ FormConfig creado para {instance.name}")