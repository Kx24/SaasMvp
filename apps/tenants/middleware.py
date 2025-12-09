from django.shortcuts import render
from .models import Client

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obtener host y extraer solo el dominio (sin puerto)
        host = request.get_host()
        domain = host.split(':')[0]
        
        try:
            request.client = Client.objects.get(domain=domain, is_active=True)
        except Client.DoesNotExist:
            return render(request, 'errors/tenant_not_found.html', {
                'domain': domain,
                'host': host,
            }, status=404)
        
        response = self.get_response(request)
        return response