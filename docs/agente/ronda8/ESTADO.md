# Ronda 8 — estado

Rama `agent/ronda8` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-36` | `CONS-11` | Cobertura de tenants núcleo ≥ 90 % (1 de 4) | ✅ DONE | 423 | 0.53 |
| `BOLT-37` | `CONS-11` | Cobertura de orders ≥ 80 % (2 de 4) | ⏳ TODO |  |  |
| `BOLT-38` | `CONS-11` | Cobertura de core y servicios de tenants (3 de 4) | ⏳ TODO |  |  |
| `BOLT-39` | `CONS-11` | Cobertura total ≥ 70 % y cierre (4 de 4) | ⏳ TODO |  |  |
| `BOLT-40` | `CONS-12` | Guardia de objetos de tenant en orders y accounts | ⏳ TODO |  |  |
| `BOLT-41` | `SEC-18` | Un solo TenantAdminMixin | ⏳ TODO |  |  |
| `BOLT-42` | `COMP-03` | Botón de enviar sin quedarse en Enviando | ⏳ TODO |  |  |
| `BOLT-43` | `DEUDA-09` | Borrar la vista dashboard_services huérfana | ⏳ TODO |  |  |
| `BOLT-44` | `FLOW-04` | provision_tenant deja un Domain primario | ⏳ TODO |  |  |
| `BOLT-45` | `LEY-08` | Aviso previo antes de purgar mensajes sin leer | ⏳ TODO |  |  |
| `BOLT-46` | `TOOL-04` | Pulido de la CI y dependencias de desarrollo | ⏳ TODO |  |  |
| `BOLT-47` | `DOC-01` | Documentación al día tras las rondas 4 a 8 | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-36`: Cobertura antes y después: tenants_core 83,87 % → 100 %; total 65,04 % → 65,32 %; orders 70,41 % → 70,41 % (sin cambio).
- `BOLT-36`: scripts/gate_baseline.json lo actualizó el gate (--update-baseline). Ningún número bajó.
- `BOLT-36`: No hay test en rojo contra HEAD porque la card solo agrega cobertura sobre código que ya funcionaba. Es lo esperado, pero conviene saberlo.
- `BOLT-36`: El dev agregó CONS-11 (parte) al histórico con formato de fila de tabla, no de viñeta como decía el spec. Mira si te sirve así.
