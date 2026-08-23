"""
CSP y Permissions-Policy (#SEC-02).

Módulo aparte -- no directo en production.py -- para poder testear el
diccionario real con un import normal. production.py exige SECRET_KEY/
EMAIL_HOST_USER/EMAIL_HOST_PASSWORD al importarse (fail-fast, ver
#AUD-07/#AUD-12); este módulo no depende de nada de eso, así que un test
puede importarlo directo sin pasar por subprocess.

Hosts externos reales auditados en el código (no una lista genérica):
Google Fonts (`docs/design-system.md`, #AUD-11), Alpine.js (jsdelivr),
htmx (unpkg), Google Analytics (opcional, `client.settings.google_analytics_id`),
imágenes de Cloudinary (`apps/core/cloudinary_utils.py`).

`style-src`/`script-src` necesitan 'unsafe-inline': los temas usan
bloques `<style>` inline con variables CSS templadas por tenant (`#AUD-11`,
por diseño, no es deuda a limpiar) y hay atributos `onclick=` en
dashboard/templates de tenant -- un nonce no cubre atributos de evento
inline, así que "unsafe-inline" es inevitable sin una reescritura grande
de esos 11 archivos. No es la política más estricta posible; es la que
no rompe nada real hoy.

`/checkout/` queda EXCLUIDO a propósito: el SDK de MercadoPago (Checkout
Bricks, ver apps/orders/templates/orders/checkout.html) crea iframes de
Secure Fields cuyo dominio exacto no está documentado públicamente por
MercadoPago de forma confiable -- una CSP mal calibrada ahí puede romper
el cobro en silencio, el mismo tipo de riesgo que ya mordió una vez en
`#AUD-01`. Habilitar CSP en checkout requiere una pasada manual contra
el sandbox real de MP (mismo cabo suelto pendiente que #AUD-07/#PAY-03,
requiere credenciales de test) -- no se hace a ciegas.
"""
from csp.constants import NONE, SELF, UNSAFE_INLINE

CONTENT_SECURITY_POLICY = {
    "EXCLUDE_URL_PREFIXES": ["/checkout/"],
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [
            SELF, UNSAFE_INLINE,
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://www.googletagmanager.com",
        ],
        "style-src": [SELF, UNSAFE_INLINE, "https://fonts.googleapis.com"],
        "font-src": [SELF, "https://fonts.gstatic.com"],
        "img-src": [SELF, "data:", "https://res.cloudinary.com", "https://www.googletagmanager.com"],
        "connect-src": [SELF, "https://www.google-analytics.com", "https://analytics.google.com"],
        "frame-ancestors": [NONE],
        "base-uri": [SELF],
        "form-action": [SELF],
        "object-src": [NONE],
    },
}

# Features que esta app no usa en ningún lado -- deshabilitadas para
# cualquier origen. `payment`/`autoplay`/`fullscreen` quedan sin listar
# a propósito (sin restricción): Checkout Bricks y el video de fondo de
# Rancho Cachimba son los únicos usos reales y restringirlos a ciegas
# corre el mismo riesgo que la CSP de checkout de arriba.
PERMISSIONS_POLICY = {
    "accelerometer": [],
    "ambient-light-sensor": [],
    "camera": [],
    "display-capture": [],
    "encrypted-media": [],
    "geolocation": [],
    "gyroscope": [],
    "magnetometer": [],
    "microphone": [],
    "usb": [],
}
