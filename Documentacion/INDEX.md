# Mapa de documentación — AndesScale SaaS

> Actualizado 2026-11-12. Regla: **un tema, un archivo vigente**. Si un documento deja de ser cierto, va a `historico/` (con `git mv`, no se borra); no se deja "para después" en su lugar original.

## 1. Planificación (qué falta, qué se hizo)

| Archivo | Para qué |
|---|---|
| [`KANBAN_PROYECTO.md`](KANBAN_PROYECTO.md) | **Único tablero.** Ahora / Siguiente / Bloqueado / Backlog + arnés de TDD. Empezar siempre acá |
| [`historico/KANBAN_HISTORICO.md`](historico/KANBAN_HISTORICO.md) | Todo lo ya hecho, una línea por card con fecha y commit |
| [`historico/KANBAN_PROYECTO_snapshot_2026-11-10.md`](historico/KANBAN_PROYECTO_snapshot_2026-11-10.md) | El kanban viejo íntegro (detalle de DoD, hallazgos y tests de cada card) |
| [`AUDITORIA_PLATAFORMA_2026-11.md`](AUDITORIA_PLATAFORMA_2026-11.md) | Auditoría de código vs. objetivo "plataforma modular": brecha, opciones de diseño y factibilidad (2026-11-11) |

## 2. Estrategia y negocio

| Archivo | Para qué | Estado |
|---|---|---|
| [`../MASTER_PLAN_Y_ARQUITECTURA.md`](../MASTER_PLAN_Y_ARQUITECTURA.md) | Diagnóstico técnico/legal, viabilidad comercial, pricing y costos (§3–4), URL temporal (§4.6). Su §2 (tablero) migró al kanban | Vigente |

## 3. Cómo funciona el sistema

| Archivo | Para qué | Estado |
|---|---|---|
| [`../CLAUDE.md`](../CLAUDE.md) | Guía operativa para trabajar con Claude Code (comandos, arquitectura, gotchas) | Vigente |
| [`ARQUITECTURA.md`](ARQUITECTURA.md) | Arquitectura actual: ciclo de un request, cada tecnología y qué hace, apps, modelo de datos Django, flujos, despliegue (2026-11-12) | Vigente |
| [`SEGURIDAD.md`](SEGURIDAD.md) | Controles vigentes, hallazgos del chequeo, mapa Ley 21.719, checklist por release (2026-11-12) | Vigente |
| [`../docs/design-system.md`](../docs/design-system.md) | Contrato de temas, tokens CSS y componentes compartidos | Vigente |
| [`../docs/CLOUDINARY.md`](../docs/CLOUDINARY.md) | Integración con Cloudinary (enero 2026) | ⚠️ Revisar contra `apps/core/cloudinary_utils.py` |
| [`README.md`](README.md) | Documentación técnica larga (2026-08-24) | ⚠️ Revisar; aún dice "Supabase" (`CONS-02`) |
| [`../README.md`](../README.md) | README del repo | ⚠️ Desactualizado (diciembre 2025): reescribir corto |

## 4. Operación

| Archivo | Para qué |
|---|---|
| [`Procedimiento_Nuevo_Tenant.md`](Procedimiento_Nuevo_Tenant.md) | Runbook de alta de cliente (+ checklist de custodia DNS) |
| [`Inventario_Secretos.md`](Inventario_Secretos.md) | Qué env vars/secretos existen y dónde viven |
| [`Ley-21719_13-DIC-2024.pdf`](Ley-21719_13-DIC-2024.pdf) | Texto oficial de la Ley 21.719 (BCN, rige el 1-dic-2026). Su aplicación a la plataforma está en `SEGURIDAD.md` §3 |

## 5. Piloto agéntico (se queda en `docs/` porque el código lo referencia por ruta)

[`../docs/kanban_agente.md`](../docs/kanban_agente.md) · [`../docs/infoagente.md`](../docs/infoagente.md) · [`../docs/tratamiento_git.md`](../docs/tratamiento_git.md) · prompts por rol en `../.claude/workflows/` · skill en `../.claude/skills/andesscale-saas/SKILL.md`. Referenciados por `orchestrate.py`, `scripts/gatekeeper.py` y sus tests; moverlos exige tocar código.

## 6. Histórico (`historico/`)

| Carpeta | Contenido |
|---|---|
| `kanbans_anteriores/` | `KanBan_NuevoCliente`, `Kanban_Plataforma_v2` y `Kanban_RanchoCachimba` (ya fusionados el 2026-08-20), `Prompt_Kanban_Setup` |
| `estructura_vieja/` | Árboles de carpetas de enero/agosto (`estructura_proyecto*`, `Structure.md`, `Estructura.txt`), obsoletos |
| `auditorias_y_manuales/` | `AUDITORIA_ARQUITECTURA_Y_NEGOCIO` (09-24, absorbida por el Master Plan), `ARQUITECTURA_SISTEMA_2026-09` (reemplazada por `ARQUITECTURA.md`) y `MANUAL_MCP_GITHUB` (el MCP se retiró) |

## Pendientes de documentación (cards en el kanban)

- Reescribir `README.md` raíz y revisar `Documentacion/README.md`, `docs/CLOUDINARY.md` → `CONS-02`.
- `Informe_Cumplimiento_Ley21719.md` lo cita el Master Plan §1.4 pero **no está en el repo**: ubicarlo o regenerarlo → `LEY-00`.
- Carpeta vacía sin trackear `Documentacion/Planificacion/` (solo `.claude/`, sin acento; la con acento se vació): borrar a mano si no la usás.
