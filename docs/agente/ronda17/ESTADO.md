# Ronda 17 — estado

Rama `agent/ronda17` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-81` | `MOD-01` | MOD-01 parte 1a: modelo MediaAsset y embeds de video | ✅ DONE | 966 | 0.8 |
| `BOLT-82` | `MOD-01` | MOD-01 parte 1b: subida firmada a Cloudinary y alta de embeds | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-81`: Migración 0026_mediaasset: crea una tabla nueva y se revierte sin perder datos existentes.
- `BOLT-81`: El parser acepta también `www.vimeo.com`, algo que el spec no pedía (decisión del dev).
- `BOLT-81`: `max_images` ahora lo usan la galería y `media` a la vez; el spec lo pide como transitorio hasta la parte 3.
- `BOLT-81`: `MEDIA_MAX_EMBEDS` está definido pero nada lo aplica aún; debe aplicarse en BOLT-82 o en la parte 2.
- `BOLT-81`: Se modificaron tests existentes (`tests_modules.py`, `tests_admin_scope.py`) para incluir el módulo y el admin nuevos.
