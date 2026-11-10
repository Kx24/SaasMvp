"""
Managers personalizados para el sistema multi-tenant
"""
from django.db import models


class TenantAwareManager(models.Manager):
    """
    Manager con helpers de conveniencia para modelos con FK a Client.

    No filtra automáticamente por tenant: cada vista debe filtrar
    explícitamente con `.filter(client=request.client)` o usar
    `for_client(client)`. Antes existía un auto-filtro basado en un
    atributo de clase `_current_client`, pero nunca se seteaba en código
    de request real (ni middleware ni vistas lo tocaban) -- en
    producción no filtraba nada, y de haberse llegado a usar habría sido
    un riesgo real: un atributo de clase se comparte entre requests
    concurrentes de distintos tenants. Se eliminó (#MED-02); ver
    apps/tenants/tests_isolation.py para la suite que prueba el
    aislamiento real (filtrado explícito por vista).
    """

    def for_client(self, client):
        """
        Método explícito para obtener datos de un cliente específico.
        
        Ignora el _current_client y filtra directamente por el cliente dado.
        
        Uso:
            Section.objects.for_client(client1).all()
        """
        # Usar el queryset base sin el filtro automático
        return super().get_queryset().filter(client=client)
    
    def active(self):
        """
        Retorna solo registros activos.
        
        Uso:
            Section.objects.active()
        """
        return self.filter(is_active=True)
    
    def featured(self):
        """
        Retorna solo registros destacados (si el modelo tiene is_featured).
        
        Uso:
            Service.objects.featured()
        """
        if hasattr(self.model, 'is_featured'):
            return self.filter(is_featured=True, is_active=True)
        return self.filter(is_active=True)
    
    def ordered(self):
        """
        Retorna registros ordenados por el campo 'order'.

        Uso:
            Section.objects.ordered()
        """
        if hasattr(self.model, 'order'):
            return self.order_by('order')
        return self.all()