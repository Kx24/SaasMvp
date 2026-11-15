# BOLT-24 — `SEC-05b`: restos de alcance por tenant en el Django Admin

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

## Qué hacer

1. Tests en `apps/accounts/tests_admin_scope.py` (ya existe, sigue su estilo): con un `staff` del
   tenant A y datos de A y B,
   - el changelist de `UserProfile` y el de `SEOConfig` no contienen el nombre del cliente B;
   - el formulario de alta/cambio de `PaymentLog` no ofrece órdenes de B;
   - un superuser sigue viendo todo (filtros y desplegables completos).
2. Solución general en `TenantAdminMixin`, no parche por admin:
   - `formfield_for_foreignkey`: para un no-superuser, todo FK cuyo modelo relacionado tenga campo
     `client` se restringe a `client=<tenant del usuario>`; el FK `client` mismo se restringe al
     propio tenant.
   - `get_list_filter`: para un no-superuser, quitar `'client'` de los filtros (su queryset ya
     está limitado a un tenant, el filtro no aporta).
3. Verifica con los tests existentes que nada de `BOLT-15` retrocede.

## No tocar

`ClientAdmin` (solo superuser por `BOLT-15`), `PlanAdmin`, el mixin local de `apps/website/admin.py`.

## Tests de rojo

`apps.accounts.tests_admin_scope`

## DoD

- [ ] Los tres casos de fuga cubiertos por test y corregidos en el mixin.
- [ ] Superuser sin cambios de comportamiento.
- [ ] Cierre documental (`SEC-05b`).
