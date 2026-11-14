# BOLT-25 — `DEUDA-06`: código muerto

## Contexto verificado (2026-11-14)

- `config/settings/cloudinary_settings.py`: su encabezado dice "Importar en base.py", pero nadie
  lo importa (`git grep cloudinary_settings` solo se encuentra a sí mismo).
- `apps/orders/services/order_processor.py::OrderProcessor`: solo lo re-exporta
  `apps/orders/services/__init__.py` (líneas 6–12); ninguna vista ni comando lo usa.
- `apps/marketing/0001_initial.py`: copia suelta de una migración, **fuera** de
  `apps/marketing/migrations/` (la real es `apps/marketing/migrations/0001_initial.py`).

## Qué hacer

1. Antes de borrar cada uno, confirma con `git grep` que nada lo importa ni lo referencia
   (código, tests, templates, `render.yaml`, documentación operativa). Si alguno **sí** se usa,
   no lo borres y explícalo en DECISIONES.
2. Test nuevo `apps/core/tests/test_dead_code_removed.py`: afirma que los tres archivos no
   existen y que `apps.orders.services` no expone `OrderProcessor`. Sirve de guardia contra que
   reaparezcan.
3. Borra los tres con `git rm` y limpia `apps/orders/services/__init__.py`. Si
   `Documentacion/ARQUITECTURA.md` o `docs/CLOUDINARY.md` los mencionan, corrige la mención.

## No tocar

`apps/marketing/migrations/`; cualquier otro código muerto que encuentres: repórtalo como
hallazgo, no lo borres.

## Tests de rojo

`apps.core.tests.test_dead_code_removed`

## DoD

- [ ] Los tres archivos fuera; suite, ruff y `makemigrations --check` verdes.
- [ ] La cobertura no baja.
- [ ] Cierre documental (`DEUDA-06`).
