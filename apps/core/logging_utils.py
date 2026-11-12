"""
Utilidades para loguear sin datos personales (SEC-07, Ley 21.719 art. 14 quinquies).

Los logs de Render se retienen y se pueden buscar. En vez del email, se
loguea una referencia opaca y estable: sirve para correlacionar eventos de
una misma persona sin exponer la dirección ni permitir enumerar cuentas.
"""
import hashlib
import hmac

from django.conf import settings


def email_ref(email) -> str:
    """
    Referencia no reversible de un email para logs: 'email:<12 hex>'.

    HMAC-SHA256 con una clave derivada de SECRET_KEY: sin la clave no se
    puede recalcular por diccionario. Normaliza mayúsculas y espacios para
    que la misma persona produzca siempre la misma referencia.
    """
    if not email:
        return 'email:-'
    key = hashlib.sha256(f'log-email-ref:{settings.SECRET_KEY}'.encode()).digest()
    normalized = str(email).strip().lower().encode()
    return 'email:' + hmac.new(key, normalized, hashlib.sha256).hexdigest()[:12]
