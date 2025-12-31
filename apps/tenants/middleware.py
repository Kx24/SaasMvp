"""
TenantMiddleware - Detección de tenant por dominio
==================================================

Funcionalidades:
- Detecta tenant por dominio, subdominio, o parámetro ?tenant=
- Thread-local storage para acceso desde template loader
- Manejo graceful de errores (no 500 si no hay tenant)
- Logging claro para debugging

Orden de detección:
1. Parámetro GET ?tenant=slug (solo en DEBUG)
2. Dominio exacto en tabla Domain
3. DEFAULT_TENANT_SLUG de settings
4. Respuesta amigable si no encuentra nada
"""

import logging
import threading

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# ============================================================
# THREAD-LOCAL STORAGE
# ============================================================
# Permite acceder al tenant actual desde cualquier parte del código
# (especialmente desde el template loader)

_thread_locals = threading.local()


def get_current_tenant():
    """
    Obtiene el tenant actual del thread-local storage.
    
    Returns:
        Client instance o None
    """
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant):
    """
    Establece el tenant actual en thread-local storage.
    
    Args:
        tenant: Client instance o None
    """
    _thread_locals.tenant = tenant


def clear_current_tenant():
    """Limpia el tenant del thread-local storage."""
    if hasattr(_thread_locals, 'tenant'):
        del _thread_locals.tenant


# ============================================================
# MIDDLEWARE
# ============================================================

class TenantMiddleware(MiddlewareMixin):
    """
    Middleware que detecta y establece el tenant actual.
    
    Agrega `request.client` con el Client detectado.
    """
    
    # Paths que no requieren tenant (admin, static, etc.)
    EXEMPT_PATHS = [
        '/superadmin/',
        '/admin/',
        '/static/',
        '/media/',
        '/__debug__/',
        '/favicon.ico',
        '/robots.txt',
        '/health/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        # Limpiar tenant anterior
        clear_current_tenant()
        
        # Verificar si el path está exento
        path = request.path
        if self._is_exempt_path(path):
            request.client = None
            return self.get_response(request)
        
        # Detectar tenant
        client = self._detect_tenant(request)
        
        # Establecer en request y thread-local
        request.client = client
        set_current_tenant(client)
        
        # Si no hay tenant y no es path exento
        if client is None:
            return self._handle_no_tenant(request)
        
        # Log para debugging
        logger.debug(f"[Tenant] {request.get_host()} → {client.name}")
        
        # Continuar con la request
        response = self.get_response(request)
        
        # Limpiar después de la request
        clear_current_tenant()
        
        return response
    
    def _is_exempt_path(self, path):
        """Verifica si el path está exento de detección de tenant."""
        for exempt in self.EXEMPT_PATHS:
            if path.startswith(exempt):
                return True
        return False
    
    def _detect_tenant(self, request):
        """
        Detecta el tenant basado en la request.
        
        Orden de prioridad:
        1. Parámetro ?tenant=slug (solo DEBUG)
        2. Dominio en tabla Domain
        3. DEFAULT_TENANT_SLUG
        """
        from apps.tenants.models import Client, Domain
        
        # 1. Parámetro GET (solo en desarrollo)
        if settings.DEBUG:
            tenant_slug = request.GET.get('tenant')
            if tenant_slug:
                try:
                    client = Client.objects.get(slug=tenant_slug, is_active=True)
                    logger.debug(f"[Tenant] Detected via ?tenant={tenant_slug}")
                    return client
                except Client.DoesNotExist:
                    logger.warning(f"[Tenant] ?tenant={tenant_slug} not found")
        
        # 2. Buscar por dominio
        host = request.get_host().lower()
        # Remover puerto si existe
        if ':' in host:
            host = host.split(':')[0]
        
        try:
            domain = Domain.objects.select_related('client').get(
                domain=host,
                is_active=True,
                client__is_active=True
            )
            logger.debug(f"[Tenant] Detected via domain: {host}")
            return domain.client
        except Domain.DoesNotExist:
            logger.debug(f"[Tenant] Domain not found: {host}")
        except Domain.MultipleObjectsReturned:
            # Si hay múltiples, tomar el primero (no debería pasar)
            domain = Domain.objects.filter(domain=host, is_active=True).first()
            if domain:
                return domain.client
        
        # 3. DEFAULT_TENANT_SLUG
        default_slug = getattr(settings, 'DEFAULT_TENANT_SLUG', None)
        if default_slug:
            try:
                client = Client.objects.get(slug=default_slug, is_active=True)
                logger.debug(f"[Tenant] Using default: {default_slug}")
                return client
            except Client.DoesNotExist:
                logger.warning(f"[Tenant] Default tenant not found: {default_slug}")
        
        return None
    
    def _handle_no_tenant(self, request):
        """
        Maneja el caso cuando no se encuentra tenant.
        
        En lugar de error 500, muestra mensaje amigable.
        """
        host = request.get_host()
        
        logger.warning(f"[Tenant] No tenant for: {host}{request.path}")
        
        # Respuesta HTML simple (no usa templates para evitar errores)
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sitio no configurado</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
                    max-width: 500px;
                    text-align: center;
                }}
                h1 {{ color: #1f2937; margin-bottom: 16px; font-size: 24px; }}
                p {{ color: #6b7280; margin-bottom: 24px; line-height: 1.6; }}
                .domain {{ 
                    background: #f3f4f6; 
                    padding: 8px 16px; 
                    border-radius: 8px; 
                    font-family: monospace;
                    color: #374151;
                    display: inline-block;
                    margin: 8px 0;
                }}
                .help {{
                    font-size: 14px;
                    color: #9ca3af;
                    margin-top: 24px;
                    padding-top: 24px;
                    border-top: 1px solid #e5e7eb;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 Sitio no configurado</h1>
                <p>El dominio solicitado no está asociado a ningún sitio.</p>
                <div class="domain">{host}</div>
                <p class="help">
                    Si eres el administrador, verifica que el dominio esté 
                    registrado en la tabla <code>Domain</code> y vinculado 
                    a un <code>Client</code> activo.
                </p>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html, status=404, content_type='text/html')