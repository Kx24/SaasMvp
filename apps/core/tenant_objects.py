"""Camino único para obtener objetos del tenant en las vistas (CONS-06)."""
from django.http import Http404
from django.shortcuts import get_object_or_404


def tenant_object_or_404(request, model, client_field='client', **lookup):
    """get_object_or_404 que SIEMPRE filtra por request.client.

    Si ``request.client`` es None lanza Http404: nunca devuelve objetos sin tenant.
    ``client_field`` permite modelos sin FK directa (p. ej. ``section__client``).
    """
    client = getattr(request, 'client', None)
    if client is None:
        raise Http404('Tenant no resuelto')
    queryset = model.objects.filter(**{client_field: client})
    return get_object_or_404(queryset, **lookup)
