# BOLT-79 — `DEUDA-17`: `audit_cloudinary_assets` cuenta cualquier `CharField` como referencia

## Decisión del dueño (2026-11-22)

Se acota la detección de referencias.

## Contexto verificado (2026-11-22)

- `apps/core/management/commands/audit_cloudinary_assets.py::_collect_db_references` (~línea 212)
  toma como referencia **cualquier** `CharField` no vacío de cualquier modelo (nombres, correos,
  slugs…). El docstring dice que solo debía tomar los `CharField` con valores `tenants/...`.
- **Cuidado: el comando tiene modo de purga** (`_purge_orphans`). Hoy el error es del lado seguro
  (sobran referencias, quedan menos huérfanos). Acotar mal la detección haría que un asset en uso
  parezca huérfano y la purga lo borre de Cloudinary. **La dirección del cambio es de riesgo.**

## Qué hacer

1. Los `CloudinaryField` se siguen tomando tal cual.
2. De los `CharField`, cuenta solo los valores que parezcan un `public_id` de Cloudinary: que empiecen
   con un prefijo de carpeta conocido. Toma los prefijos de `apps/core/cloudinary_utils.py`
   (`get_cloudinary_folder`, la lista de categorías) y **también** los prefijos legacy `{slug}/...`
   que dejaron las subidas del dashboard (hallado por `BOLT-13`: carpeta `{slug}/…` en vez de
   `tenants/{slug}/…`). Si dudas de un prefijo, inclúyelo: en caso de duda, contar de más.
3. No cambies el modo de purga ni sus confirmaciones.

## Tests de rojo

`apps.core.tests.test_audit_cloudinary_referencias` (archivo nuevo): un modelo con un `CharField`
cuyo valor no es un `public_id` (p. ej. el nombre de un cliente) **no** cuenta como referencia; un
`CharField` con `tenants/<slug>/gallery/x` y uno con `<slug>/gallery/x` **sí** cuentan. Sin red:
parchea `cloudinary.api`. Debe fallar contra el código actual.

## No tocar

`_purge_orphans`, `_list_cloudinary_assets`, la heurística de `CloudinaryField`, otros comandos.

## DoD

- [ ] Solo cuentan como referencia los `CloudinaryField` y los `CharField` con prefijo de Cloudinary.
- [ ] Ningún caso nuevo hace que un asset en uso aparezca como huérfano (anótalo en el informe).
- [ ] Cierre documental: borra la fila `DEUDA-17` y agrega la línea al histórico.
