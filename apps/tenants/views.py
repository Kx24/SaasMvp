"""
Vistas de la app Tenants (solo para testing y debug).
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


def tenant_debug(request):
    """
    Vista de debug que muestra información del tenant detectado.
    
    Útil para verificar que TenantMiddleware está funcionando correctamente.
    
    URL: /tenant-debug/
    
    Muestra:
        - Cliente detectado
        - Dominio usado
        - Configuración del cliente
    """
    context = {
        'client': getattr(request, 'client', None),
        'hostname': request.get_host(),
        'path': request.path,
        'method': request.method,
    }
    return render(request, 'tenants/debug.html', context)


@staff_member_required
def tenant_list(request):
    """
    Lista todos los clientes (solo para staff).
    
    URL: /tenants/
    """
    from .models import Client
    
    clients = Client.objects.select_related('settings').all()
    
    context = {
        'clients': clients,
    }
    return render(request, 'tenants/list.html', context)