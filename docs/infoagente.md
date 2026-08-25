# infoagente.md — Cómo operan los agentes de este repo

> Documento de referencia del piloto AI-DLC (desarrollo autónomo desatendido).
> Complementa `docs/kanban_agente.md` (el tablero operativo, fuente de verdad del
> *qué* está hecho) — este archivo explica el *cómo* y el *dónde*.

---

## 1. Mapa de rutas

| Ruta | Qué es |
|---|---|
| `C:\Users\sanch\Documents\Proyectos\SaaSMVP` | Checkout principal del repo (trabajo manual del usuario). Los agentes **no** operan acá. |
| `C:\Users\sanch\Documents\Proyectos\SaaSMVP-agentic-pilot` | **Worktree del piloto** (`git worktree add`, sibling del principal). Todo turno de agente corre acá, sobre la rama `agent/ai-dlc-pilot`. |
| `docs/kanban_agente.md` | Tablero del piloto: precondiciones (§0), cards (§1 infraestructura, §2 producto), bloqueadas (§3), registro de ejecución (§4). El planificador lo lee al inicio de cada corrida; el validador lo actualiza al cierre de cada card. |
| `.claude/workflows/01_planificador.md` | Prompt del rol Planificador (turno 1). |
| `.claude/workflows/02_dev_tester.md` | Prompt del rol Dev/Tester (turno 2, dueño del bucle REPAIR). |
| `.claude/workflows/03_validador.md` | Prompt del rol Validador (turno 3, único que commitea). |
| `.claude/skills/andesscale-saas/SKILL.md` | Conocimiento de dominio (templates multi-tenant, filtrado por tenant, provisioning). Los workflows lo referencian, no lo duplican. |
| `scripts/gatekeeper.py` | Gate determinista (PILOT-01): ruff + suite + migraciones, veredicto en JSON. Único mecanismo de verificación aceptado. |
| `orchestrate.py` (raíz) | Máquina de estados del ciclo (PILOT-03). **No invoca agentes reales** — ver §4. |
| `scripts/output/` | Logs JSONL del orquestador (`orchestrator_{timestamp}.jsonl`). Gitignorado. |
| `.env` (raíz del worktree) | Gitignorado, NO se copia con `git worktree add`. Debe existir con 4 valores dummy antes de correr el gatekeeper: `SECRET_KEY`, `MP_PUBLIC_KEY`, `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET` (detalle en `kanban_agente.md` §0.-1). |
| `Documentacion/KANBAN_PROYECTO.md` | Kanban maestro del producto (fuente de verdad del *producto*). El piloto lo actualiza solo cuando una card lo exige (ej: BOLT-01). |

---

## 2. El ciclo por card (WIP = 1)

Cada card recorre exactamente este circuito, definido en `kanban_agente.md` §0.3:

```
PLANIFICADOR ──handoff──▶ DEV/TESTER ──handoff──▶ VALIDADOR ──▶ commit + push
     ▲                        │  ▲                     │
     │                        ▼  │ (REPAIR, máx. 3)    │ APPROVE / REJECT
     └────── siguiente card ──┴──┘◀── gatekeeper ──────┘
```

### Turno 1 — Planificador (`01_planificador.md`)
- Lee el kanban completo (§0 primero), el registro §4 y el estado real del repo.
- Respeta **WIP=1**: si hay una card `DOING`, la retoma; si no, toma la primera `TODO`
  elegible en orden (§1 antes que §2), filtrando por §0.4 (restricciones) y §3 (bloqueadas).
- Marca la card `DOING` (su único cambio de producción) y produce el **spec del test**:
  qué comportamiento probar, en qué archivo (convención §0.0: paquete `tests/` en
  core/orders/website; archivo plano `tests_*.py` en tenants), y qué confirma el rojo.
- No escribe código de producción.

### Turno 2 — Dev/Tester (`02_dev_tester.md`)
- **Test primero, rojo confirmado**: el test nuevo debe fallar por la razón esperada
  (no por sintaxis/import) antes de implementar. Sin rojo visto no hay card cerrada.
- Implementación mínima → `python scripts/gatekeeper.py` desde la raíz del worktree.
- `passed: false` → bucle REPAIR con el JSON como diagnóstico. **Máximo 3 reintentos**;
  al 4º fallo la card pasa a `BLOCKED` con diagnóstico completo.
- Entrega handoff con `ROJO_CONFIRMADO`, `ARCHIVOS_TOCADOS` (reales), `GATEKEEPER_JSON`
  completo e `INTENTOS`.

### Turno 3 — Validador (`03_validador.md`)
- Verifica el **DoD checkbox por checkbox** contra la card real (releída, no recordada).
  El gate en verde es condición necesaria, no suficiente.
- Compara `ARCHIVOS_TOCADOS` vs. esperados; todo archivo extra necesita justificación
  (patrón "hallazgo incidental": se documenta, no se ignora).
- `APPROVE` → marca `DONE`, agrega fila a §4, commitea (un commit por card, ID en la
  primera línea) y **pushea** (ver `docs/tratamiento_git.md`). `REJECT` → la card vuelve
  a `TODO` y el ciclo re-planifica (nunca un segundo intento ciego del mismo dev).

---

## 3. El gatekeeper (contrato de verificación)

