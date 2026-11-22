# BOLT-68 — `DASH-09`: fondo del ícono de mensajes sin token de marca

## Contexto verificado (2026-11-18)

- `templates/dashboard/index.html` línea 23: el ícono de la tarjeta "Contactos" usa
  `style="background: rgba(var(--primary-rgb, 59, 130, 246), 0.1);"`. `--primary-rgb` **no existe**
  en ningún template ni CSS (`grep -rn 'primary-rgb' templates static/css/input.css` solo da esta
  línea), así que el fondo siempre cae al azul por defecto y no toma la marca del tenant.
- El dashboard define `--color-primary` en `templates/dashboard/base.html` (~línea 20) y ya usa
  `color-mix(in srgb, var(--color-primary) 8%, transparent)` en su CSS (~línea 33).
- Hallado por `BOLT-64`.

## Qué hacer

1. Cambia ese fondo a `background: color-mix(in srgb, var(--color-primary) 10%, transparent);`
   (mismo patrón que el CSS de `base.html`). Un solo `style=""` existente: no migrarlo a Tailwind
   aquí.
2. Busca otros `var(--primary-rgb` en `templates/` (no debería haber más) y trátalos igual.

## Tests de rojo

`apps.website.tests.test_dashboard_icon_token` (archivo nuevo con ese nombre exacto; copia el
montaje de `apps/website/tests/test_dashboard_brand_token.py`). Casos: (a) ningún archivo bajo
`templates/` contiene `--primary-rgb`; (b) la home del dashboard de un tenant con
`primary_color='#0b5fa5'` contiene `color-mix(in srgb, var(--color-primary)` en la tarjeta de
contactos y no contiene `primary-rgb`.

## No tocar

El contraste de botones (`DASH-07`), el resto de los `style=""`, los demás temas.

## DoD

- [ ] El fondo del ícono sigue la marca del tenant.
- [ ] Cierre documental (`DASH-09`): borra la fila del kanban y agrega la línea al histórico.
