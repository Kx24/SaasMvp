# Ronda 5 — estado

Rama `agent/ronda5` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-24` | `SEC-05b` | Restos de alcance por tenant en el admin | ⛔ BLOCKED |  | 0 |
| `BOLT-25` | `DEUDA-06` | Código muerto | ✅ DONE | 313 | 0.39 |
| `BOLT-26` | `LEY-03` | Tope legal de 365 días para mensajes de contacto | ⏳ TODO |  |  |
| `BOLT-27` | `SEC-10` | Dependencias al día y pip-audit | ⏳ TODO |  |  |
| `BOLT-28` | `CONS-06` | Camino único para objetos del tenant | ⏳ TODO |  |  |
| `BOLT-29` | `CONS-07` | Separar views.py por área | ⏳ TODO |  |  |
| `BOLT-30` | `SEC-12` | Integración continua con el gate | ⏳ TODO |  |  |
| `BOLT-31` | `CONS-02` | Documentación al día | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-25`: Que borrar cloudinary_settings.py (CLOUDINARY_DEFAULT_LIMITS y CLOUDINARY_ALERT_THRESHOLDS) sea aceptable: OPS-04 los necesitará, aunque estaban sin uso.
- `BOLT-25`: Que la fila de DEUDA-06 se haya movido a la tabla del histórico en vez de dejarla como viñeta.
- `BOLT-25`: Documentación todavía desactualizada en README.md y MASTER_PLAN_Y_ARQUITECTURA.md (hallazgo sin card en el kanban).

## Hallazgos incidentales

- `BOLT-25`: Documentacion/README.md (líneas ~304, 312, 541, 665) todavía describe order_processor.py y cloudinary_settings.py como vigentes.
- `BOLT-25`: Documentacion/MASTER_PLAN_Y_ARQUITECTURA.md (líneas 86, 87, 149, 158) todavía menciona cloudinary_settings.py, CLOUDINARY_DEFAULT_LIMITS y OrderProcessor como existentes.
- `BOLT-25`: docs/kanban_agente.md (líneas 130, 444) menciona order_processor. Es histórico, pero puede inducir a error.
- `BOLT-25`: OPS-04 (alerta de créditos Cloudinary) sigue citando CLOUDINARY_ALERT_THRESHOLDS, que vivía en el archivo borrado; al implementarla habrá que definir los umbrales de nuevo.

## Pendiente de tu decisión

- `BOLT-24` (BLOCKED): la sesión del agente falló: timeout de 3600s
