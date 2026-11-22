# BOLT-77 — `DEUDA-18`: el JSON-LD lee un campo de teléfono que no existe

## Decisión del dueño (2026-11-22)

Se arregla leyendo el campo real. No se agregan campos nuevos.

## Contexto verificado (2026-11-22)

- `apps/marketing/models.py` (`SEOConfig.get_schema_json`, ~línea 166): lee `settings.phone`, pero
  `ClientSettings` (`apps/tenants/models.py` ~316) tiene `contact_phone` y `address`. Resultado: el
  JSON-LD nunca incluye `telephone`. La rama de `address` sí funciona.
- La misma función lee `settings.description`: comprueba si `ClientSettings` tiene ese campo; si no
  existe, es el mismo bug: corrígelo leyendo el campo real si hay uno equivalente, o regístralo en
  `hallazgos` si no lo hay.
- `apps/marketing/tests_seoconfig_model.py` (agregado en `BOLT-75`) fija que `telephone` **no**
  aparece en el JSON-LD. Esa aserción describe el bug: cámbiala para que exija el teléfono.

## Qué hacer

1. Cambia `settings.phone` por `settings.contact_phone`.
2. Ajusta `tests_seoconfig_model.py` para el comportamiento correcto, sin debilitar el resto.

## Tests de rojo

`apps.marketing.tests_schema_telefono` (archivo nuevo): un `ClientSettings` con `contact_phone`
produce un JSON-LD con `"telephone"` igual a ese valor; sin teléfono, la clave no aparece. Debe
fallar contra el código actual.

## No tocar

Modelos y migraciones; el resto de `get_schema_json`.

## DoD

- [ ] El JSON-LD incluye el teléfono cuando el tenant lo tiene.
- [ ] Cierre documental: borra la fila `DEUDA-18` y agrega la línea al histórico.
