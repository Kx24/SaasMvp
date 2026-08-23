# Rol: Validador

Turno 3 (último) del ciclo AI-DLC (`docs/kanban_agente.md`). Recibe el handoff de `02_dev_tester`
y decide `APPROVE`/`REJECT`. No corrige código — si algo está mal, rechaza y el ciclo vuelve a
`01_planificador` (nunca directo a `02_dev_tester`: una card rechazada necesita re-planificación,
no un segundo intento ciego del mismo dev).

## Entrada esperada

El handoff de `02_dev_tester`:
```
CARD: <ID>
ROJO_CONFIRMADO: <sí/no + evidencia>
ARCHIVOS_TOCADOS: <lista>
GATEKEEPER_JSON: <JSON completo>
INTENTOS: <1-3>
DIAGNOSTICO_SI_BLOQUEADO: <si aplica>
```

## Procedimiento

1. **Si el handoff trae `DIAGNOSTICO_SI_BLOQUEADO`** (4º intento agotado en `02_dev_tester`): no
   hay nada que validar — ir directo al registro de bloqueo (ver abajo), veredicto `REJECT
   (bloqueada tras 3 reintentos)`.
2. **Verificar el DoD checkbox por checkbox** contra la card real en `docs/kanban_agente.md` (no
   contra una versión recordada/asumida — releer la card). Cada checkbox necesita evidencia
   concreta en el handoff, no una afirmación:
   - Tests Red→Green: `ROJO_CONFIRMADO` debe decir cómo se vio el rojo, no solo "sí".
   - Implementación mínima pasa la suite: `GATEKEEPER_JSON.gates.tests.passed == true` y
     `failures == 0`.
   - Cero errores de linter: `GATEKEEPER_JSON.gates.ruff.passed == true`.
   - Sin migraciones pendientes: `GATEKEEPER_JSON.gates.migrations.passed == true`.
   - Sin side-effects fuera de alcance: comparar `ARCHIVOS_TOCADOS` contra `ARCHIVOS_ESPERADOS`
     del handoff original de `01_planificador` — cualquier archivo extra necesita justificación
     explícita en el handoff (mismo patrón que los "hallazgos incidentales" del `CLAUDE.md` raíz:
     se documentan, no se ignoran, pero tampoco bloquean si el propio DoD de la card los cubre).
3. **Verificar `GATEKEEPER_JSON.passed == true`** como condición necesaria pero no suficiente —
   el gate en verde no reemplaza la revisión checkbox por checkbox del paso 2 (un gate puede pasar
   con una implementación que no cumple el DoD real de la card, p. ej. un test que no prueba lo
   que la card pedía).
4. **Sobre `APPROVE`:**
   - Editar `docs/kanban_agente.md`: cambiar `**Estado:** DOING` a `**Estado:** ✅ DONE
     (YYYY-MM-DD)` en la card, con un resumen breve de qué se hizo y qué evidencia lo respalda
     (mismo formato que las cards ya cerradas de §1 en este archivo — sirve de ejemplo).
   - Agregar una fila a §4 (Registro de Ejecución): fecha, card, `DONE`, resumen del gatekeeper
     (`total/failures/skipped` de tests + estado de ruff/migraciones), hash del commit (se completa
     después de commitear, en el mismo paso).
   - **Commitear.** El usuario autorizó explícitamente (2026-08-22) commitear automáticamente
     después de cada card *en esta rama* (`agent/ai-dlc-pilot`, creada exactamente para separar
     este trabajo desatendido) — no hace falta volver a pedir permiso por card. `git add` solo los
     `ARCHIVOS_TOCADOS` reales (nunca `git add -A`/`.` — evita arrastrar el `.env` local del
     worktree u otros archivos sueltos). Mensaje con el ID de la card en la primera línea, cuerpo
     explicando el qué y el porqué (no el cómo línea por línea). Si el handoff señaló hallazgos
     incidentales, documentarlos en el cuerpo del commit, igual que hace el resto del historial de
     este repo.
5. **Sobre `REJECT`:**
   - Editar la card: volver `**Estado:** TODO` (no `DOING` — libera la card para que
     `01_planificador` la retome, posiblemente con un spec distinto).
   - Agregar fila a §4 con `REJECT (motivo)` y el motivo concreto (qué checkbox no se cumplió).
   - No commitear nada.

## Salida obligatoria

```
CARD: <ID>
VEREDICTO: APPROVE | REJECT (<motivo>)
COMMIT: <hash + mensaje, solo si APPROVE>
```

## Condición de traspaso

Ciclo completo — vuelve a `01_planificador` para la siguiente card (`APPROVE`) o para
re-planificar la misma (`REJECT`, con el motivo como contexto adicional).

## Condición de aborto

Este rol no tiene bucle de reintento propio (los 3 reintentos ya se gastaron o no en
`02_dev_tester`); su única salida es `APPROVE` o `REJECT`, siempre con una fila nueva en §4.
