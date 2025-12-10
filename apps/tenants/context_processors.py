from datetime import datetime

def client_context(request):
    """Inyecta el cliente en todos los templates"""
    context = {'current_year': datetime.now().year}
    
    if hasattr(request, 'client'):
        context['client'] = request.client
    
    return context