```bash
python scripts/gatekeeper.py
# → {"passed": bool,
#    "gates": {"ruff": {...}, "tests": {"total", "failures", "skipped"}, "migrations": {...}},
#    "duration_s": N}     — exit 0 ⇔ passed: true
```

- **ruff**: solo sobre archivos del diff vs `HEAD` + no trackeados (respeta la deuda
  preexistente de `#AUD-10` — ~135 errores globales reservados al usuario). Ojo: al tocar
  un archivo, el gate lo lintéa **completo**, así que deuda vieja de ese archivo puede
  aflorar (pasó en BOLT-02/03/07; se corrige lo mínimo, documentado como incidental).
- **tests**: `manage.py test apps -v 1`, suite completa.
- **migrations**: `makemigrations --check --dry-run`.
- Guarda anti-recursión: propaga `GATEKEEPER_TEST_RUN=1` para que sus propios tests
  (`apps/core/tests/test_gatekeeper.py`) se salteen dentro del gate (incidente de
  fork-bomb documentado en PILOT-01 — no tocar esa guarda).

---

## 4. orchestrate.py — qué es y qué NO es

`python orchestrate.py [--max-cards N] [--dry-run]` implementa **solo la máquina de
estados**: secuencia turnos, corta al primer `passed: true`, cuenta reintentos (tope 3),
decide `DONE`/`BLOCKED`/`REJECTED` y loguea JSONL por turno en `scripts/output/`.

- Recibe un `AgentRunner` (protocolo de 3 métodos: `run_planificador`,
  `run_dev_tester(card, attempt)`, `run_validador(card, dev_result)`).
- **Sin runner conectado lanza `NotImplementedError` a propósito** (`NotWiredAgentRunner`):
  no simula resultados ni maneja API keys. `--dry-run` usa un runner simulado sin costo.
- En la práctica actual, el "agente real" es una sesión de Claude Code operando en el
  worktree, que ejecuta los 3 turnos siguiendo los prompts de `.claude/workflows/` y
  respeta la misma semántica de la máquina de estados. Conectar el CLI en modo no
  interactivo como `AgentRunner` programático es un paso de integración pendiente,
  deliberadamente fuera de PILOT-03.

---

## 5. Políticas duras (no negociables por el agente)

1. **Cero preguntas por secretos** (§0.1): la suite, ruff, migraciones y el smoke E2E no
   requieren ninguna variable. Una card que descubre que necesita un secreto real se
   detiene, se marca `BLOCKED` y pasa a §3 — nunca se improvisa un valor ni se pregunta
   a mitad de turno. (Valores *dummy* sí valen cuando el código solo necesita que la
   variable exista, no que sea válida contra un servicio real.)
2. **No tocar Rancho Cachimba** (`#RC-*`, branch `feature/RanchocachimbaEtapa1` en pausa).
   Leer/copiar archivos *commiteados* de esa branch está permitido (pasó en BOLT-01/05);
   modificarla, no.
3. **No limpiar lint global preexistente** (`#AUD-10`) más allá de lo que el gate exige
   sobre archivos tocados.
4. **Convenciones de código de `CLAUDE.md`**: filtrado explícito por tenant, emails con
   `transaction.on_commit`, orden de `apps/orders/urls.py`, etc.
5. **Nada se commitea con la suite en rojo**; un commit por card; el kanban se actualiza
   en el mismo commit.

---

## 6. Gotchas aprendidos por el propio piloto

- **Trabajo varado en feature branches**: 4 artefactos que el kanban maestro daba por
  entregados existían solo en `feature/RanchocachimbaEtapa1`, nunca en `develop`
  (`SKILL.md`, retiro de `apps/core/managers.py`, `check_tenant_setup.py`,
  `Procedimiento_Nuevo_Tenant.md`). Antes de asumir que algo "ya existe", verificar con
  `git ls-files` / `git log --all -- <ruta>`.
- **Shadowing del `TenantTemplateLoader`**: un include de `'components/x.html'` se
  resuelve PRIMERO en `templates/{tema}/components/x.html`. Un grep de los `{% include %}`
  no dice qué archivo se renderiza de verdad (BOLT-07), y un componente compartido no
  puede llamarse igual que su wrapper de tema o el include recursa (BOLT-08 →
  `hero_ctas_base.html`).
- **El cwd de la shell puede resetearse entre llamadas**: todo comando dirigido al
  worktree lleva su propio `cd "...\SaaSMVP-agentic-pilot" &&` al inicio.
- **`.env` del worktree**: si el worktree se recrea, recrear el `.env` dummy antes de
  correr el gatekeeper (2 tests de checkout devuelven 400 sin los `MP_*` — artefacto
  conocido, no bug).

---

## 7. Cómo lanzar una corrida nueva

1. Verificar entorno: worktree correcto, rama `agent/ai-dlc-pilot` (o la rama nueva del
   lote), `.env` dummy presente, `python scripts/gatekeeper.py` en verde.
2. Iniciar el ciclo con el rol Planificador (`.claude/workflows/01_planificador.md`) y
   dejar que el circuito §2 corra card por card hasta "cola vacía".
3. Al terminar: rama pusheada, PR contra `develop` (ver `docs/tratamiento_git.md`).
