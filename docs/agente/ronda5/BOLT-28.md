# BOLT-28 — `CONS-06`: un único camino para obtener objetos del tenant en el dashboard

## Contexto verificado (2026-11-14)

`apps/website/views.py` tiene unas 18 llamadas a `get_object_or_404(...)` / `.objects.get(...)`.
El aislamiento depende de que cada una recuerde pasar `client=request.client` (no hay
auto-filtro, `#MED-02`). Las vistas son funciones, no clases.

## Decisión de diseño

La card se llama "`TenantOwnedMixin`", pero como las vistas son funciones el camino único es un
**helper**, no un mixin:

```python
# apps/core/tenant_objects.py
def tenant_object_or_404(request, model, client_field='client', **lookup):
    """get_object_or_404 que SIEMPRE filtra por request.client."""
```

- Si `request.client` es `None` → `Http404` (nunca devuelve objetos sin tenant).
- Filtra con `model.objects.filter(**{client_field: request.client})`; para modelos sin campo
  `client` directo (por ejemplo `GalleryItem` vía `section__client`) se pasa `client_field`.
- No convierte las vistas a clases.

## Qué hacer

1. Tests en `apps/core/tests/test_tenant_objects.py`:
   - Devuelve el objeto del tenant del request; 404 para un objeto de otro tenant con el mismo
     `pk`; 404 si `request.client` es `None`; `client_field` funciona para un modelo indirecto.
   - **Guardia estática:** el código de las vistas de `apps/website` (el archivo `views.py` o, si
     ya es un paquete, todos sus módulos) no contiene `get_object_or_404(` ni `.objects.get(`
     fuera del helper. Si alguna llamada debe quedar (una búsqueda que no es de un objeto de
     tenant), márcala con `# tenant-ok: <razón>` en la misma línea; la guardia acepta solo las
     líneas marcadas.
2. Reemplaza las llamadas por el helper, una por una, sin cambiar el comportamiento de ninguna
   vista.
3. `python manage.py test apps.tenants.tests_isolation apps.website` sigue verde sin editar esos
   tests.

## No tocar

No separes `views.py` en archivos (es `BOLT-29`). No cambies URLs, templates ni decoradores.
Otras apps (`orders`, `accounts`) quedan fuera: si ves el mismo patrón, repórtalo.

## Tests de rojo

`apps.core.tests.test_tenant_objects`

## DoD

- [ ] Helper con tests; guardia estática verde; cada excepción `# tenant-ok` listada en el informe.
- [ ] Suite de aislamiento verde sin modificar.
- [ ] Cierre documental (`CONS-06`).
