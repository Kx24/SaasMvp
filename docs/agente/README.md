# Ejecución agéntica desatendida — cómo se opera

Desde la ronda 4 (2026-11-14). Las rondas 1–3 están en `docs/kanban_agente.md` (histórico).

## Reparto

| Paso | Quién | Dónde |
|---|---|---|
| Planificar: elegir cards, resolver decisiones, escribir specs | Sesión interactiva con el modelo grande + tú | `docs/agente/ronda<N>/BOLT-XX.md`, `cola.json` |
| Implementar | `claude -p` con Sonnet 5.5, una sesión nueva por card | `.claude/workflows/02_dev_tester.md` |
| Verificar | Código determinista, no un modelo | `scripts/gatekeeper.py --strict` + `--red-check` + control de alcance en `orchestrate.py` |
| Validar contra el DoD | `claude -p` con Sonnet 5.5, solo lectura | `.claude/workflows/03_validador.md` |
| Commit + push a `agent/*` | `orchestrate.py` | — |
| Revisar y mergear a `develop` | Tú | PR en GitHub / PyCharm |

## Lanzar una ronda

```bash
# en la rama de la ronda, con el árbol limpio
env/Scripts/python.exe orchestrate.py --ronda docs/agente/ronda4/cola.json --max-cards 4
```

- Toma las cards `TODO` en el orden de `cola.json`, una a la vez.
- Hasta 3 intentos de reparación por card. A la segunda card fallida la ronda se detiene
  (`--max-failures`).
- Card fallida (`BLOCKED` o `REJECTED`): su trabajo parcial queda en `git stash` y como parche en
  `scripts/output/`, el motivo en `ESTADO.md`, y la ronda sigue con la siguiente.
- Estado legible (también desde GitHub en el teléfono): `docs/agente/ronda<N>/ESTADO.md`.
  Incluye "Revisar a mano en el PR" y "Pendiente de tu decisión".
- Log completo: `scripts/output/orchestrator_<ts>.jsonl` (no se commitea).

## Qué impide que el agente haga daño

1. `.claude/settings.agent.json`: el agente no puede hacer commit, push, cambiar de rama, usar
   `git stash`, leer `.env`, editar el gate ni navegar la web.
2. Control de alcance en `orchestrate.py` (`FORBIDDEN_PATHS`): rutas prohibidas, migraciones y
   dependencias nuevas solo si `cola.json` las autoriza para esa card.
3. El gate lo corre el orquestador, no el agente. Cobertura y bandit son un trinquete contra
   `scripts/gate_baseline.json`: no pueden empeorar.
4. El rojo se confirma contra `HEAD` en un worktree temporal.
5. El push solo va a ramas `agent/*`. **La barrera real para `main` y `develop` es la protección
   de ramas de GitHub** (Settings → Branches → exigir pull request): actívala.

## Desde el teléfono (Remote Control)

Requiere el PC encendido con una sesión abierta:

```bash
claude --remote-control "AndesScale agente"
```

En la app de Claude (pestaña Code) aparece la sesión: puedes leer `ESTADO.md`, lanzar la ronda
("corre la ronda 4"), responder decisiones y aprobar permisos. Las notificaciones push llegan si
las activas en la app. Las sesiones `claude -p` que lanza el orquestador no piden permisos: lo
que no está permitido se deniega y la card queda `BLOCKED` con el motivo.

## Desbloquear una card

1. Lee el motivo en `ESTADO.md`.
2. Decide y escribe la decisión en el spec de la card (sección "Decisión").
3. Cambia su `estado` a `TODO` en `cola.json`, commitea y vuelve a lanzar.
4. Si quieres recuperar el trabajo parcial: `git stash list` y `git stash apply`.
