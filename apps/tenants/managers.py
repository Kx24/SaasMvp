"""
Managers personalizados para filtrado automático por tenant.

Los managers permiten filtrar automáticamente los QuerySets por cliente,
evitando que los datos de un cliente se mezclen con otro.

Inspirado en: django.contrib.sites.managers.CurrentSiteManager
"""
from django.db import models


class TenantManager(models.Manager):
    """
    Manager básico que permite filtrar por tenant manualmente.
    
    Uso:
        # En un modelo:
        class Section(models.Model):
            client = models.ForeignKey(Client)
            objects = TenantManager()
        
        # En una vista:
        sections = Section.objects.for_client(request.client)
    """
    
    def __init__(self, client_field='client'):
        """
        Args:
            client_field (str): Nombre del campo ForeignKey al modelo Client
                               Default: 'client'
        """
        super().__init__()
        self._client_field = client_field
    
    def get_queryset(self):
        """
        Retorna el queryset base sin filtrar.
        Útil para operaciones internas o de superusuario.
        """
        return super().get_queryset()
    
    def for_client(self, client):
        """
        Filtra los resultados por un cliente específico.
        
        Args:
            client (Client): Instancia del cliente a filtrar
            
        Returns:
            QuerySet: Objetos que pertenecen solo a ese cliente
            
        Example:
            # En una vista:
            sections = Section.objects.for_client(request.client)
            
            # Esto genera SQL como:
            # SELECT * FROM website_section WHERE client_id = 1
        """
        if client is None:
            # Si no hay cliente, retornar queryset vacío
            # Esto evita errores cuando request.client no existe
            return self.none()
        
        # Filtrar usando el campo client
        return self.get_queryset().filter(**{self._client_field: client})
    
    def active(self):
        """
        Shortcut para filtrar solo objetos activos.
        
        Returns:
            QuerySet: Objetos con is_active=True
            
        Example:
            active_sections = Section.objects.active()
        """
        return self.get_queryset().filter(is_active=True)


class TenantAwareQuerySet(models.QuerySet):
    """
    QuerySet personalizado con métodos útiles para multi-tenancy.
    
    Permite encadenar métodos de forma intuitiva:
        Section.objects.for_client(client).active().ordered()
    """
    
    def for_client(self, client):
        """
        Filtra por cliente.
        
        Args:
            client (Client): Cliente a filtrar
            
        Returns:
            TenantAwareQuerySet: QuerySet filtrado
        """
        if client is None:
            return self.none()
        return self.filter(client=client)
    
    def active(self):
        """
        Filtra solo objetos activos.
        
        Returns:
            TenantAwareQuerySet: Solo objetos con is_active=True
        """
        return self.filter(is_active=True)
    
    def ordered(self):
        """
        Ordena por el campo 'order' si existe en el modelo.
        
        Muchos modelos CMS tienen un campo 'order' para ordenar contenido.
        Este método lo aplica automáticamente si existe.
        
        Returns:
            TenantAwareQuerySet: QuerySet ordenado
        """
        # Verificar si el modelo tiene campo 'order'
        if 'order' in [f.name for f in self.model._meta.get_fields()]:
            return self.order_by('order')
        return self


class TenantAwareManager(models.Manager):
    """
    Manager completo que combina TenantManager con QuerySet personalizado.
    
    Este es el manager que usarás en la mayoría de tus modelos.
    Proporciona todos los métodos útiles de TenantManager + TenantAwareQuerySet.
    
    Uso en un modelo:
        class Section(models.Model):
            client = models.ForeignKey(Client, on_delete=models.CASCADE)
            title = models.CharField(max_length=200)
            is_active = models.BooleanField(default=True)
            order = models.IntegerField(default=0)
            
            # Manager personalizado
            objects = TenantAwareManager()
        
        # Uso en vistas:
        sections = Section.objects.for_client(request.client).active().ordered()
        
        # Esto encadena:
        # 1. for_client(request.client) → filtra por cliente
        # 2. active() → solo is_active=True
        # 3. ordered() → ordena por campo 'order'
    """
    
    def get_queryset(self):
        """
        Retorna el QuerySet personalizado en lugar del default.
        
        Esto permite usar métodos como .for_client(), .active(), etc.
        """
        return TenantAwareQuerySet(self.model, using=self._db)
    
    def for_client(self, client):
        """Acceso directo al método for_client del QuerySet"""
        return self.get_queryset().for_client(client)
    
    def active(self):
        """Acceso directo al método active del QuerySet"""
        return self.get_queryset().active()
    
    def ordered(self):
        """Acceso directo al método ordered del QuerySet"""
        return self.get_queryset().ordered()


# ==================== EJEMPLO DE USO ====================
"""
# En apps/website/models.py:

from apps.tenants.managers import TenantAwareManager

class Section(models.Model):
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Usar el manager personalizado
    objects = TenantAwareManager()


# En una vista (apps/website/views.py):

def home(request):
    # request.client será inyectado por TenantMiddleware (Card #4)
    
    # Forma larga (explícita):
    sections = Section.objects.for_client(request.client).filter(is_active=True).order_by('order')
    
    # Forma corta (con manager):
    sections = Section.objects.for_client(request.client).active().ordered()
    
    # Ambas hacen lo mismo, pero la segunda es más limpia


# En el admin (apps/website/admin.py):

class SectionAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Si el usuario no es superadmin, solo ver su tenant
        if not request.user.is_superuser:
            # Asumiendo que user tiene un perfil con tenant
            return qs.for_client(request.user.profile.client)
        
        return qs
"""