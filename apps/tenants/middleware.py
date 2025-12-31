"""
Middleware Multi-Tenant con soporte para:
- Múltiples dominios por cliente
- Wildcard subdomains (*.tuapp.cl)
- Parámetro ?tenant= para desarrollo
- Fallback a tenant default
- SEGURIDAD: Validación de acceso por usuario
- THREAD-LOCAL: Para acceso desde template loader
"""
import threading
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib import messages

# Thread-local storage para el tenant actual
_thread_locals = threading.local()


def get_current_tenant():
    """
    Obtiene el tenant actual desde cualquier parte del código.
    Útil para template loaders, managers, etc.
    """
    return getattr(_thread_locals, 'tenant', None)


def get_current_request():
    """
    Obtiene el request actual desde cualquier parte del código.
    """
    return getattr(_thread_locals, 'request', None)


class TenantMiddleware:
    """
    Middleware que detecta el tenant basándose en:
    1. Parámetro GET ?tenant=slug (solo en DEBUG)
    2. Dominio exacto en tabla Domain
    3. Wildcard subdomain (cliente.tuapp.cl)
    4. Fallback a DEFAULT_TENANT_SLUG
    
    SEGURIDAD:
    - Usuarios logueados solo pueden acceder a SU tenant
    - Superusers pueden acceder a cualquier tenant
    
    THREAD-LOCAL:
    - Guarda tenant en thread-local para acceso desde template loader
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.base_domain = getattr(settings, 'BASE_DOMAIN', 'tuapp.cl')
        self.default_tenant = getattr(settings, 'DEFAULT_TENANT_SLUG', None)
        self.saas_domain = getattr(settings, 'SAAS_DOMAIN', None)
    
    def __call__(self, request):
        from apps.tenants.models import Client, Domain
        
        host = request.get_host()
        domain = host.split(':')[0].lower()
        
        client = None
        
        # ============================================================
        # 1. RUTAS EXCLUIDAS (admin, static, media)
        # ============================================================
        excluded_paths = ['/superadmin/', '/static/', '/media/', '/__debug__/']
        if any(request.path.startswith(p) for p in excluded_paths):
            try:
                if settings.DEBUG and request.GET.get('tenant'):
                    client = Client.objects.get(
                        slug=request.GET.get('tenant'),
                        is_active=True
                    )
                else:
                    domain_obj = Domain.objects.select_related('client').get(
                        domain=domain,
                        is_active=True,
                        client__is_active=True
                    )
                    client = domain_obj.client
            except (Client.DoesNotExist, Domain.DoesNotExist):
                client = None
            
            request.client = client
            # Guardar en thread-local
            _thread_locals.tenant = client
            _thread_locals.request = request
            
            response = self.get_response(request)
            
            # Limpiar thread-local
            _thread_locals.tenant = None
            _thread_locals.request = None
            
            return response
        
        # ============================================================
        # 2. PARÁMETRO ?tenant= (solo en DEBUG)
        # ============================================================
        if settings.DEBUG and request.GET.get('tenant'):
            tenant_slug = request.GET.get('tenant')
            try:
                client = Client.objects.get(slug=tenant_slug, is_active=True)
                
                # VALIDAR ACCESO DEL USUARIO
                redirect_response = self._validate_user_access(request, client)
                if redirect_response:
                    return redirect_response
                
                request.client = client
                _thread_locals.tenant = client
                _thread_locals.request = request
                
                response = self.get_response(request)
                
                _thread_locals.tenant = None
                _thread_locals.request = None
                
                return response
            except Client.DoesNotExist:
                pass
        
        # ============================================================
        # 3. DOMINIO DEL SAAS (landing page del servicio)
        # ============================================================
        if self.saas_domain and domain in [self.saas_domain, f'www.{self.saas_domain}']:
            request.client = None
            request.is_saas_landing = True
            return self.get_response(request)
        
        # ============================================================
        # 4. BÚSQUEDA POR DOMINIO EXACTO
        # ============================================================
        try:
            domain_obj = Domain.objects.select_related('client').get(
                domain=domain,
                is_active=True,
                client__is_active=True
            )
            client = domain_obj.client
            
            # VALIDAR ACCESO DEL USUARIO
            redirect_response = self._validate_user_access(request, client)
            if redirect_response:
                return redirect_response
            
            request.client = client
            request.current_domain = domain_obj
            _thread_locals.tenant = client
            _thread_locals.request = request
            
            response = self.get_response(request)
            
            _thread_locals.tenant = None
            _thread_locals.request = None
            
            return response
        except Domain.DoesNotExist:
            pass
        
        # ============================================================
        # 5. WILDCARD SUBDOMAIN (cliente.tuapp.cl)
        # ============================================================
        if domain.endswith(f'.{self.base_domain}'):
            subdomain = domain.replace(f'.{self.base_domain}', '')
            
            if subdomain == 'www':
                request.client = None
                request.is_saas_landing = True
                return self.get_response(request)
            
            try:
                client = Client.objects.get(slug=subdomain, is_active=True)
                
                # VALIDAR ACCESO DEL USUARIO
                redirect_response = self._validate_user_access(request, client)
                if redirect_response:
                    return redirect_response
                
                domain_obj, created = Domain.objects.get_or_create(
                    domain=domain,
                    defaults={
                        'client': client,
                        'domain_type': 'subdomain',
                        'is_active': True,
                        'is_verified': True,
                    }
                )
                
                request.client = client
                request.current_domain = domain_obj
                _thread_locals.tenant = client
                _thread_locals.request = request
                
                response = self.get_response(request)
                
                _thread_locals.tenant = None
                _thread_locals.request = None
                
                return response
            except Client.DoesNotExist:
                pass
        
        # ============================================================
        # 6. LOCALHOST / DESARROLLO
        # ============================================================
        localhost_domains = ['localhost', '127.0.0.1', 'testserver']
        if domain in localhost_domains:
            if self.default_tenant:
                try:
                    client = Client.objects.get(slug=self.default_tenant, is_active=True)
                    
                    # VALIDAR ACCESO DEL USUARIO
                    redirect_response = self._validate_user_access(request, client)
                    if redirect_response:
                        return redirect_response
                    
                    request.client = client
                    _thread_locals.tenant = client
                    _thread_locals.request = request
                    
                    response = self.get_response(request)
                    
                    _thread_locals.tenant = None
                    _thread_locals.request = None
                    
                    return response
                except Client.DoesNotExist:
                    pass
            
            client = Client.objects.filter(is_active=True).first()
            if client:
                # VALIDAR ACCESO DEL USUARIO
                redirect_response = self._validate_user_access(request, client)
                if redirect_response:
                    return redirect_response
                
                request.client = client
                _thread_locals.tenant = client
                _thread_locals.request = request
                
                response = self.get_response(request)
                
                _thread_locals.tenant = None
                _thread_locals.request = None
                
                return response
        
        # ============================================================
        # 7. TENANT NO ENCONTRADO
        # ============================================================
        return render(request, 'errors/tenant_not_found.html', {
            'domain': domain,
            'host': host,
            'base_domain': self.base_domain,
        }, status=404)
    
    def _validate_user_access(self, request, client):
        """
        Valida que el usuario tenga acceso al tenant.
        """
        user = request.user
        
        if not user.is_authenticated:
            return None
        
        if user.is_superuser:
            request.is_superuser_override = True
            return None
        
        if hasattr(user, 'profile') and user.profile.client:
            user_client = user.profile.client
            
            if user_client.id != client.id:
                if settings.DEBUG:
                    messages.warning(
                        request,
                        f'No tienes acceso a "{client.name}". Redirigido a tu sitio.'
                    )
                    return HttpResponseRedirect(f'/?tenant={user_client.slug}')
                else:
                    return render(request, 'errors/access_denied.html', {
                        'user_tenant': user_client.name,
                        'requested_tenant': client.name,
                    }, status=403)
        
        elif hasattr(user, 'profile') and user.profile.client is None:
            if not user.is_staff:
                return render(request, 'errors/no_tenant_assigned.html', {
                    'user': user,
                }, status=403)
        
        return None


class TenantAdminMiddleware:
    """
    Middleware adicional para el admin.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/superadmin/'):
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not request.user.is_superuser:
                    if hasattr(request.user, 'profile') and request.user.profile.client:
                        request.admin_client = request.user.profile.client
        
        return self.get_response(request)