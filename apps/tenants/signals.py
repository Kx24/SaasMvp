"""
Signals para automatizar la creación de objetos relacionados.

Cuando se crea un Client, automáticamente se crea su ClientSettings.
Esto evita errores de "Client has no settings".
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Client, ClientSettings


@receiver(post_save, sender=Client)
def create_client_settings(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un Client.
    
    Si es un Client nuevo (created=True), crea sus ClientSettings
    automáticamente con valores por defecto.
    
    Args:
        sender: El modelo que envió la señal (Client)
        instance: La instancia del Client que se guardó
        created: True si es nuevo, False si es actualización
        **kwargs: Otros parámetros del signal
    """
    if created:
        # Cliente nuevo, crear sus settings
        ClientSettings.objects.create(
            client=instance,
            primary_color='#3B82F6',  # Azul Tailwind por defecto
            secondary_color='#1E40AF',
            font_family='Inter, sans-serif'
        )
        print(f"✅ ClientSettings creado automáticamente para {instance.name}")


@receiver(post_save, sender=Client)
def save_client_settings(sender, instance, **kwargs):
    """
    Signal que garantiza que el Client siempre tenga settings.
    
    Si por alguna razón no existen settings, los crea.
    Esto es una red de seguridad adicional.
    """
    if not hasattr(instance, 'settings'):
        ClientSettings.objects.create(client=instance)