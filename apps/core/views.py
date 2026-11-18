"""Vistas de infraestructura (sin tenant, sin autenticación)."""
import logging

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@never_cache
@require_http_methods(['GET', 'HEAD'])
def health(request):
    """#OPS-05: 200 si la base responde `SELECT 1`, 503 si no.

    No expone detalles: el error real va al log, no a la respuesta.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        logger.exception('[health] La base de datos no responde')
        return JsonResponse({'status': 'error', 'database': 'error'}, status=503)
    return JsonResponse({'status': 'ok', 'database': 'ok'})
