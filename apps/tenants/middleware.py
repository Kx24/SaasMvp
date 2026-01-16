"""
TenantMiddleware - Detección y Seguridad de Hosts (Nivel 1)
===========================================================
Actúa como reemplazo dinámico de ALLOWED_HOSTS.
1. Busca el dominio en la DB.
2. Si existe -> Carga el tenant.
3. Si no existe -> Verifica si es un dominio de sistema (localhost, render).
4. Si no es ninguno -> Bloquea la petición (404 Seguro).
"""

import logging
import threading
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

_thread_locals = threading.local()

def get_current_tenant():
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    _thread_locals.tenant = tenant

def clear_current_tenant():
    if hasattr(_thread_locals, 'tenant'):
        del _thread_locals.tenant

class TenantMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Dominios de sistema siempre permitidos (bypass de tenant)
        self.SYSTEM_DOMAINS = [
            'localhost', 
            '127.0.0.1',
            getattr(settings, 'BASE_DOMAIN', 'localhost'),
            getattr(settings, 'RENDER_EXTERNAL_HOSTNAME', None)
        ]

    def __call__(self, request):
        clear_current_tenant()
        
        # 1. Obtener Host limpio (sin puerto)
        host = request.get_host().split(':')[0].lower()
        
        # 2. Detectar Tenant en Base de Datos
        client = self._detect_tenant(request, host)
        
        # CASO A: Es un Tenant Válido
        if client:
            request.client = client
            set_current_tenant(client)
            logger.debug(f"[Tenant] Matched: {host} -> {client.slug}")
            response = self.get_response(request)
            clear_current_tenant()
            return response
            
        # CASO B: Es un Dominio de Sistema (Admin, Marketing, Infraestructura)
        # Permitimos pasar sin tenant (request.client = None)
        if self._is_system_domain(host):
            request.client = None
            logger.debug(f"[Tenant] System Domain Allowed: {host}")
            return self.get_response(request)

        # CASO C: Dominio Desconocido -> BLOQUEAR
        # Aquí reemplazamos la seguridad de ALLOWED_HOSTS=['*']
        logger.warning(f"[Tenant] Blocked Unknown Host: {host}")
        return self._handle_no_tenant(request, host)

    def _detect_tenant(self, request, host):
        """Busca el tenant en la BD."""
        from apps.tenants.models import Client, Domain
        
        # 1. Parámetro GET (Dev)
        if settings.DEBUG:
            tenant_slug = request.GET.get('tenant')
            if tenant_slug:
                return Client.objects.filter(slug=tenant_slug, is_active=True).first()

        # 2. Búsqueda por Dominio (Prod)
        try:
            domain_obj = Domain.objects.select_related('client').get(
                domain=host,
                is_active=True,
                client__is_active=True
            )
            return domain_obj.client
        except Domain.DoesNotExist:
            pass
            
        return None

    def _is_system_domain(self, host):
        """Verifica si es un dominio de infraestructura permitido."""
        if not host: 
            return False
            
        # 1. Coincidencia exacta con lista blanca
        if host in self.SYSTEM_DOMAINS:
            return True
            
        # 2. Subdominios de render (ej: mi-app.onrender.com)
        if '.onrender.com' in host:
            return True
            
        return False

    def _handle_no_tenant(self, request, host):
        """Muestra página de error 404 amigable."""
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Sitio no encontrado</title>
            <style>
                body {{ font-family: sans-serif; background: #f3f4f6; display: flex; height: 100vh; justify-content: center; align-items: center; margin: 0; }}
                .card {{ background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); max-width: 400px; text-align: center; }}
                h1 {{ color: #1f2937; font-size: 1.5rem; margin-bottom: 1rem; }}
                p {{ color: #4b5563; margin-bottom: 1.5rem; line-height: 1.5; }}
                .domain {{ background: #e5e7eb; padding: 0.5rem; border-radius: 0.5rem; font-family: monospace; font-size: 0.9rem; color: #374151; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>🔌 Dominio no conectado</h1>
                <p>El dominio que intentas visitar no está configurado en nuestra plataforma.</p>
                <div class="domain">{host}</div>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html, status=404)