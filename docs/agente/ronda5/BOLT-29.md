# BOLT-29 — `CONS-07`: separar `apps/website/views.py` por área

## Contexto verificado (2026-11-14)

`apps/website/views.py` tiene cerca de 1.100 líneas con todo mezclado. Lo importan:
`apps/website/urls.py` (`from . import views` y `from apps.website.views import dashboard_branding`),
`apps/core/tests/test_client_ip.py:65` (`from apps.website import views as website_views`) y
`apps/website/tests/test_home_render.py:153` (`from apps.website.views import dashboard_portada`).
Puede haber `mock.patch('apps.website.views.<algo>')` en tests: búscalos antes de mover nada
(`git grep -n "apps.website.views" -- "*.py"`).

## Qué hacer

Refactor puro, **sin cambio de comportamiento**:

1. Convierte `views.py` en el paquete `apps/website/views/` con un módulo por área:
   `public.py` (home, contacto y demás vistas públicas), `sections.py`, `services.py`,
   `gallery.py`, `contacts.py`, `branding.py` (portada, branding y ajustes del dashboard) y, si
   hace falta, `_shared.py` para helpers comunes. Ajusta los nombres si el contenido real pide
   otra división, pero ningún módulo supera 400 líneas.
2. `apps/website/views/__init__.py` re-exporta **todos** los nombres públicos que hoy expone
   `views.py` (con `__all__`), para que `urls.py` y los imports de tests sigan funcionando sin
   editarlos. Excepción: si un `mock.patch('apps.website.views.X')` parchea un nombre que la
   vista usa internamente, el parche dejará de surtir efecto al mover la vista; en ese caso
   actualiza el target del parche al módulo nuevo y decláralo en el informe.
3. Usa `git mv` para el archivo principal donde ayude a conservar historial.
4. Test nuevo `apps/website/tests/test_views_package.py`:
   - `apps.website.views` es un paquete (`__path__` existe) y contiene los módulos de área.
   - Ningún módulo del paquete supera 400 líneas.
   - El conjunto de nombres de URL (`name=`) de `apps/website/urls.py` y
     `apps/website/auth_urls.py` es **idéntico** a una lista congelada: genera la lista desde el
     código actual antes de mover nada y pégala en el test; cada patrón resuelve a un callable.

## No tocar

Lógica de las vistas, decoradores, URLs, templates. Nada de "ya que estoy" (renombrar, tipar,
simplificar): si ves algo, repórtalo.

## Tests de rojo

`apps.website.tests.test_views_package`

## DoD

- [ ] Paquete con módulos de 400 líneas o menos; `urls.py` sin cambios funcionales.
- [ ] Conjunto de nombres de URL idéntico al de antes.
- [ ] Suite completa, aislamiento y Playwright verdes; cobertura no baja.
- [ ] Cierre documental (`CONS-07`).
