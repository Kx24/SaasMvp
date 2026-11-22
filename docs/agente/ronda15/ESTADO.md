# Ronda 15 — estado

Rama `agent/ronda15` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-74` | `DEUDA-15` | Borrar el comando create_tenant y sus tests | ✅ DONE | 931 | 0.54 |
| `BOLT-75` | `DEUDA-16` | Quitar TenantSectionsSitemap del sitemap | ✅ DONE | 938 | 0.83 |
| `BOLT-76` | `DEUDA-11` | Borrar max_pages de Client y Plan | ✅ DONE | 940 | 0.38 |

## Revisar a mano en el PR

- `BOLT-74`: La cobertura total bajó de 90.27% a 90.10% y la de orders de 92.46% a 92.41%, por borrar código cubierto; el gate pasó, pero el baseline de gate_baseline.json quizá convenga recalibrarlo.
- `BOLT-74`: Las menciones de create_tenant en docs/kanban_agente.md y en Documentacion/KANBAN_PROYECTO.md (sección Retomar aquí, línea 31) quedaron intactas a propósito: son históricas o de decisiones.
- `BOLT-75`: Decidir DEUDA-18: agregar los campos de teléfono y dirección a ClientSettings o borrar las ramas.
- `BOLT-75`: tests_seoconfig_model.py es un archivo de tests nuevo que no pedía el spec; se agregó solo para sostener la cobertura total. Conviene mirar que no fije comportamiento que se quiera cambiar (por ejemplo, que telephone y address no aparezcan en el JSON-LD).
- `BOLT-75`: El dev no confirmó si la baja de cobertura de orders (92.41% contra 92.46%) viene de antes de este cambio.
- `BOLT-76`: Dos migraciones: orders 0004 (RemoveField Plan.max_pages) y tenants 0032 (RemoveField Client.max_pages). Los valores guardados se pierden al aplicarlas, como decidió el dueño. Hay que correr migrate en Neon al desplegar.
- `BOLT-76`: Decidir qué hacer con la promesa de "5/10/50 páginas" que queda en MASTER_PLAN §4.3.
- `BOLT-76`: El párrafo "Decisiones del dueño" de "Retomar aquí" no fue tocado, como pide el spec, y lo edita el dueño.
- `BOLT-76`: El dev no corrió el rojo él mismo. El red_check del orquestador sí lo confirmó.

## Hallazgos incidentales

- `BOLT-75`: DEUDA-18: SEOConfig.get_schema_json lee settings.phone y settings.address, campos que ClientSettings no tiene; esas ramas nunca se ejecutan. Ya está en el kanban.
- `BOLT-75`: La cobertura de orders (92.41%) queda bajo su baseline (92.46%). El gate pasó igual y el dev no confirmó si la baja es previa a este cambio.
- `BOLT-76`: MASTER_PLAN_Y_ARQUITECTURA.md §4.3 (~línea 161) sigue describiendo los planes con "5 páginas / 10 / 50 páginas" (Esencial, Pro y Enterprise). Es copy comercial en un doc vigente, y el spec manda reportarlo en vez de cambiarlo. Decisión de negocio: si el número de páginas se sigue vendiendo o se quita.
- `BOLT-76`: El dev reportó que no hay copy comercial con páginas. Eso es cierto en templates y setup_plans, pero el MASTER_PLAN sí lo tiene, como se ve arriba.
