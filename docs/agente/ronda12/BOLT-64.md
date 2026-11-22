# BOLT-64 — `DASH-06`: token `--primary` inexistente en el dashboard

## Contexto verificado (2026-11-18)

- El dashboard define el color de marca como `--color-primary` (`templates/dashboard/base.html`
  línea ~20, desde `client.settings.primary_color`). **No existe `--primary`.**
- Cuatro usos rotos de `var(--primary)`: `templates/dashboard/base.html` líneas 114 y 147 (fondo del
  avatar, dos veces) y `templates/dashboard/index.html` líneas 24 (ícono) y 149 (enlace "ver
  mensajes"). Sin definición, el navegador ignora la declaración y el elemento queda sin color de
  marca.
- `DASH-08` del kanban está obsoleta: `unread_contacts` ya lo define
  `apps/accounts/context_processors.py` desde `BOLT-55` (no se toca aquí; se cierra en el kanban
  por documentación).

## Qué hacer

1. Cambia `var(--primary)` por `var(--color-primary)` en esos cuatro lugares. Es un cambio de
   token, no de diseño: nada de reescribir los `style=""` a Tailwind en esta card.
2. `grep -rn 'var(--primary)' templates/dashboard` debe quedar vacío.

## Tests de rojo

`apps.website.tests.test_dashboard_brand_token` (archivo nuevo con ese nombre exacto). Casos:
(a) ningún archivo bajo `templates/dashboard/` contiene `var(--primary)` (recorre el árbol);
(b) la home del dashboard de un tenant con `primary_color='#0b5fa5'` (login del dueño, `HTTP_HOST`
del tenant; copia el montaje de `apps/tenants/tests_module_access.py::ModuleAccessBase`) renderiza
`var(--color-primary)` en el avatar y no contiene `var(--primary)`.

## No tocar

`.btn-primary`, el contraste de los botones (es `DASH-07`), el resto de los `style=""`.

## DoD

- [ ] Avatar e ícono del dashboard toman el color de marca del tenant.
- [ ] Cierre documental (`DASH-06` y `DASH-08`): borra las dos filas del kanban maestro y agrega
      una línea para cada una en el histórico (`DASH-08`: "ya cubierta por `BOLT-55`, el context
      processor define `unread_contacts`; la fila quedó obsoleta").
