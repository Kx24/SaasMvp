# BOLT-41 — `SEC-18`: un solo `TenantAdminMixin`

## Contexto verificado (2026-11-15)

- `apps/accounts/mixins.py::TenantAdminMixin` es el mixin real: `get_queryset` por tenant,
  `get_list_filter` (oculta el filtro por cliente a staff no superuser, `BOLT-24`),
  `save_model`, `formfield_for_foreignkey` (desplegables FK limitados al tenant, `BOLT-32`) y
  permisos por objeto. Lo usan `orders/admin.py`, `tenants/admin.py` y `marketing/admin.py`.
- `apps/website/admin.py:12-15` hace `try: from apps.accounts.mixins import TenantAdminMixin` y,
  si falla, define **otro** `TenantAdminMixin` local (línea 15). `SectionAdmin`, `ServiceAdmin` y
  `ContactSubmissionAdmin` heredan del nombre resultante.
- `get_list_filter` y la regla de FK miran el campo `client` directo. Un modelo que llega al
  tenant por otro camino (por ejemplo `PaymentLog` → `order__client`) no queda cubierto por la
  misma regla.

## Qué hacer

1. Borra el mixin local y el `try/except` de `apps/website/admin.py`; importa siempre el de
   `apps/accounts/mixins.py`. Si el local tenía algún comportamiento que el real no tiene,
   llévalo al real con test.
2. Generaliza el camino al tenant: un atributo de clase (por ejemplo `tenant_lookup = 'client'`,
   sobreescribible a `'order__client'`) que usen `get_queryset`, `get_list_filter`,
   `formfield_for_foreignkey` y `_obj_tenant`. Aplica el valor correcto en cada admin cuyo modelo
   no tiene `client` directo.
3. Un staff de tenant no debe ver, filtrar ni elegir en un desplegable nada de otro tenant, en
   **ningún** admin registrado. Un staff sin tenant recibe `none()`.

## Tests

En `apps/accounts/tests_admin_scope.py` (amplía los existentes): para **cada** `ModelAdmin`
registrado que hereda del mixin, con un staff del tenant A: el `changelist` no lista objetos de
B, el `change` de un objeto de B responde 302/403/404, y los desplegables FK no ofrecen objetos
de B. El test recorre `admin.site._registry`, de modo que un admin nuevo sin cubrir falle. Un
test afirma que solo existe una clase `TenantAdminMixin` en el proyecto.

## Tests de rojo

`apps.accounts.tests_admin_scope`

## No tocar

`TenantAdminReadOnlyMixin` más allá de lo que herede. El admin de `Client` (solo superuser).
Modelos y migraciones.

## DoD

- [ ] Un solo `TenantAdminMixin`; `apps/website/admin.py` lo importa sin `try/except`.
- [ ] Todos los admins con tenant indirecto quedan acotados (test por registro).
- [ ] `tests_isolation` y suite completa verdes.
- [ ] Cierre documental (`SEC-18`) y una línea en `Documentacion/SEGURIDAD.md`.
