"""
Managers personalizados para el sistema multi-tenant
"""
from django.db import models


class TenantAwareManager(models.Manager):
    """
    Manager que filtra automáticamente por el tenant actual.
    
    Uso:
        # En el modelo
        objects = TenantAwareManager()
        
        # En el middleware o vista
        Section._current_client = request.client
        
        # Ahora las queries se filtran automáticamente
        Section.objects.all()  # Solo del cliente actual
    """
    
    def get_queryset(self):
        """
        Retorna queryset filtrado por el cliente actual.
        
        Si _current_client está definido en el modelo, filtra por ese cliente.
        Si no, retorna el queryset completo (para admin de superuser).
        """
        queryset = super().get_queryset()
        
        # Obtener el cliente actual del modelo
        if hasattr(self.model, '_current_client'):
            current_client = getattr(self.model, '_current_client', None)
            
            if current_client is not None:
                # Filtrar por el cliente actual
                queryset = queryset.filter(client=current_client)
        
        return queryset
    
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


class TenantQuerySet(models.QuerySet):
    """
    QuerySet personalizado con métodos útiles para multi-tenant.
    """
    
    def for_client(self, client):
        """Filtrar por cliente"""
        return self.filter(client=client)
    
    def active(self):
        """Solo registros activos"""
        return self.filter(is_active=True)
    
    def featured(self):
        """Solo registros destacados"""
        if hasattr(self.model, 'is_featured'):
            return self.filter(is_featured=True, is_active=True)
        return self.filter(is_active=True)
    
    def ordered(self):
        """Ordenados por campo order"""
        if hasattr(self.model, 'order'):
            return self.order_by('order')
        return self


class TenantManager(models.Manager):
    """
    Manager que usa TenantQuerySet.
    
    Alternativa más robusta a TenantAwareManager.
    Proporciona los mismos métodos tanto en el manager como en el queryset.
    """
    
    def get_queryset(self):
        """Retorna TenantQuerySet con filtrado automático"""
        queryset = TenantQuerySet(self.model, using=self._db)
        
        # Auto-filtrar si hay cliente actual
        if hasattr(self.model, '_current_client'):
            current_client = getattr(self.model, '_current_client', None)
            if current_client is not None:
                queryset = queryset.filter(client=current_client)
        
        return queryset
    
    def for_client(self, client):
        """Filtrar por cliente específico (ignora _current_client)"""
        return TenantQuerySet(self.model, using=self._db).for_client(client)
    
    def active(self):
        """Solo registros activos"""
        return self.get_queryset().active()
    
    def featured(self):
        """Solo registros destacados"""
        return self.get_queryset().featured()
    
    def ordered(self):
        """Ordenados por campo order"""
        return self.get_queryset().ordered()