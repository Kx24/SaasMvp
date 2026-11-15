# BOLT-31 — `CONS-02`: documentación al día

## Contexto verificado (2026-11-14)

- `CLAUDE.md` dice "Supabase/Postgres" (la base de producción es **Neon**), "68 tests", que el
  aislamiento "corre en cada push", y conserva la sección completa "Automatización Git/GitHub
  (MCP)" aunque el MCP de GitHub se retiró (PRs y push se hacen desde PyCharm/GitHub).
- `Documentacion/README.md` (906 líneas) y `README.md` raíz arrastran lo mismo.
- `.gitignore` no ignora `.coverage`.

Esta card está autorizada a editar `CLAUDE.md`. **No** puede editar `.claude/` (el skill
`andesscale-saas` queda pendiente: repórtalo, no lo intentes).

## Qué hacer

1. Test nuevo `apps/core/tests/test_docs_drift.py` (guardia anti-desfase, estilo `BOLT-10`):
   - `CLAUDE.md`, `README.md` y `Documentacion/README.md` no contienen `Supabase` (sin distinguir
     mayúsculas).
   - `CLAUDE.md` no contiene `github-mcp-server`, `MCP Server` ni "corre en cada push".
   - `CLAUDE.md` menciona `docs/agente/README.md` y `scripts/gatekeeper.py --strict`.
   - `.gitignore` contiene `.coverage`.
2. `CLAUDE.md`:
   - "Supabase/Postgres" → "Neon (Postgres)".
   - Suite: quita el número fijo de tests; deja "ver `Documentacion/KANBAN_PROYECTO.md`".
   - Aislamiento: "corre en cada push" → "lo corre el gate y la CI" si
     `.github/workflows/ci.yml` existe; si no existe, "lo corre el gate".
   - Reemplaza la sección "Automatización Git/GitHub (MCP)" por una breve "Git y PRs": push y PRs
     los hace el dueño desde PyCharm/GitHub; antes de cerrar o cambiar de rama,
     `git status --short --branch` y `git log origin/<rama>..<rama> --oneline`; cherry-pick hacia
     `develop` solo mostrando el diff y con confirmación.
   - En "Branches": agrega que las ramas `agent/*` son del agente desatendido (único destino de
     push automático) y enlaza `docs/agente/README.md`.
   - En "El arnés de TDD": agrega una línea sobre `scripts/gatekeeper.py --strict` (trinquete de
     cobertura y bandit en `scripts/gate_baseline.json`) y `--red-check`.
   - En "Dónde mirar primero": quita la línea del manual histórico del MCP si sigue ahí.
   - No cambies nada más: es el archivo de instrucciones del dueño.
3. `README.md` raíz: reescríbelo corto (qué es, stack real, cómo levantar, cómo correr tests y
   gate, dónde está la documentación). Máximo unas 60 líneas.
4. `Documentacion/README.md`: solo corrige Supabase → Neon y referencias al MCP; no lo
   reestructures.
5. `docs/CLOUDINARY.md`: revisa que los nombres de funciones y presets citados existan en
   `apps/core/cloudinary_utils.py`; corrige los que no.
6. `.gitignore`: agrega `.coverage`, `.coverage.*`, `htmlcov/` en la sección de temporales.

## Tests de rojo

`apps.core.tests.test_docs_drift`

## DoD

- [ ] Guardia verde; fallaba antes.
- [ ] `CLAUDE.md` sin MCP ni Supabase, con la ejecución agéntica enlazada.
- [ ] Cierre documental (`CONS-02`); en HALLAZGOS, "el skill `andesscale-saas` sigue diciendo
      Supabase (no editable por el agente)" si corresponde.
