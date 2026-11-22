# Ronda 15 — estado

Rama `agent/ronda15` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-74` | `DEUDA-15` | Borrar el comando create_tenant y sus tests | ✅ DONE | 931 | 0.54 |
| `BOLT-75` | `DEUDA-16` | Quitar TenantSectionsSitemap del sitemap | ⏳ TODO |  |  |
| `BOLT-76` | `DEUDA-11` | Borrar max_pages de Client y Plan | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-74`: La cobertura total bajó de 90.27% a 90.10% y la de orders de 92.46% a 92.41%, por borrar código cubierto; el gate pasó, pero el baseline de gate_baseline.json quizá convenga recalibrarlo.
- `BOLT-74`: Las menciones de create_tenant en docs/kanban_agente.md y en Documentacion/KANBAN_PROYECTO.md (sección Retomar aquí, línea 31) quedaron intactas a propósito: son históricas o de decisiones.
