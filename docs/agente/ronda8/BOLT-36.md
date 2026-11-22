# BOLT-36 — `CONS-11` (parte 1 de 4): cobertura de `tenants` núcleo ≥ 90 %

## Contexto verificado (2026-11-15)

- El contrato de TDD exige `apps/tenants/middleware.py` + `managers.py` ≥ 90 %. Hoy: 83,87 %
  (`scripts/gate_baseline.json`, clave `tenants_core`).
- `apps/tenants/managers.py`: 43 % (14 sentencias, 8 sin cubrir: líneas 33, 42, 51-53, 62-64 →
  `for_client`, `active`, `featured`, `ordered`, con y sin el atributo `is_featured` / `order`).
- `apps/tenants/middleware.py`: 91 % (sin cubrir 105-108 = atajo `?tenant=` con `DEBUG=True`;
  131, 141, 149).

## Qué hacer

1. Tests nuevos en `apps/tenants/tests_managers.py` (o el módulo de tests de tenants que
   corresponda) que ejerciten cada método del manager con modelos reales (`Section`, `Service`):
   `for_client` no devuelve filas de otro tenant; `active`; `featured` con un modelo que tiene
   `is_featured` y con uno que no; `ordered` con y sin `order`.
2. Tests para las líneas sin cubrir del middleware. El atajo `?tenant=` se prueba con
   `override_settings(DEBUG=True)` **y también** que con `DEBUG=False` el parámetro se ignora.
3. Son tests de comportamiento: cada uno afirma un resultado observable. No escribas tests que
   solo importan o llaman sin aserción.
4. Si un test destapa un bug real, arréglalo y repórtalo como hallazgo incidental.
5. Al final, con todo verde: `python scripts/gatekeeper.py --strict --update-baseline` (sube el
   trinquete). Es la única razón por la que esta card puede tocar `scripts/gate_baseline.json`;
   no lo edites a mano y verifica que ningún número bajó.

## No tocar

El código de `middleware.py` y `managers.py` salvo bug demostrado por un test. `COVERAGE_OMIT` y
el resto de `scripts/gatekeeper.py`. No agregues `# pragma: no cover`.

## DoD

- [ ] `tenants_core` ≥ 90 % en `scripts/gate_baseline.json`, y `orders`/`total` no bajan.
- [ ] Suite completa y suite de aislamiento verdes.
- [ ] Cierre documental: `CONS-11` **parcial** (actualiza el número de tenants en la fila).
      En `revisar_humano`: porcentajes antes y después.
