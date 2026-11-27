# Ronda 17 — estado

Rama `agent/ronda17` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-81` | `MOD-01` | MOD-01 parte 1a: modelo MediaAsset y embeds de video | ✅ DONE | 966 | 0.8 |
| `BOLT-82` | `MOD-01` | MOD-01 parte 1b: subida firmada a Cloudinary y alta de embeds | ✅ DONE | 991 | 0.63 |

## Revisar a mano en el PR

- `BOLT-81`: Migración 0026_mediaasset: crea una tabla nueva y se revierte sin perder datos existentes.
- `BOLT-81`: El parser acepta también `www.vimeo.com`, algo que el spec no pedía (decisión del dev).
- `BOLT-81`: `max_images` ahora lo usan la galería y `media` a la vez; el spec lo pide como transitorio hasta la parte 3.
- `BOLT-81`: `MEDIA_MAX_EMBEDS` está definido pero nada lo aplica aún; debe aplicarse en BOLT-82 o en la parte 2.
- `BOLT-81`: Se modificaron tests existentes (`tests_modules.py`, `tests_admin_scope.py`) para incluir el módulo y el admin nuevos.
- `BOLT-82`: Probar a mano en desarrollo la subida real a Cloudinary con un archivo del teléfono (HEIC incluido) antes de la parte 2; los tests la simulan.
- `BOLT-82`: Confirmar que cloudinary.api.resource(public_id) funciona con el public_id que devuelve la subida (carpeta + id) y que el campo MediaAsset.image guarda el mismo formato; la idempotencia depende de eso.
- `BOLT-82`: Decisión del dev sin spec: respuesta 200 (no 201) cuando el asset o embed ya existía.
- `BOLT-82`: Revisar el rate limit de la firma: RateLimiter es en memoria del proceso (OPS-05), así que no es global entre workers.

## Hallazgos incidentales

- `BOLT-82`: Un public_id ya registrado devuelve 200 en vez de 201, tanto en confirmar como en embed; el spec no lo definía.
- `BOLT-82`: El tope de embeds (403) es independiente de check_limit, que cuenta solo imágenes.
