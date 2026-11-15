# BOLT-24 — `SEC-05b` (1 de 2): filtros por cliente en el admin

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

## Alcance de esta card (mitad 1 de 2)

Solo los **filtros laterales** `client` de `UserProfileAdmin` y `SEOConfigAdmin`. El desplegable de
`PaymentLog.order` es la card `BOLT-32`; no lo toques acá.

> La ronda anterior agotó el tiempo de la sesión (1 h) con las dos mitades juntas. Mantente en
> esta: si en 25 minutos no hay un test rojo escrito y confirmado, escribe
> `RESULTADO: BLOQUEADA — <qué te frena>`.

## Qué hacer

1. Tests en `apps/accounts/tests_admin_scope.py` (ya existe; sigue su estilo): con un `staff` del
   tenant A y datos de A y B:
   - el changelist de `UserProfile` y el de `SEOConfig` no contienen el nombre del cliente B;
   - un superuser sigue viendo los filtros completos.
2. En `apps/accounts/mixins.py::TenantAdminMixin` agrega `get_list_filter`: para un no-superuser
   quita `'client'` de los filtros (su queryset ya está limitado a un tenant). No toques
   `formfield_for_foreignkey` ni los demás métodos.
3. Los tests existentes de `BOLT-15` siguen verdes sin editarlos.

## No tocar

`ClientAdmin`, `PlanAdmin`, el mixin local de `apps/website/admin.py`, `apps/orders/admin.py`.

## Tests de rojo

`apps.accounts.tests_admin_scope`

## DoD

- [ ] Ni `UserProfile` ni `SEOConfig` listan el nombre de otro cliente a un `staff`.
- [ ] Superuser sin cambios.
- [ ] Cierre documental: **acota** la fila `SEC-05b` del kanban a "desplegable de
      `PaymentLog.order` (`BOLT-32`)"; no la borres. Una línea en el histórico.
