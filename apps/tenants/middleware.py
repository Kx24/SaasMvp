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
from django.shortcuts import render
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

        # Rutas que deben seguir funcionando aunque el tenant esté
        # en modo construcción: para que el cliente pueda loguearse y
        # administrar su sitio, y para que el propio formulario de leads
        # de la página "en construcción" (POST a /contact/submit/) responda.
        self.CONSTRUCTION_BYPASS_PREFIXES = ('/dashboard', '/auth', '/superadmin', '/contact')

    def __call__(self, request):
        clear_current_tenant()
        
        # 1. Obtener Host limpio (sin puerto)
        host = request.get_host().split(':')[0].lower()
        
        # 2. Detectar Tenant en Base de Datos
        client, domain_obj = self._detect_tenant(request, host)

        # CASO A: Es un Tenant Válido
        if client:
            request.client = client
            request.tenant_domain = domain_obj
            set_current_tenant(client)
            logger.debug(f"[Tenant] Matched: {host} -> {client.slug}")

            # #PREV-03: un dominio marcado is_preview se salta el modo
            # construcción -- el cliente revisa el sitio real ahí aunque el
            # dominio público siga mostrando "en construcción".
            is_preview_bypass = bool(domain_obj and domain_obj.is_preview)
            if (
                client.mode_under_construction
                and not request.path.startswith(self.CONSTRUCTION_BYPASS_PREFIXES)
                and not is_preview_bypass
            ):
                response = render(request, 'errors/under_construction.html', {'client': client})
                clear_current_tenant()
                return self._apply_preview_seo_headers(request, response, client, domain_obj)

            response = self.get_response(request)
            clear_current_tenant()
            return self._apply_preview_seo_headers(request, response, client, domain_obj)

        # CASO B: Es un Dominio de Sistema (Admin, Marketing, Infraestructura)
        # Permitimos pasar sin tenant (request.client = None)
        if self._is_system_domain(host):
            request.client = None
            request.tenant_domain = None
            logger.debug(f"[Tenant] System Domain Allowed: {host}")
            return self.get_response(request)

        # CASO C: Dominio Desconocido -> BLOQUEAR
        # Aquí reemplazamos la seguridad de ALLOWED_HOSTS=['*']
        logger.warning(f"[Tenant] Blocked Unknown Host: {host}")
        return self._handle_no_tenant(request, host)

    def _detect_tenant(self, request, host):
        """Busca el tenant en la BD. Retorna (client, domain_obj)."""
        from apps.tenants.models import Client, Domain

        # 1. Parámetro GET (Dev) -- atajo sin Domain real detrás, así que
        # domain_obj siempre es None (sin noindex ni bypass de construcción).
        if settings.DEBUG:
            tenant_slug = request.GET.get('tenant')
            if tenant_slug:
                client = Client.objects.filter(slug=tenant_slug, is_active=True).first()
                return client, None

        # 2. Búsqueda por Dominio (Prod)
        try:
            domain_obj = Domain.objects.select_related('client').get(
                domain=host,
                is_active=True,
                client__is_active=True
            )
            return domain_obj.client, domain_obj
        except Domain.DoesNotExist:
            pass

        return None, None

    def _apply_preview_seo_headers(self, request, response, client, domain_obj):
        """#PREV-02: un dominio no-primario con un primario distinto activo
        no debe competir en SEO con el dominio real del cliente."""
        if response is None or not domain_obj or domain_obj.is_primary:
            return response

        primary = client.primary_domain
        if not primary or primary.domain == domain_obj.domain:
            return response

        response['X-Robots-Tag'] = 'noindex, nofollow'
        canonical_url = f"https://{primary.domain}{request.path}"
        response['Link'] = f'<{canonical_url}>; rel="canonical"'
        return response

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