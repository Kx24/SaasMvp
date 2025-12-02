"""
Middleware Multi-Tenant - Corazón del sistema.

Este middleware se ejecuta en CADA request HTTP y detecta automáticamente
a qué cliente pertenece basándose en el dominio de la URL.

Flujo:
1. Usuario visita: https://servelec-ingenieria.cl/
2. Middleware lee el dominio: "servelec-ingenieria.cl"
3. Busca Client con ese dominio en la base de datos
4. Inyecta request.client en el request
5. Todas las vistas pueden usar request.client

Casos especiales:
- localhost / 127.0.0.1 → usa el primer cliente activo
- Dominio no encontrado → muestra error 404 personalizado
- Cliente inactivo → muestra página de mantenimiento
"""
from django.shortcuts import render
from django.http import Http404
from django.core.cache import cache
from .models import Client


class TenantMiddleware:
    """
    Middleware que detecta el tenant/cliente por dominio.
    
    Se ejecuta ANTES de las vistas, inyectando request.client
    para que todas las vistas tengan acceso al cliente actual.
    
    Architecture:
        Request → TenantMiddleware → View → Response
                       ↓
                  request.client
    """
    
    def __init__(self, get_response):
        """
        Inicialización del middleware (se ejecuta una sola vez al arrancar Django).
        
        Args:
            get_response: Callable que procesa el request y retorna response
        """
        self.get_response = get_response
        
        # Cache para evitar consultas repetidas a la DB
        # En producción esto mejora significativamente el performance
        self.cache_timeout = 300  # 5 minutos
    
    def __call__(self, request):
        """
        Método principal que se ejecuta en CADA request.
        
        Args:
            request: HttpRequest object
            
        Returns:
            HttpResponse object
            
        Flow:
            1. Extraer dominio del request
            2. Buscar cliente en caché o DB
            3. Inyectar request.client
            4. Continuar con el request normal
        """
        # ==================== EXTRAER DOMINIO ====================
        # request.get_host() retorna: "servelec-ingenieria.cl:8000"
        # Necesitamos solo: "servelec-ingenieria.cl"
        hostname = request.get_host().split(':')[0]  # Remover puerto
        
        # ==================== CASOS ESPECIALES: DESARROLLO ====================
        if hostname in ['localhost', '127.0.0.1', 'testserver']:
            # En desarrollo local, usar el primer cliente activo
            # Esto permite desarrollar sin configurar dominios
            request.client = self._get_default_client()
            
            if request.client is None:
                # No hay ningún cliente en la DB
                return self._render_no_clients_error(request)
            
            # Continuar con el request normal
            response = self.get_response(request)
            return response
        
        # ==================== PRODUCCIÓN: BUSCAR POR DOMINIO ====================
        try:
            # Intentar obtener cliente desde caché primero
            # Esto evita golpear la DB en cada request
            cache_key = f'tenant_client_{hostname}'
            client = cache.get(cache_key)
            
            if client is None:
                # No está en caché, buscar en DB
                client = Client.objects.select_related('settings').get(
                    domain=hostname,
                    is_active=True
                )
                
                # Guardar en caché para próximos requests
                cache.set(cache_key, client, self.cache_timeout)
            
            # ==================== VERIFICAR PAGO ====================
            # Si el cliente no está al día con pagos, mostrar mensaje
            if not client.is_payment_current:
                return self._render_payment_required(request, client)
            
            # ==================== INYECTAR CLIENTE ====================
            # Este es el paso MÁS IMPORTANTE
            # Todas las vistas tendrán acceso a request.client
            request.client = client
            
        except Client.DoesNotExist:
            # ==================== DOMINIO NO ENCONTRADO ====================
            # El dominio no existe en nuestra base de datos
            return self._render_tenant_not_found(request, hostname)
        
        except Client.MultipleObjectsReturned:
            # ==================== ERROR DE DATOS ====================
            # Hay múltiples clientes con el mismo dominio (NO debería pasar)
            # Esto indica un problema en la base de datos
            return self._render_data_error(request, hostname)
        
        # ==================== CONTINUAR CON REQUEST NORMAL ====================
        # El middleware ha hecho su trabajo, pasar al siguiente middleware o vista
        response = self.get_response(request)
        
        return response
    
    # ==================== MÉTODOS AUXILIARES ====================
    
    def _get_default_client(self):
        """
        Obtiene el primer cliente activo para desarrollo local.
        
        Returns:
            Client: Primer cliente activo o None si no hay ninguno
        """
        try:
            # Buscar el primer cliente activo
            # En producción esto no se usa, solo en localhost
            return Client.objects.select_related('settings').filter(
                is_active=True
            ).first()
        except Exception:
            return None
    
    def _render_no_clients_error(self, request):
        """
        Página de error cuando no hay clientes en la base de datos.
        
        Esto solo debería pasar en desarrollo inicial.
        """
        context = {
            'error_title': 'No hay clientes configurados',
            'error_message': 'Debes crear al menos un cliente en Django Admin.',
            'action_url': '/admin/tenants/client/add/',
            'action_text': 'Crear Cliente',
        }
        return render(
            request,
            'errors/tenant_not_found.html',
            context,
            status=404
        )
    
    def _render_tenant_not_found(self, request, hostname):
        """
        Página de error 404 personalizada cuando el dominio no existe.
        
        Args:
            request: HttpRequest
            hostname: Dominio que no se encontró
            
        Returns:
            HttpResponse con status 404
        """
        context = {
            'error_title': 'Sitio no encontrado',
            'error_message': f'El dominio {hostname} no está configurado en nuestro sistema.',
            'domain': hostname,
            'support_email': 'soporte@tusaas.com',  # Cambiar por tu email
        }
        return render(
            request,
            'errors/tenant_not_found.html',
            context,
            status=404
        )
    
    def _render_payment_required(self, request, client):
        """
        Página cuando el cliente no ha pagado.
        
        Args:
            request: HttpRequest
            client: Cliente con pago vencido
            
        Returns:
            HttpResponse con status 402 (Payment Required)
        """
        context = {
            'client': client,
            'error_title': 'Pago Requerido',
            'error_message': 'El sitio está temporalmente suspendido por falta de pago.',
            'next_payment_due': client.next_payment_due,
            'contact_email': client.contact_email,
        }
        return render(
            request,
            'errors/payment_required.html',
            context,
            status=402  # HTTP 402: Payment Required
        )
    
    def _render_data_error(self, request, hostname):
        """
        Error cuando hay datos duplicados en la DB.
        
        Esto NO debería pasar nunca (domain es unique).
        Si pasa, indica un problema serio.
        """
        context = {
            'error_title': 'Error de Configuración',
            'error_message': 'Hay un problema con la configuración del sitio. Contacta al administrador.',
            'domain': hostname,
        }
        return render(
            request,
            'errors/500.html',
            context,
            status=500
        )


class TenantContextMiddleware:
    """
    Middleware opcional que inyecta el cliente en el contexto de TODOS los templates.
    
    Esto permite usar {{ client.name }} directamente en cualquier template
    sin tener que pasarlo explícitamente desde la vista.
    
    Usage en templates:
        <h1>{{ client.company_name }}</h1>
        <p>{{ client.settings.primary_color }}</p>
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """
        Inyecta el cliente en el contexto si existe.
        """
        response = self.get_response(request)
        
        # Si el response tiene context_data (TemplateResponse)
        # inyectar el cliente automáticamente
        if hasattr(response, 'context_data') and hasattr(request, 'client'):
            if response.context_data is not None:
                response.context_data['client'] = request.client
        
        return response