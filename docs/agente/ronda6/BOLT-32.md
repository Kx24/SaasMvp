# BOLT-32 — `SEC-05b` (2 de 2): desplegable de `PaymentLog.order` por tenant

## Contexto verificado (2026-11-14)

`BOLT-15` limitó el admin por tenant con `apps/accounts/mixins.py::TenantAdminMixin`
(`get_queryset` + permisos por objeto). Quedaron tres fugas menores para un usuario `staff` no
superuser que pertenece a un tenant:

- `apps/accounts/admin.py:155` — `UserProfileAdmin.list_filter = ['client', 'role']`: el filtro
  lateral lista los nombres de **todos** los clientes.
- `SEOConfigAdmin` (`apps/marketing/admin.py`): mismo problema con su filtro por `client`.
- `apps/orders/admin.py:351` — `PaymentLogAdmin`: el desplegable del campo `order` muestra
  órdenes de todos los tenants.

Ojo: `apps/website/admin.py:15` define un `TenantAdminMixin` local distinto (con
`formfield_for_foreignkey`). No lo unifiques en esta card; repórtalo si ves diferencias de
comportamiento.

## Alcance de esta card (mitad 2 de 2)

Solo el **desplegable de `PaymentLog.order`** en `apps/orders/admin.py` (`PaymentLogAdmin`, línea
~351) y la regla general de FK en el mixin. La mitad 1 (`BOLT-24`) ya quitó los filtros `client`;
no los toques.

> Mantente en esta: si en 25 minutos no hay un test rojo escrito y confirmado, escribe
> `RESULTADO: BLOQUEADA — <qué te frena>`.

## Qué hacer

1. Tests en `apps/accounts/tests_admin_scope.py`: con un `staff` del tenant A, el formulario de
   cambio de un `PaymentLog` de A **no ofrece** órdenes de B en el desplegable `order`; un
   superuser las ve todas.
2. En `TenantAdminMixin.formfield_for_foreignkey`: para un no-superuser, todo FK cuyo modelo
   relacionado tenga campo `client` se restringe a `client=<tenant del usuario>`. Si el modelo
   relacionado no tiene `client` directo, averigua el camino real mirando
   `apps/orders/models.py` y restringe por él.
3. Los tests existentes de `BOLT-15` y de `BOLT-24` siguen verdes sin editarlos.

## No tocar

`ClientAdmin`, `PlanAdmin`, el mixin local de `apps/website/admin.py`, `get_list_filter`.

## Tests de rojo

`apps.accounts.tests_admin_scope`

## DoD

- [ ] Un `staff` no ve órdenes de otro tenant en `PaymentLog`.
- [ ] Superuser sin cambios.
- [ ] Cierre documental: borra la fila `SEC-05b` del kanban (queda cerrada del todo). Una línea en
      el histórico.
