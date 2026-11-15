# Ronda 5 — estado

Rama `agent/ronda5` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-24` | `SEC-05b` | Restos de alcance por tenant en el admin | ⛔ BLOCKED |  | 0 |
| `BOLT-25` | `DEUDA-06` | Código muerto | ✅ DONE | 313 | 0.39 |
| `BOLT-26` | `LEY-03` | Tope legal de 365 días para mensajes de contacto | ✅ DONE | 320 | 0.57 |
| `BOLT-27` | `SEC-10` | Dependencias al día y pip-audit | ❌ REJECTED |  | 0.57 |
| `BOLT-28` | `CONS-06` | Camino único para objetos del tenant | ⏳ TODO |  |  |
| `BOLT-29` | `CONS-07` | Separar views.py por área | ⏳ TODO |  |  |
| `BOLT-30` | `SEC-12` | Integración continua con el gate | ⏳ TODO |  |  |
| `BOLT-31` | `CONS-02` | Documentación al día | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-25`: Que borrar cloudinary_settings.py (CLOUDINARY_DEFAULT_LIMITS y CLOUDINARY_ALERT_THRESHOLDS) sea aceptable: OPS-04 los necesitará, aunque estaban sin uso.
- `BOLT-25`: Que la fila de DEUDA-06 se haya movido a la tabla del histórico en vez de dejarla como viñeta.
- `BOLT-25`: Documentación todavía desactualizada en README.md y MASTER_PLAN_Y_ARQUITECTURA.md (hallazgo sin card en el kanban).
- `BOLT-26`: Hay un cambio de comportamiento destructivo en producción: los mensajes new sin leer de más de 365 días se borrarán, incluso en tenants con la purga apagada. La decisión es del dueño, pero conviene que lo confirme al mergear.
- `BOLT-26`: La purga solo corre cuando se ejecuta send_contact_digest. Sin el cron de OPS-06 en Render no se ejecuta en producción.
- `BOLT-26`: El plazo de 365 días todavía no está publicado en la política de privacidad (sigue pendiente en LEY-03).
- `BOLT-26`: El texto visible al cliente en el digest es nuevo: «Se eliminaron N mensajes con más de 365 días (plazo máximo de conservación)».

## Hallazgos incidentales

- `BOLT-25`: Documentacion/README.md (líneas ~304, 312, 541, 665) todavía describe order_processor.py y cloudinary_settings.py como vigentes.
- `BOLT-25`: Documentacion/MASTER_PLAN_Y_ARQUITECTURA.md (líneas 86, 87, 149, 158) todavía menciona cloudinary_settings.py, CLOUDINARY_DEFAULT_LIMITS y OrderProcessor como existentes.
- `BOLT-25`: docs/kanban_agente.md (líneas 130, 444) menciona order_processor. Es histórico, pero puede inducir a error.
- `BOLT-25`: OPS-04 (alerta de créditos Cloudinary) sigue citando CLOUDINARY_ALERT_THRESHOLDS, que vivía en el archivo borrado; al implementarla habrá que definir los umbrales de nuevo.
- `BOLT-26`: _purge_beyond_legal_cap está anotado como -> str pero devuelve None en los casos sin purga y en dry-run (cosmético; el método existente _purge_old_contacts tiene el mismo patrón).
- `BOLT-26`: El tope se aplica por created_at, no por la última actividad del mensaje, y no hay aviso previo al cliente antes de borrar mensajes new sin leer.

## Pendiente de tu decisión

- `BOLT-24` (BLOCKED): la sesión del agente falló: timeout de 3600s
- `BOLT-27` (REJECTED): El DoD exige `pip-audit` limpio sobre requirements.txt y el propio informe dice que sigue con pillow==11.0.0 y 71 avisos. Tampoco hay evidencia de Playwright con las versiones nuevas (el gate marca e2e `ran: false`).
