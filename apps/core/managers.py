"""
Managers personalizados
"""
from django.db import models


class TenantAwareManager(models.Manager):
    """Manager que filtra por tenant"""
    
    def get_queryset(self):
        qs = super().get_queryset()
        client = getattr(self.model, '_current_client', None)
        if client is None:
            return qs.none()
        return qs.filter(client=client)
    
    def for_client(self, client):
        """Fuerza un cliente específico"""
        return super().get_queryset().filter(client=client)