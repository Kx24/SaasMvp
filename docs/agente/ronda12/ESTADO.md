# Ronda 12 — estado

Rama `agent/ronda12` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-64` | `DASH-06` | Token --primary inexistente en el dashboard | ✅ DONE | 848 | 0.81 |
| `BOLT-65` | `TOOL-08` | test_gatekeeper sin falsos rojos | ⏳ TODO |  |  |
| `BOLT-66` | `DEUDA-12` | Residuos de las rondas 10 y 11 | ⏳ TODO |  |  |
| `BOLT-67` | `SEC-15` | Runbook de incidentes y rotación de secretos | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-64`: El dev modificó `apps/core/tests/test_docs_theme_choices.py`, que el spec no mencionaba, para que la suite pasara: CLAUDE.md cita `themes/andesscale` y el test lo excluía. Confirmar que ese criterio (CLAUDE.md compara con el conjunto completo, SKILL.md sin andesscale) es el que quieres.
- `BOLT-64`: Decidir si `--primary-rgb` merece su propia card, porque el fondo del ícono sigue sin el color de marca.

## Hallazgos incidentales

- `BOLT-64`: `index.html` línea 23 usa `var(--primary-rgb, 59, 130, 246)` para el fondo del ícono. Ese token tampoco existe, así que siempre cae al azul por defecto en vez del color de marca. Queda fuera del alcance de la card y sin registrar.
