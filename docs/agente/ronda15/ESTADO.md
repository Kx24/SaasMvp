# Ronda 15 — estado

Rama `agent/ronda15` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-74` | `DEUDA-15` | Borrar el comando create_tenant y sus tests | ✅ DONE | 931 | 0.54 |
| `BOLT-75` | `DEUDA-16` | Quitar TenantSectionsSitemap del sitemap | ✅ DONE | 938 | 0.83 |
| `BOLT-76` | `DEUDA-11` | Borrar max_pages de Client y Plan | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-74`: La cobertura total bajó de 90.27% a 90.10% y la de orders de 92.46% a 92.41%, por borrar código cubierto; el gate pasó, pero el baseline de gate_baseline.json quizá convenga recalibrarlo.
- `BOLT-74`: Las menciones de create_tenant en docs/kanban_agente.md y en Documentacion/KANBAN_PROYECTO.md (sección Retomar aquí, línea 31) quedaron intactas a propósito: son históricas o de decisiones.
- `BOLT-75`: Decidir DEUDA-18: agregar los campos de teléfono y dirección a ClientSettings o borrar las ramas.
- `BOLT-75`: tests_seoconfig_model.py es un archivo de tests nuevo que no pedía el spec; se agregó solo para sostener la cobertura total. Conviene mirar que no fije comportamiento que se quiera cambiar (por ejemplo, que telephone y address no aparezcan en el JSON-LD).
- `BOLT-75`: El dev no confirmó si la baja de cobertura de orders (92.41% contra 92.46%) viene de antes de este cambio.

## Hallazgos incidentales

- `BOLT-75`: DEUDA-18: SEOConfig.get_schema_json lee settings.phone y settings.address, campos que ClientSettings no tiene; esas ramas nunca se ejecutan. Ya está en el kanban.
- `BOLT-75`: La cobertura de orders (92.41%) queda bajo su baseline (92.46%). El gate pasó igual y el dev no confirmó si la baja es previa a este cambio.
