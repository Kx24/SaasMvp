# BOLT-76 — `DEUDA-11`: borrar `max_pages` de `Client` y de `Plan`

> Va **al final de la ronda**: es la única con migración.

## Decisión del dueño (2026-11-22)

Se borra en las dos tablas, con migración. No existe modelo de páginas y `MOD-00` descartó el
page-builder multipágina; el límite no se aplica a nada y confunde al comparar los límites de
`Plan` con los de `Client`. Se hace ahora, en consolidación y con pocos tenants en Neon.

## Contexto verificado (2026-11-22)

`max_pages` aparece en:
- `apps/tenants/models.py:90` (`Client.max_pages`, default 10) y `apps/tenants/admin.py:337`
  (`fieldsets`, junto a `max_images` y `max_services`).
- `apps/orders/models.py:106` (`Plan.max_pages`, default 5) y `apps/orders/admin.py:65`.
- `apps/orders/management/commands/setup_plans.py` (líneas ~46, 76 y 107: valores 5, 10 y 50).
- `apps/orders/views_onboarding.py:214` (`max_pages=plan.max_pages` al crear el `Client`).
- Docs vigentes: `MASTER_PLAN_Y_ARQUITECTURA.md` (líneas ~83 y ~163) y
  `Documentacion/AUDITORIA_PLATAFORMA_2026-11.md` (~36) lo nombran entre los límites. Las menciones
  en `docs/agente/` y en el histórico se dejan tal cual.

## Qué hacer

1. Quita el campo de ambos modelos y todas las referencias de arriba (admins, `setup_plans`,
   onboarding). Genera una migración por app afectada (`tenants` y `orders`).
2. Busca copy de planes que prometa "páginas" (templates de precios, emails, `features` de
   `setup_plans`): `grep -rniE "p[aá]ginas?" templates apps --include=*.html --include=*.py`.
   Si algún texto comercial promete un número de páginas, **no lo cambies**: repórtalo en
   `hallazgos` (es decisión de negocio).
3. Ajusta los docs vigentes que nombran `max_pages` (que queden `max_images` y `max_services`) y
   corre `apps.core.tests.test_docs_vigentes`.
4. Comprueba que la migración corre sobre la base de desarrollo con datos (`python manage.py
   migrate` sin fallar).

## Tests de rojo

`apps.tenants.tests_max_pages_removed` (archivo nuevo): ni `Client` ni `Plan` tienen un campo
`max_pages` (`_meta.get_field` lanza `FieldDoesNotExist`). Debe fallar contra el código actual.

## No tocar

`max_images`, `max_services`, `ClientSettings.hero_images_limit` / `gallery_images_limit` y el
flujo de límites de `BIZ-01`. Ninguna otra migración.

## DoD

- [ ] `max_pages` ya no existe en ningún modelo, admin, comando ni vista.
- [ ] Una migración por app, `makemigrations --check` limpio, suite en verde.
- [ ] Cierre documental: borra solo la fila `DEUDA-11` de la tabla y agrega la línea al histórico.
      El párrafo "Decisiones del dueño" de "Retomar aquí" lo edita el dueño, no tú.
