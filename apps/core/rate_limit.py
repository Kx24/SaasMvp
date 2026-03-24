# =============================================================================
# apps/core/rate_limit.py
# =============================================================================
# Helper de rate limiting usando el cache de Django.
# No requiere dependencias externas — usa django.core.cache.
#
# USO:
#   from apps.core.rate_limit import RateLimiter
#
#   limiter = RateLimiter(request, scope='contact', limit=3, period=600)
#   if limiter.is_exceeded():
#       return HttpResponse('Demasiados intentos', status=429)
#   limiter.increment()
#
# SCOPES sugeridos: 'contact', 'login', 'password_reset'
# =============================================================================

from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter por IP + tenant + scope usando Django cache.

    Args:
        request:    HttpRequest con request.client inyectado por TenantMiddleware
        scope:      Identificador del contexto (ej: 'contact', 'login')
        limit:      Número máximo de intentos permitidos en el período
        period:     Ventana de tiempo en segundos (default: 600 = 10 min)
    """

    def __init__(self, request, scope: str, limit: int = 3, period: int = 600):
        self.limit = limit
        self.period = period
        self.key = self._build_key(request, scope)

    def _build_key(self, request, scope: str) -> str:
        """
        Construye la cache key: rl:{scope}:{tenant_id}:{ip}

        Usa tenant_id para que el límite sea por tenant, no global.
        Si no hay cliente (misconfiguration), usa 'unknown'.
        """
        tenant_id = getattr(request.client, 'id', 'unknown') if hasattr(request, 'client') else 'unknown'
        ip = self._get_ip(request)
        return f"rl:{scope}:{tenant_id}:{ip}"

    def _get_ip(self, request) -> str:
        """Obtiene la IP real considerando proxies (Render usa X-Forwarded-For)."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip[:45]

    def current_count(self) -> int:
        """Retorna el número de intentos actuales en la ventana."""
        return cache.get(self.key, 0)

    def is_exceeded(self) -> bool:
        """Retorna True si el límite ya fue alcanzado."""
        return self.current_count() >= self.limit

    def increment(self):
        """
        Incrementa el contador.
        Si no existe la key, la crea con TTL = period.
        Si ya existe, solo incrementa (respeta el TTL original).
        """
        try:
            cache.add(self.key, 0, timeout=self.period)  # Crea si no existe
            cache.incr(self.key)
        except Exception as e:
            # En caso de fallo del cache, no bloquear al usuario — solo loggear
            logger.warning(f"[RateLimiter] Cache error on key {self.key}: {e}")

    def remaining(self) -> int:
        """Retorna intentos restantes en la ventana actual."""
        return max(0, self.limit - self.current_count())

    def reset(self):
        """Reinicia el contador (útil para tests)."""
        cache.delete(self.key)
