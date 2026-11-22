# BOLT-65 — `TOOL-08`: `test_gatekeeper` sin falsos rojos

## Contexto verificado (2026-11-18)

- `apps/core/tests/test_gatekeeper.py` tiene pruebas que ejecutan el gatekeeper completo como
  subproceso (`_run_gatekeeper`, `timeout=120`): `GatekeeperHealthyRepoTestCase` (3 tests, cada
  uno corre el gate entero) y `GatekeeperBrokenTestTestCase` (1 test).
- El gate corre la suite completa (más de 800 tests, ~1–3 min). Con tope de 120 s fallan por
  `TimeoutExpired` con la máquina cargada, y cada test repite la misma corrida. Ya generó falsos
  rojos en `BOLT-44`, `46` y `47`.
- `orchestrate.py` exporta `GATEKEEPER_TEST_RUN=1` al agente (ya hecho): dentro de las rondas
  estos tests se saltan. Esta card arregla el caso de correr la suite a mano o en la CI.

## Qué hacer

1. En `test_gatekeeper.py`: constante `GATEKEEPER_TEST_TIMEOUT_S = 900`, y
   `_run_gatekeeper(timeout=GATEKEEPER_TEST_TIMEOUT_S)`. Permite sobrescribirla con la variable de
   entorno `GATEKEEPER_TEST_TIMEOUT_S` (entero).
2. `GatekeeperHealthyRepoTestCase`: una sola corrida del gate para sus tres tests (resultado
   cacheado en `setUpClass`, `json.loads` una vez); los tres tests verifican sobre ese resultado
   lo mismo que hoy. La clase de fallo inyectado sigue corriendo el gate por su cuenta (necesita
   el archivo inyectado).
3. Un `TimeoutExpired` debe fallar con un mensaje que diga cuánto esperó y que sugiera subir
   `GATEKEEPER_TEST_TIMEOUT_S`.

## Tests de rojo

`apps.core.tests.test_gatekeeper_runtime` (archivo nuevo con ese nombre exacto; sin lanzar el gate
real, parchea `subprocess.run`). Casos: el timeout por defecto es ≥ 600; la variable de entorno lo
sobrescribe; la clase sana invoca `subprocess.run` exactamente una vez para sus tres tests (cuenta
las llamadas con un mock); un `TimeoutExpired` produce un fallo con el mensaje pedido.
Estos tests no deben saltarse con `GATEKEEPER_TEST_RUN=1` (no lanzan el gate).

## No tocar

`scripts/gatekeeper.py`, `scripts/gate_baseline.json`, `orchestrate.py` (rutas prohibidas). La
semántica de lo que verifican los tests existentes.

## DoD

- [ ] La suite a mano no da falsos rojos por tiempo y el gate se corre una vez por clase sana.
- [ ] Cierre documental (`TOOL-08`).
