# BOLT-72 — `OPS-05` (parte): endpoint `/health/` real

## Contexto verificado (2026-11-18)

- No existe ningún endpoint de salud (`grep -rn health apps config` no da nada fuera de tests).
  Render hoy no tiene "Health Check Path" configurado, así que un deploy con la app rota no se
  detecta.
- El middleware de tenants (`apps/tenants/middleware.py`) resuelve el `Host` contra una
  allowlist dinámica (`Domain`) y tiene prefijos de bypass (`CONSTRUCTION_BYPASS_PREFIXES`,
  `SYSTEM_DOMAINS`). Render consulta el health check con el host del propio servicio
  (`*.onrender.com`), que **no** es un `Domain` de tenant: hay que comprobar qué hace el
  middleware con ese host y con la ruta `/health/`.
- `config/urls.py` incluye primero `apps.tenants.urls` en `''`; el orden importa
  (`CLAUDE.md`, gotcha de `apps/orders/urls.py`).

## Qué hacer

1. Vista `health` (en `apps/core/views.py` o archivo nuevo en `apps/core/`): `GET /health/`
   responde `200` con JSON `{"status": "ok", "database": "ok"}` tras ejecutar `SELECT 1`; si la
   base falla, `503` con `{"status": "error", "database": "error"}`. Sin autenticación, sin
   datos de tenants, sin nombres de modelos ni mensajes de excepción en la respuesta (no filtrar
   detalles); el error real va al log.
2. Ruta `health/` en `config/urls.py`. Que funcione con cualquier `Host` (incluido el de Render
   y `localhost`) y con un tenant en construcción: ajusta el middleware **solo** para dejar pasar
   esta ruta exacta, con test.
3. Solo `GET` y `HEAD`; otros métodos → 405. Sin cache (`never_cache`).
4. `Documentacion/ARQUITECTURA.md` (operación): describe el endpoint y que hay que configurar
   en Render el "Health Check Path" = `/health/` (no edites `render.yaml`: está protegido).

## Tests de rojo

`apps.core.tests.test_health` (archivo nuevo con ese nombre exacto). Casos: 200 y JSON esperado
con `Host` de un tenant, con `Host` desconocido (`servicio.onrender.com`) y con `localhost`;
tenant en construcción (`mode_under_construction`) también 200; `connection.cursor` parcheado
para lanzar → 503 y la respuesta no contiene el texto de la excepción; `POST` → 405; no exige
login.

## No tocar

`render.yaml`, `build.sh`, el resto de rutas. Nada de Sentry ni de cache compartida (otras partes
de `OPS-05`).

## DoD

- [ ] `/health/` responde 200/503 sin depender del `Host`.
- [ ] Cierre documental: `OPS-05` se **acota** (queda cache compartida y Sentry); anota
      `OPS-05 (parcial)` en el histórico.
- [ ] En `revisar_humano`: configurar el Health Check Path en Render.
