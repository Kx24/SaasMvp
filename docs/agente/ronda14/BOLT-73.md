# BOLT-73 — `DEUDA-14`: dos arreglos chicos que dejó la ronda 13

## Contexto verificado (2026-11-18)

- `apps/tenants/management/commands/setup_cloudinary_folders.py` importa `cloudinary` y
  `cloudinary.uploader` (líneas 8-9) pero llama `cloudinary.api.resources(...)` (~línea 69).
  Funciona solo porque otro módulo ya importó `cloudinary.api` antes: si el comando corre solo, es
  un `AttributeError`. Hallado por `BOLT-70`.
- Cinco archivos de tests siguen armando planes con `available_themes=['default']`, un slug que
  `Plan.get_available_themes_list` ahora filtra por inválido (`BOLT-69`): `apps/core/tests/
  test_data_subject_command.py`, `apps/orders/tests/test_checkout_consent.py`,
  `test_checkout_views.py`, `test_onboarding.py`, `test_onboarding_views.py`. Hoy pasan, pero
  prueban contra un valor que ya no existe. Hallado por `BOLT-69`.

## Qué hacer

1. `setup_cloudinary_folders.py`: agrega `import cloudinary.api` junto a los otros imports.
2. En esos cinco archivos, reemplaza `['default']` en `available_themes` por
   `['themes/default']`. Si algún test depende explícitamente del slug viejo (p. ej. prueba el
   filtrado), déjalo y anótalo en el informe. No debilites ninguna aserción.

## Tests de rojo

`apps.tenants.tests_setup_cloudinary_folders_import` (archivo nuevo con ese nombre exacto): corre
el módulo del comando en un subproceso limpio (`python -c "import apps.tenants.management.commands.setup_cloudinary_folders as m; import cloudinary; assert hasattr(cloudinary, 'api')"` con
`DJANGO_SETTINGS_MODULE` ya fijado por el entorno, sin importar `cloudinary.api` antes) o,
equivalente, inspecciona el AST del módulo y comprueba que `cloudinary.api` está importado. Debe
fallar contra el código actual y pasar con el cambio. Los cambios de fixtures no llevan test
propio (los cubre la suite existente).

## No tocar

`audit_cloudinary_assets` (su heurística de referencias es una decisión aparte), el sitemap de
secciones (decisión del dueño), `Plan.get_available_themes_list`.

## DoD

- [ ] El comando importa `cloudinary.api` por sí mismo.
- [ ] Ningún test arma planes con el slug viejo salvo que pruebe justamente el filtrado.
- [ ] Cierre documental: agrega la línea `DEUDA-14` al histórico (la fila no existía en el kanban).
