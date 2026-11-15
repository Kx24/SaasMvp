# BOLT-35 — `DASH-04`: roles con efecto en el dashboard

> **Matriz confirmada por el dueño el 2026-11-15**, sin cambios. `editor` sigue siendo el rol por
> defecto (no hay migración).

## Contexto verificado (2026-11-15)

- `UserProfile.role` (`apps/accounts/models.py:28`) tiene **cuatro** valores: `owner`, `admin`,
  `editor` (default) y `viewer`. Las propiedades `is_owner`, `is_admin` (owner o admin) y
  `can_edit` (owner, admin o editor) existen, pero **ninguna vista del dashboard las consulta**:
  las 21 vistas de `apps/website/views/` usan solo `@tenant_member_required`
  (`apps/accounts/decorators.py`), que comprueba el tenant y nada más. Un `viewer` puede hoy
  editar, borrar y cambiar la marca.
- Solo el admin de Django usa los roles (`TenantAdminReadOnlyMixin` en `apps/accounts/mixins.py`:
  borrar y crear exigen `is_admin`).
- Quien se registra por onboarding queda `owner` (`process_onboarding`); un usuario creado sin
  rol explícito queda `editor`.

## Matriz (confirmada)

Acciones agrupadas por el efecto, no por pantalla. ✔ permitido · ✘ 403.

| Acción | Vistas | owner | admin | editor | viewer |
|---|---|---|---|---|---|
| `view_dashboard`: ver inicio, secciones, servicios, galería | `dashboard`, `dashboard_sections`, `dashboard_gallery` | ✔ | ✔ | ✔ | ✔ |
| `view_contacts`: ver los mensajes recibidos (datos personales de terceros) | `dashboard_contacts` | ✔ | ✔ | ✔ | ✘ |
| `edit_content`: crear y editar secciones, servicios, galería y portada; ocultar/destacar/reordenar | `edit_section_dashboard`, `create_service`, `edit_service_dashboard`, `toggle_service_active`, `toggle_service_featured`, `reorder_services`, `gallery_item_add`, `gallery_item_edit`, `gallery_item_toggle`, `dashboard_portada` | ✔ | ✔ | ✔ | ✘ |
| `manage_contacts`: marcar mensajes leídos/respondidos | `mark_contact_read`, `mark_contact_replied` | ✔ | ✔ | ✔ | ✘ |
| `delete_content`: borrar servicios e imágenes | `delete_service_dashboard`, `gallery_item_delete` | ✔ | ✔ | ✘ | ✘ |
| `manage_branding`: cambiar colores, fuentes y logo | `dashboard_branding` | ✔ | ✔ | ✘ | ✘ |

Razones: el `viewer` es de solo lectura y no ve mensajes (minimización de datos, Ley 21.719 art.
14 quáter); el `editor` crea y edita pero no borra (irreversible) ni cambia la marca; borrar y la
marca los comparte `admin` con `owner`. La gestión de usuarios (invitar, cambiar roles) **no
existe aún en el dashboard**: queda reservada a `owner` cuando se construya y no es parte de esta
card.

## Qué hacer

1. **Una sola fuente de verdad:** `apps/accounts/permissions.py` con
   `DASHBOARD_PERMISSIONS = {'view_dashboard': {...roles}, ...}` exactamente como la tabla, y
   `has_dashboard_permission(user, client, action) -> bool` (superuser siempre sí; sin perfil, de
   otro tenant o sin tenant: no).
2. **Decorador:** `tenant_permission_required(action)` en `apps/accounts/decorators.py`, que
   envuelve a `tenant_member_required` (conserva su comportamiento: login, tenant, 403) y además
   responde `HttpResponseForbidden('No tienes permiso para esta acción.')` cuando el rol no
   alcanza. Reemplaza en cada vista del dashboard el `@tenant_member_required` por el decorador
   con la acción que indica la matriz. Una vista no listada en la matriz: no la toques y
   repórtala.
3. **Interfaz:** un context processor (o el mecanismo que ya use el dashboard para su contexto)
   expone `dash_perms` (dict acción → bool) y las plantillas de `templates/dashboard/` ocultan los
   botones de editar, borrar, marca y los enlaces a mensajes que el rol no permite. El 403 es la
   defensa; ocultar el botón es solo comodidad.
4. **Tests existentes:** los que ejecutan acciones con un usuario de rol `editor` (el default) y
   ahora reciben 403 se corrigen **cambiando el rol del usuario de prueba**, nunca la matriz ni
   las aserciones.
5. Documentación: matriz en `Documentacion/ARQUITECTURA.md` (sección de autorización) y una línea
   en `Documentacion/SEGURIDAD.md`; kanban: `DASH-04` borrada, una línea en el histórico.

## Tests (nuevo `apps/accounts/tests_dashboard_roles.py`)

- **Matriz completa:** para cada acción de la tabla y cada rol, una petición a **cada vista** de
  esa acción con un usuario del tenant: permitido → 200/302, no permitido → 403. Se arma
  recorriendo `DASHBOARD_PERMISSIONS` y una tabla acción → vistas dentro del test, de modo que
  agregar un rol o una vista sin cubrirla falle. Los POST de mutación (borrar, toggle, reorder)
  usan datos reales del tenant.
- **Cobertura de vistas:** un test recorre las URL del dashboard (`apps/website/urls.py` con prefijo
  `dashboard/` más `mark_contact_*`) y afirma que cada vista está decorada con
  `tenant_permission_required` o figura en una lista explícita de excepciones.
- **Cross-tenant:** un `owner` del tenant A recibe 403 en cualquier vista del tenant B, y un
  superuser pasa siempre (la suite de aislamiento existente sigue verde sin editarla).
- **Interfaz:** con un `viewer` el HTML del dashboard no contiene los enlaces de editar/borrar ni el
  de mensajes; con un `owner` sí.
- Un rol desconocido (`UserProfile.role='x'`) no obtiene ninguna acción.

## No tocar

`UserProfile.ROLE_CHOICES` (no agregues roles), el admin de Django (`mixins.py`), las vistas
públicas, los modelos y migraciones (esta card no cambia datos), Rancho Cachimba.

## Tests de rojo

`apps.accounts.tests_dashboard_roles`

## DoD

- [ ] La matriz vive en un solo lugar y las 21 vistas del dashboard la aplican.
- [ ] Un `viewer` no puede editar, borrar ni ver mensajes; un `editor` no puede borrar ni cambiar
      la marca (tests por rol y por vista).
- [ ] La interfaz oculta lo no permitido.
- [ ] Suite de aislamiento y suite completa verdes; cobertura de `apps/accounts` no baja.
- [ ] Cierre documental (`DASH-04`). En `revisar_humano`: la matriz tal como quedó, y qué tests
      existentes cambiaron de rol.
