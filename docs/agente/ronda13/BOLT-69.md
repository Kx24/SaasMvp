# BOLT-69 — `DEUDA-13`: `Plan.get_available_themes_list` devuelve un slug inválido

## Contexto verificado (2026-11-18)

- `apps/orders/models.py` ~línea 202: si `available_themes` no es una lista, devuelve
  `['default']`. Ese slug **no** está en `Client.THEME_CHOICES` (los valores reales son
  `themes/default`, `themes/servelec`, `themes/andesscale`). `BOLT-66` ya corrigió el fallback de
  `apps/orders/views_onboarding.py`, pero este método sigue produciendo el mismo valor inválido
  cuando el JSON del plan está corrupto o nulo.
- Hallado por `BOLT-66`.

## Qué hacer

1. El fallback pasa a `['themes/default']`.
2. Además, el método **filtra** lo que devuelve: solo valores presentes en
   `Client.THEME_CHOICES`; si el filtro deja la lista vacía, también `['themes/default']`. Un plan
   con un tema que ya no existe no debe ofrecérselo al cliente.
3. No cambies el modelo ni crees migraciones: el campo `available_themes` queda igual. No toques
   los datos existentes de los planes.

## Tests de rojo

`apps.orders.tests.test_plan_available_themes_fallback` (archivo nuevo con ese nombre exacto).
Casos: `available_themes` nulo, string o dict → `['themes/default']`; lista válida
`['themes/default', 'themes/servelec']` → igual; lista con un valor inexistente
(`['themes/default', 'themes/borrado']`) → solo `['themes/default']`; lista de solo inválidos →
`['themes/default']`; lista vacía → `['themes/default']`.

## No tocar

`views_onboarding.py` (ya corregido), `forms.py`, migraciones, datos de planes.

## DoD

- [ ] El onboarding nunca recibe un tema fuera de `THEME_CHOICES`.
- [ ] Cierre documental (`DEUDA-13`): agrega la fila a la tabla `DEUDA` del kanban y bórrala en
      el mismo cambio, o, más simple, solo la línea en el histórico (la fila no existía).
