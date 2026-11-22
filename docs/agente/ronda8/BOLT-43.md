# BOLT-43 — `DEUDA-09`: borrar la vista `dashboard_services` y lo que quedó sin uso

## Contexto verificado (2026-11-15)

- `apps/website/views/services.py:23` define `dashboard_services`; `apps/website/views/__init__.py`
  la re-exporta (líneas 22 y 35). **Ninguna ruta** de `apps/website/urls.py` la usa.
- `templates/dashboard/services.html` existe y parece ser solo de esa vista.
- `BOLT-35` reportó además: en `templates/dashboard/gallery.html` un
  `{% include ... with ... %}` partido en varias líneas (estado vacío) no se renderiza y muestra
  la etiqueta cruda.

## Qué hacer

1. Confirma con `git grep` que `dashboard_services` y `dashboard/services.html` no se referencian
   desde ninguna URL, vista, plantilla ni test. Si algo los usa, **no borres** y repórtalo.
2. Borra la vista, su re-exportación y la plantilla (y los parciales que solo usara ella).
3. Corrige el `{% include %}` multilínea de `templates/dashboard/gallery.html` (una sola línea, o
   `{% with %}` + include) para que el estado vacío se renderice.
4. Si el test de matriz de roles (`apps/accounts/tests_dashboard_roles.py`) lista
   `dashboard_services` como excepción, quítala de la lista.

## Tests

- Render de `dashboard_gallery` con la galería vacía: el HTML no contiene `{%` ni `%}` y muestra
  el estado vacío.
- Un test afirma que toda función exportada en `apps/website/views/__init__.py::__all__` que
  empieza por `dashboard_` tiene una ruta en `apps/website/urls.py` (evita que vuelva a quedar
  una vista huérfana).

## Tests de rojo

`apps.website.tests.test_dashboard_orphans` (archivo nuevo con ese nombre exacto: el orquestador confirma el rojo con esa etiqueta).

## No tocar

Las vistas de servicios que sí tienen ruta (`create_service`, `edit_service_dashboard`, etc.).

## DoD

- [ ] Sin vista ni plantilla huérfanas; la galería vacía se ve bien.
- [ ] Playwright verde (la card toca `templates/`).
- [ ] Cierre documental (`DEUDA-09`).
