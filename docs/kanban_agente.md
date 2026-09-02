# KANBAN AGÉNTICO — Piloto AI-DLC AndesScale SaaS

> **Qué es este archivo:** tablero operativo para el flujo de desarrollo autónomo desatendido (AI-DLC).
> Generado 2026-08-22 según `docs/prompt_agentes.md`, a partir del estado real del código y de
> `Documentacion/KANBAN_PROYECTO.md` (que sigue siendo la **fuente única de verdad del producto** —
> este archivo no lo reemplaza: toma sus cards pendientes ejecutables sin intervención humana y las
> descompone en Atomic Bolts consumibles por el Agente Planificador).
>
> **WIP máximo: 1 tarea activa a la vez.** Nada se da por hecho sin pasar los gates de §0.2.
> **Regla de commit:** un commit por card, mensaje con el ID, este archivo actualizado en el mismo commit.

---

## 🔄 SYNC 2026-09-01 — ronda 2 arranca aquí

**Hallazgo al retomar la sesión:** este archivo (y esta rama) llevaban desde el 2026-08-23 sin
saber que `agent/ai-dlc-pilot` **ya se había mergeado a `develop`** (commit `45eca7b`,
2026-08-24) y que `develop` había seguido avanzando 14 commits más — `#DEUDA-03`, `#DS-03`,
`#DEUDA-02` Fase 1, `#FLOW-01`/`#FLOW-02`, `#SEC-03`, todos cerrados con el mismo rigor TDD (ver
`Documentacion/KANBAN_PROYECTO.md`, "Retomar aquí"). §1/§2 de este archivo (`PILOT-01..03`,
`BOLT-01..09`) siguen siendo el registro histórico correcto de lo que este piloto entregó; no se
reescriben.

**Acciones de esta sesión (sync, no una card — sin test posible, es alineación de rama/entorno):**
- `git merge --ff-only origin/develop` en esta rama y worktree — sin conflictos (el piloto nunca
  tuvo commits propios divergentes de `develop`, la relación siempre fue de ancestro directo).
  Pusheado a `origin/agent/ai-dlc-pilot`.
- Gate re-verificado tras el sync: **198 tests OK, 5 skips, ruff limpio, migraciones limpias.**
- Venv dedicado del worktree creado (ver §0.-1) — antes no existía, el gate corría contra el venv
  del checkout principal.
- `Documentacion/KANBAN_PROYECTO.md`: corregida la nota stale "`#MED-04`/`#MED-05`... sin mergear"
  (ya estaban mergeados desde el 24).
- §0.0 (estructura del repo) actualizada abajo contra el estado real post-merge (temas movidos a
  `templates/themes/`, pool de galería en `apps/website/models.py`).
- **Hallazgo nuevo, va a §2 como `BOLT-10`:** `CLAUDE.md`/`SKILL.md` citan `THEME_CHOICES` como
  `'themes/default'`, `'servelec'`, `'ranchocachimba'` — desactualizado desde `#DEUDA-03`
  (2026-08-24): el valor real en `apps/tenants/models.py` hoy es solo `[('themes/default', ...),
  ('themes/servelec', ...)]` (RC no está mergeado a `develop`, `servelec` se unificó bajo
  `themes/`). Nadie lo tocó porque `#DEUDA-03` no pasó por `CLAUDE.md`/`SKILL.md`.

---

## §0 · PRECONDICIONES DE EJECUCIÓN (leer antes de tomar cualquier card)

### 0.-1 Rama y entorno de ejecución de este piloto (desde PILOT-01, 2026-08-22)

Todo el trabajo de este kanban corre en una rama y un worktree dedicados, **separados** de
`feature/RanchocachimbaEtapa1` (que tiene trabajo del usuario sin commitear y está en pausa —
`#0.4`) y del checkout principal del repo:

- **Rama:** `agent/ai-dlc-pilot`, creada desde `develop` (el kanban maestro usa `develop` como rama
  de integración para trabajo de plataforma no relacionado con Rancho Cachimba).
- **Worktree:** `C:\Users\sanch\Documents\Proyectos\SaaSMVP-agentic-pilot` (sibling del checkout
  principal, creado con `git worktree add`). Cualquier corrida futura del planificador/dev/validador
  debe operar ahí, no en el checkout principal — así el trabajo desatendido nunca pisa cambios sin
  commitear del usuario en otra rama.
- **`.env` local del worktree (gitignorado, no compartido con el checkout principal):** cada
  worktree tiene su propio directorio de trabajo, y `.env` está en `.gitignore` — no se copia solo
  con `git worktree add`. Se creó un `.env` mínimo *sin secretos reales* con `SECRET_KEY` dummy y
  `MP_PUBLIC_KEY`/`MP_ACCESS_TOKEN`/`MP_WEBHOOK_SECRET` dummy (estos 3 tienen `default=''` en
  `config/settings/base.py`, pero un valor vacío hace que `MercadoPagoService` registre error y
  2 tests de checkout devuelvan 400 en vez de 200 — no es un bug de código, es un artefacto de este
  `.env` minimalista). Si el worktree se recrea, hay que recrear este `.env` con los mismos 4 valores
  dummy antes de correr el gatekeeper.
- **Nota de shell:** en esta sesión, el `cwd` del tool de Bash **se resetea al directorio del checkout
  principal entre llamadas** (no persiste `cd` de una llamada a la siguiente, a diferencia de lo que
  suele asumirse). Cada comando dirigido al worktree necesita su propio `cd
  "C:\Users\sanch\Documents\Proyectos\SaaSMVP-agentic-pilot" &&` al principio.
- **Entorno virtual del worktree (creado 2026-09-01):** `env/` (gitignorado, patrón `ENV/`/`env` en
  `.gitignore`) — venv dedicado con `requirements.txt` + `requirements-dev.txt` instalados. Antes se
  corría el gatekeeper contra el venv del checkout principal (`../SaaSMVP/env`), lo cual violaba el
  aislamiento que este documento pide en otros puntos. Invocar `./env/Scripts/python.exe
  scripts/gatekeeper.py` (Windows) — no asumir que `python`/`pip` del PATH global tienen Django
  instalado. Si el worktree se recrea, recrear también este venv (`python -m venv env && ./env/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt`) antes de correr el gatekeeper.

### 0.0 Estructura real del repo (re-verificada 2026-09-01 tras el sync con `develop` — NO usar `docs/Structure.md`, está desactualizado)

**Cambios reales desde la última verificación (2026-08-22), por `#DEUDA-03`/`#DEUDA-02` Fase 1 en
`develop`:** `templates/servelec/` se movió a `templates/themes/servelec/` (unificación de temas,
`THEME_CHOICES` de `Client` ahora es solo `[('themes/default', ...), ('themes/servelec', ...)]`);
`GalleryItem.gallery_type` fue reemplazado por FKs `section`/`service` (`apps/website/models.py`).
Ver `BOLT-10` en §2 para el hallazgo de docs desactualizadas que esto dejó.

```
apps/
├── accounts/      # UserProfile (signal post_save), decorators.py (tenant_member_required)
├── core/          # rate_limit.py, cloudinary_utils.py, template_resolver.py, EmailOutbox
│   └── tests/     # paquete: test_*.py
├── orders/        # models.py (Plan:30, Order, PaymentLog), views.py, urls.py, urls_onboarding.py,
│   │              # views_onboarding.py, services/ (mercadopago_service, email_service, order_processor)
│   └── tests/     # paquete: test_*.py
├── website/       # views.py (dashboard), auth_views.py (client_login), forms.py
│   └── tests/     # paquete: test_*.py
├── tenants/       # middleware.py, managers.py, template_loader.py, models.py (Client, Domain,
│   │              # ClientSettings), management/commands/ (provision_tenant, check_tenant_setup, …)
│   │              # SIN paquete tests/: archivos planos tests.py, tests_isolation.py, tests_branding_form.py
├── marketing/     # SEOConfig, templatetags/seo_tags
config/settings/   # __init__ (DJANGO_ENVIRONMENT) → base / development / production / e2e / security_headers
scripts/           # PLANO, sin __init__.py (test_multi_tenant.py, seed_fernando.py, …) + output/ (gitignorado)
templates/         # global + components/ + emails/ + temas: andesscale/, servelec/, ranchocachimba/, themes/default/
.claude/skills/andesscale-saas/SKILL.md   # skill de dominio existente
docs/              # design-system.md, CLOUDINARY.md, prompt_agentes.md, este archivo
Documentacion/     # KANBAN_PROYECTO.md (fuente de verdad del producto)
```

**Convención de tests a respetar por cualquier bolt:** en `core`/`orders`/`website` los tests van
dentro del paquete `tests/` (`test_<tema>.py`); en `tenants` van como archivo plano `tests_<tema>.py`
en la raíz de la app. No crear el patrón contrario en ninguna de las dos.

### 0.1 Variables de entorno — política "cero preguntas manuales"

El flujo desatendido **no debe detenerse a preguntar por secretos**. Regla dura:

| Contexto | Variables requeridas | Estado |
|---|---|---|
| Suite de tests (`python manage.py test apps`) | **Ninguna** — `config.settings` cae en `development` por defecto; DB efímera de Django | ✅ Siempre ejecutable |
| Lint (`python -m ruff check`) / `makemigrations --check` | **Ninguna** | ✅ Siempre ejecutable |
| Smoke E2E (`npx playwright test`) | **Ninguna** — usa `config.settings.e2e`, SQLite descartable, puerto 8811, dominios `*.localhost` | ✅ Siempre ejecutable |
| `check --deploy --settings=config.settings.production` | `SECRET_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (el módulo **falla al importar** sin ellas — intencional, `#AUD-07`/`#AUD-12`). Los tests que las necesitan (`test_production_settings.py`) ya las inyectan vía subprocess con valores de prueba | ⚠️ Solo si el runner las define; si faltan, **omitir el check y registrarlo**, no preguntar |
| Sandbox real de MercadoPago | `MP_ACCESS_TOKEN`, `MP_PUBLIC_KEY`, `MP_WEBHOOK_SECRET` de test | ⛔ No disponible — todo lo que lo requiera va a §3 (bloqueadas), nunca a un bolt |
| Base de producción (Neon), Render dashboard, DNS/Zoho | Credenciales del usuario | ⛔ Ídem §3 |

**Consecuencia de diseño:** todos los bolts de §2 tienen `Variables requeridas: ninguna`. Una tarea que
descubra a mitad de ejecución que necesita un secreto **se detiene, se marca `BLOCKED` con diagnóstico
y pasa a §3** — no se improvisa un valor ni se le pregunta al usuario en medio del turno.

### 0.2 Verdad absoluta (gates — idénticos a §2.2 del kanban maestro)

```bash
python -m ruff check apps/ config/          # 0 errores NUEVOS (hay ~135 preexistentes fuera de alcance, #AUD-10 — no tocar sin pedido explícito)
python manage.py test apps -v 1             # 0 fallos (≈103 tests al 2026-08-22, 1 skip documentado)
python manage.py makemigrations --check --dry-run   # sin migraciones pendientes
```

Cobertura mínima (con `coverage`, `requirements-dev.txt`): `apps/orders/` ≥ 80 %,
`apps/tenants/middleware.py`+`managers.py` ≥ 90 %, código nuevo ≥ 70 %. Nunca baja.

### 0.3 Bucle de reparación (por card)

```
SPEC → test en ROJO confirmado → CODE mínimo → VERIFY (gates §0.2) →
REPAIR (máx. 3 reintentos; al 4º fallo: detenerse y reportar bloqueo con diagnóstico) →
CLOSE (actualizar card aquí + commit único con ID)
```

### 0.4 Restricciones heredadas que el agente NO puede violar

- **No tocar nada de Rancho Cachimba** (`#RC-*`, branch `feature/RanchocachimbaEtapa1` en pausa por decisión del usuario).
- **No limpiar el lint global preexistente** (~135 errores, deuda `#AUD-10` explícitamente reservada al usuario).
- **No eliminar** `apps/accounts/views.py::login_view`/`logout_view` (código muerto conocido, decisión de limpieza reservada al usuario — ver `#DEUDA-05`).
- Vistas nuevas: filtrado explícito `client=request.client` (no existe auto-filtro, `#MED-02`) + `tenant_member_required` en dashboard (`#AUD-03`).
- Emails dentro de `transaction.atomic()` → siempre `transaction.on_commit(...)` (`#AUD-06`).
- `apps/orders/urls.py`: el patrón `<slug:plan_slug>/` va **al final** (`#AUD-01`).
- Gotchas completos en `CLAUDE.md` y skill `andesscale-saas`.

---

## §1 · INFRAESTRUCTURA DEL PILOTO AGÉNTICO (Prioridad Inmediata)

### ✅ [PILOT-01] Skill de Gatekeeper & Test Runner determinista — **DONE (2026-08-22)**
- **Componente:** DevOps
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `scripts/gatekeeper.py` (nuevo — `scripts/` es plano y sin `__init__.py`, ver §0.0; se desvía a propósito del `scripts/skills/` que pedía `prompt_agentes.md` para no introducir un paquete donde el repo usa scripts standalone), `apps/core/tests/test_gatekeeper.py` (nuevo, 4 tests)
- **Contexto:** los gates de §0.2 hoy se corren a mano, comando por comando, y su salida es texto libre. El orquestador (PILOT-03) necesita un veredicto parseable y determinista.
- **Resultado:** `python scripts/gatekeeper.py` corre en secuencia `ruff check` (solo sobre archivos del diff vs `HEAD` + no trackeados que existen en disco — respeta la deuda preexistente de §0.4/`#AUD-10`), `manage.py test apps -v 1`, `manage.py makemigrations --check --dry-run`, y emite un único JSON a stdout: `{"passed": bool, "gates": {"ruff": {...}, "tests": {"total", "failures", "skipped"}, "migrations": {...}}, "duration_s": N}`. Exit 0 ⇔ `passed: true`.
- **⚠️ Incidente encontrado y corregido durante la implementación (bomba de fork real):** la primera versión colgó el gate de tests indefinidamente. Causa raíz: `apps/core/tests/test_gatekeeper.py` vive dentro de `apps` (lo que el propio gate ejecuta vía `manage.py test apps`) y sus tests invocan `scripts/gatekeeper.py` como subproceso para probarlo — recursión sin límite: gatekeeper → `manage.py test apps` → descubre `test_gatekeeper.py` → vuelve a invocar gatekeeper → ... **Confirmado en vivo: +150 procesos `python.exe` en ~3 minutos** antes de diagnosticarlo; requirió `Stop-Process -Force` repetido para limpiar el sistema. Fix: `gatekeeper.py` propaga `GATEKEEPER_TEST_RUN=1` al entorno del subproceso `manage.py test`; `test_gatekeeper.py` se salta a sí mismo (`@unittest.skipIf`) cuando ve esa env var — así solo corre cuando un desarrollador lo invoca directamente (`manage.py test apps.core.tests.test_gatekeeper`), acotando la recursión a profundidad 1. Segundo hallazgo menor en el mismo incidente: `subprocess.run()` sin `stdin=subprocess.DEVNULL` se cuelga en Windows cuando un `python.exe` lanza otro `python.exe` (el mismo comando corrido a mano en la shell termina en ~10s; vía `subprocess.run()` sin ese flag nunca retorna) — corregido en la función `_run()` común.
- **Definición de Terminado (DoD Verificable):**
  - [x] Test (`apps/core/tests/test_gatekeeper.py`, 4 tests) escrito que exprese el contrato JSON (Red → Green confirmado: 4/4 fallaban con `FileNotFoundError` antes de crear el script — ver incidente arriba para el rojo real encontrado ya con el script existiendo). Repo sano → `passed: true` exit 0 (verificado, `duration_s: 10.33`, 107 tests total incluyendo los 4 nuevos, 5 skips = 1 original + 4 por la guarda anti-recursión). Con un test roto inyectado dinámicamente en `apps/core/tests/` (`GatekeeperBrokenTestTestCase`, escribe y borra el archivo en `setUp`/`addCleanup`) → `passed: false`, exit ≠ 0, fallo contado.
  - [x] Implementación mínima que pasa la suite completa: `manage.py test apps.core.tests.test_gatekeeper -v 2` → 4/4 OK en 42s (cada test invoca una corrida anidada completa de la suite, acotada por la guarda — no recursiva).
  - [x] Cero errores en Linter: `ruff check apps/core/tests/test_gatekeeper.py scripts/gatekeeper.py` → "All checks passed!".
  - [x] Sin side-effects fuera del alcance de la tarjeta: no modifica settings, no escribe fuera de stdout; `makemigrations --check --dry-run` limpio. Verificado 2 veces que no queda ningún proceso `python.exe` huérfano tras correr el gate completo ni tras correr la suite de tests del propio gatekeeper.

### ✅ [PILOT-02] Prompts de trabajo por rol — **DONE (2026-08-22)**
- **Componente:** DevOps
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `.claude/workflows/01_planificador.md`, `.claude/workflows/02_dev_tester.md`, `.claude/workflows/03_validador.md` (nuevos); `.claude/skills/andesscale-saas/SKILL.md` (traído a esta rama — ver hallazgo abajo)
- **Contexto:** ya existe `.claude/skills/andesscale-saas/SKILL.md` con el conocimiento de dominio (templates multi-tenant, filtrado, provisioning) — los workflows lo referencian, no lo duplican.
- **⚠️ Hallazgo incidental (bloqueaba el DoD — corregido acá):** `.claude/skills/andesscale-saas/SKILL.md` (que la card asumía "ya existe" citando el kanban maestro) **nunca se había commiteado en ninguna rama** — solo vivía sin trackear en el checkout principal (`?? .claude/` en `git status`, confirmado con `git ls-files`/`git ls-tree` en todas las ramas). El propio kanban maestro (`#DEUDA-05`) lo registra como entregado, pero el `git add`/commit real nunca ocurrió. Como esta card exige que los workflows referencien el skill "por ruta exacta, verificado que existe", y `agent/ai-dlc-pilot` (creada desde `develop`) no lo tenía, se copió el archivo a esta rama y se commiteó acá — sin eso, el DoD de `PILOT-02` era imposible de cumplir literalmente. **No se tocó** el estado de ese archivo en el checkout principal ni en `feature/RanchocachimbaEtapa1`; es una corrección de alcance acotado a esta rama. Queda como hallazgo para el usuario: el kanban maestro puede necesitar reabrir `#DEUDA-05` o al menos anotar que ese commit nunca se hizo.
- **Segundo hallazgo, mismo origen:** el propio `SKILL.md` citaba `Documentacion/Procedimiento_Nuevo_Tenant.md`, que tampoco existe en `develop` (solo en `feature/RanchocachimbaEtapa1`/`feature/mejorar-provisioning-tenant`) y además está desactualizado — sigue documentando el management command `test_isolation`, eliminado en `#MED-02`. Se quitó esa cita puntual de la copia del skill en esta rama (con una nota explicando por qué) en vez de arrastrar un documento stale fuera de alcance.
- **Resultado:**
  - `01_planificador.md`: lee `docs/kanban_agente.md` completo, respeta WIP=1 (si ya hay una card `DOING` la retoma, si no toma la primera `TODO` elegible filtrando por §0.4/§3), marca `DOING`, produce el spec del test sin tocar código de producción.
  - `02_dev_tester.md`: ejecuta SPEC→CODE→VERIFY→REPAIR (§0.3), prohíbe cerrar sin rojo confirmado, invoca `python scripts/gatekeeper.py` (PILOT-01) y adjunta su JSON completo al handoff; tope de 3 reintentos explícito.
  - `03_validador.md`: verifica el DoD checkbox por checkbox contra el JSON del gatekeeper + `ARCHIVOS_TOCADOS`, veredicto `APPROVE`/`REJECT`; en `APPROVE` marca `DONE` en este kanban, agrega fila a §4 y commitea (documenta la autorización explícita del usuario del 2026-08-22 para commitear sin volver a preguntar, acotada a esta rama).
  - Los tres declaran la política de §0.1 (secreto faltante → `BLOCKED` + §3, nunca preguntar) y citan `docs/kanban_agente.md` §0.-1 para el entorno de ejecución (worktree, `.env` dummy).
- **Definición de Terminado (DoD Verificable):**
  - [x] Los 3 archivos existen y cada uno define: rol, entrada esperada, salida obligatoria (formato), condición de traspaso al siguiente rol y condición de aborto — el límite de 3 reintentos vive en `02_dev_tester.md` (dueño real del bucle REPAIR), citado explícitamente ahí.
  - [x] Referencian gatekeeper (PILOT-01, `scripts/gatekeeper.py`), este kanban (`docs/kanban_agente.md`) y el skill `andesscale-saas` (`.claude/skills/andesscale-saas/SKILL.md`) por ruta exacta — verificado con un chequeo de existencia sobre las 17 rutas citadas entre los 3 workflows y el skill; 1 ruta colgante encontrada y corregida (ver hallazgos arriba).
  - [x] Cero errores en Linter: no aplica a `.md`; en su lugar se corrió `python scripts/gatekeeper.py` (`ruff`/tests/migraciones) tras los cambios → `passed: true`, 107 tests OK (5 skip), `files_checked: 0` en ruff (correcto: esta card no tocó ningún `.py`).
  - [x] Sin side-effects fuera del alcance de la tarjeta — verificado 0 procesos `python.exe` huérfanos tras la corrida del gate.

### ✅ [PILOT-03] Script orquestador con manejo de turnos — **DONE (2026-08-22)**
- **Componente:** DevOps
- **Variables requeridas:** ninguna (el runner del agente provee su propia autenticación; el script no maneja API keys en código)
- **Archivos Afectados:** `orchestrate.py` (raíz, nuevo), `apps/core/tests/test_orchestrate.py` (nuevo, 5 tests)
- **Contexto:** depende de PILOT-01 (gate parseable) y PILOT-02 (roles). Cierra el circuito planificador → dev → validador.
- **Decisión de diseño (aclarada durante la implementación, no estaba explícita en el spec original):** `orchestrate.py` implementa **solo la máquina de estados** — secuenciar turnos, contar reintentos, decidir `DONE`/`BLOCKED`/`REJECTED` — a través de un protocolo `AgentRunner` con 3 métodos (`run_planificador`/`run_dev_tester`/`run_validador`). **No invoca ningún agente real ni maneja credenciales**: conectar un agente real (CLI de Claude Code en modo no interactivo con los prompts de `.claude/workflows/`, o la API de Anthropic) es un paso de integración aparte, deliberadamente fuera de esta card — coincide con el propio DoD original ("agentes stub") y con la nota de "el script no maneja API keys en código". El runner por defecto (`NotWiredAgentRunner`) levanta `NotImplementedError` explícito en vez de fallar en silencio o simular un resultado falso.
- **Resultado:** `python orchestrate.py [--max-cards N] [--dry-run]`. El bucle real: planificador → (dev_tester × hasta 3, corta en el primer `passed: true`) → si nunca pasó, `BLOCKED` sin correr validador; si pasó, validador → `DONE`/`REJECTED` según el veredicto. Log JSONL por turno en `scripts/output/orchestrator_{timestamp}.jsonl` (carpeta ya gitignorada). `--dry-run` usa `DryRunAgentRunner` (un card simulado, sin agente real, sin costo) — probado a mano: `DRY-RUN-CARD: DONE (intentos=1)`, exit 0, log JSONL de 4 líneas verificado.
- **Definición de Terminado (DoD Verificable):**
  - [x] Test de la máquina de estados escrito (Red → Green, rojo confirmado: `ModuleNotFoundError: No module named 'orchestrate'` antes de crear el script) con `ScriptedRunner` (stub): happy path (1 card → `DONE`, 1 intento) ✅; reintento (2 fallos + 1 éxito → `DONE` con `attempts: 3`, `dev_tester_calls == 3`) ✅; agotamiento (dev_tester siempre falla → `BLOCKED`, `attempts == MAX_REPAIR_ATTEMPTS == 3`, **nunca un 4º intento**, `validador_calls == 0`) ✅. Se agregaron 2 tests más allá del DoD mínimo (cola vacía sin efectos; `--max-cards` corta el loop) por ser casos borde directos de la misma máquina de estados, sin costo adicional de alcance.
  - [x] Implementación mínima que pasa la suite completa: `apps.core.tests.test_orchestrate` → 5/5 OK. Gate completo (`scripts/gatekeeper.py`): 112 tests OK (5 skip, +5 de esta card sobre los 107 de PILOT-02).
  - [x] Cero errores en Linter: `ruff check` (vía gatekeeper, alcance = archivos tocados) → `files_checked: 2, errors: 0`.
  - [x] Sin side-effects fuera del alcance de la tarjeta: `--dry-run` verificado a mano — único archivo nuevo en `git status` tras correrlo es el JSONL en `scripts/output/`, confirmado gitignorado (`git check-ignore -v`). El script no ejecuta `git commit` en ningún punto (esa responsabilidad vive en la implementación real de `run_validador`, fuera de este script). 0 procesos `python.exe` huérfanos tras la corrida.

---

## §2 · ATOMIC BOLTS DE PRODUCTO (Backlog de Corto Plazo)

> Seleccionados del kanban maestro por ser 100 % ejecutables desde el repo (sin secretos, sin insumos
> del cliente, sin dashboards externos), de bajo acoplamiento entre sí y de 15–45 min cada uno.
> Orden sugerido: BOLT-01 primero (asegura terreno firme); el resto es independiente.
>
> **BOLT-06..08 (agregados 2026-08-24):** derivan del análisis de diseño del hero de Rancho Cachimba
> (`#RC-20` del maestro; spec detallada en `Documentacion/Planificación/spec_bolt_hero_cachimba.md`,
> **en `feature/RanchocachimbaEtapa1` — no visible desde esta branch**, el contexto necesario está
> copiado en cada card). Son la parte *de plataforma / system design* de ese análisis: mejoran a todos
> los tenants y tocan solo código que existe en esta branch. La maquetación Rancho-específica quedó
> fuera del piloto (§0.4 intacta, ver §3). La generalización de `stats.html` a componente compartido
> se excluyó a propósito: solo 2 temas lo tienen y con layouts distintos — forzarla sería el
> anti-patrón del "flag de más" que `docs/design-system.md` §2b prohíbe.

### ✅ [BOLT-01] Confirmar suite en verde tras el retiro de `apps/core/managers.py` — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Backend
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/core/managers.py` (eliminado — ver hallazgo), `Documentacion/KANBAN_PROYECTO.md`, este archivo
- **Contexto:** `#DEUDA-05` eliminó la copia muerta de `TenantAwareManager` en `apps/core/managers.py`, pero esa sesión **no pudo correr la suite completa** (bloqueada por el runner). El import en frío funcionó; falta la confirmación formal. Es el único cabo suelto verificable desde el repo que quedó abierto.
- **⚠️ Hallazgo incidental (bloqueaba el sentido de la card — corregido acá):** el retiro que la card daba por hecho **nunca llegó a esta rama**: el commit que borraba el archivo (`d3bb7ba`, `DEUDA-05: reconcilia README...`) vive solo en `feature/RanchocachimbaEtapa1`, no en `develop` (base de `agent/ai-dlc-pilot`) — mismo patrón que el hallazgo del `SKILL.md` en PILOT-02. Se completó el retiro aquí (`git rm`), previa verificación de que es código muerto: 0 imports de `apps.core.managers` en `apps/`/`config/`; todo el uso real de `TenantAwareManager` importa de `apps/tenants/managers.py`. Al mergear ambas ramas el borrado converge sin conflicto.
- **Definición de Terminado (DoD Verificable):**
  - [x] Suite completa en verde tras el retiro, vía gatekeeper: **112 tests, 0 fallos, 5 skips** (`duration_s: 10.27`). Sin test nuevo por diseño de la card ("la suite entera ES el test").
  - [x] `ruff` sin errores nuevos (gate en verde) y `makemigrations --check --dry-run` limpio.
  - [x] Nota de cierre registrada en `KANBAN_PROYECTO.md` (§"Retomar aquí" con fecha 2026-08-23 y card `#DEUDA-05`), incluyendo el hallazgo del commit `d3bb7ba` no mergeado.
  - [x] Sin side-effects fuera del alcance: únicos archivos tocados = el retiro + los 2 kanbans; 0 procesos huérfanos.

### ✅ [BOLT-02] Slugs reservados en `Plan` — cierre del DoD de `#AUD-01` — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Backend
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/orders/models.py` (`RESERVED_PLAN_SLUGS` + `Plan.clean()` + `Plan.save()`), `apps/orders/tests/test_models.py` (+3 tests, `PlanReservedSlugTestCase`)
- **Contexto:** cabo suelto explícito del kanban maestro (§7, `#AUD-01`, checkbox abierto): un `Plan` con slug `process`, `success` o `error` queda inalcanzable en silencio — `apps/orders/urls.py` resuelve esas rutas literales antes que `<slug:plan_slug>/`.
- **Resultado:** `Plan.clean()` rechaza `{'process', 'success', 'error'}` con `ValidationError` en el campo `slug` que nombra el conflicto de ruta. **Decisión de diseño:** `Plan.save()` llama `full_clean()` — ningún otro modelo del repo lo hace (verificado por grep), pero la card lo contemplaba explícitamente y sin eso la guardia no cubre creación programática (shell/scripts); desviación documentada en comentario en el código. Sin migración: la validación vive en `clean()`, no en `validators=` del campo. Los tests existentes que crean `Plan` mínimos (`name`/`slug`/`price`) pasan `full_clean()` sin cambios (todos los demás campos tienen default o `blank=True`).
- **Definición de Terminado (DoD Verificable):**
  - [x] Test Red → Green: rojo confirmado con 4 fallos `ValidationError not raised` (3 slugs reservados vía `full_clean()` en subTests + guardia en `save()`); slug normal en verde desde el rojo. Verde tras implementar.
  - [x] Implementación mínima que pasa la suite completa: gatekeeper 115 tests OK (5 skip, +3 de esta card).
  - [x] Cero errores en Linter: `ruff` en verde al 3er intento (REPAIR ×2 por `I001` — bloque de imports preexistente desordenado que se activó al tocar el archivo; resuelto con `ruff --fix`, solo reordena imports).
  - [x] Sin side-effects: `makemigrations --check` limpio (sin migración, esperado); planes con slugs válidos intactos.

### ✅ [BOLT-03] `#MED-05` (a) — IP confiable detrás del proxy de Render — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Backend
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/core/rate_limit.py` (`get_client_ip()` canónica; `RateLimiter._get_ip` eliminado — delegaba la 3ª copia de la lógica), `apps/orders/views.py`, `apps/website/views.py` (copias reemplazadas por import), `apps/core/tests/test_client_ip.py` (nuevo, 8 tests)
- **Contexto:** hallazgo de auditoría (§1.2 del maestro): `get_client_ip()` confía en `X-Forwarded-For` completo → el rate-limit se evade spoofeando el header. La card citaba 2 copias; el planificador encontró una **3ª** en `RateLimiter._get_ip` (misma lógica vulnerable, ya listada en archivos afectados).
- **Resultado:** `apps.core.rate_limit.get_client_ip(request)` toma el valor a `TRUSTED_PROXY_COUNT` posiciones desde la derecha del XFF (setting con default 1 = último valor, el que escribe Render), cae a `REMOTE_ADDR` sin header, trunca a 45 chars, sin IPs hardcodeadas. Las 3 copias consumen la canónica (2 por import directo, `RateLimiter` por llamada interna); tests de identidad (`assertIs`) impiden que una copia local reaparezca en silencio.
- **⚠️ Hallazgo incidental:** `F841` preexistente en `apps/website/views.py:821` (`tab = gallery_type`, asignación muerta) — el gate lintéa completo el archivo tocado; eliminada la línea (verificado que `gallery_type` se usa directo después). No es limpieza de lint global (#AUD-10): solo lo que el gate exige sobre archivos del diff.
- **Definición de Terminado (DoD Verificable):**
  - [x] Test Red → Green: rojo estructural (ImportError, la canónica no existía) + rojo conductual demostrado en vivo (XFF `"1.2.3.4, 5.6.7.8"` → la copia de website devolvía `1.2.3.4`, el valor spoofeado). Verde: cadena larga spoofeada resuelve el último salto; sin XFF → `REMOTE_ADDR`; `TRUSTED_PROXY_COUNT=2` → penúltimo; ambos consumidores usan la canónica (`assertIs`) y la key del `RateLimiter` lleva la IP del último salto.
  - [x] Implementación mínima que pasa la suite completa: gatekeeper 123 tests OK (5 skip, +8 de esta card).
  - [x] Cero errores en Linter: ruff en verde, 4 archivos chequeados (intentos: 2 — F841 preexistente arriba).
  - [x] Sin side-effects: rate limit de contacto sigue verde en la suite completa; `makemigrations --check` limpio.

### ✅ [BOLT-04] `#MED-05` (b) — Rate limit en login y checkout — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Auth
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/website/auth_views.py`, `apps/orders/views.py`, `apps/core/rate_limit.py` (param `key_extra` nuevo), `apps/website/tests/test_login_rate_limit.py` (7 tests) y `apps/orders/tests/test_checkout_rate_limit.py` (3 tests, nuevos)
- **Contexto:** segunda mitad de `#MED-05`; depende de BOLT-03 (cerrada). `RateLimiter` existente extendido, no reescrito.
- **Resultado:** login: `scope='login'`, 5 intentos fallidos / 5 min por IP+hash(username)+tenant (`RATE_LIMIT_LOGIN_LIMIT/PERIOD` vía `getattr` con defaults); **solo los fallos consumen cupo** (login legítimo bajo umbral intacto) y alcanzado el límite ni la contraseña correcta entra (si entrara, el 429 confirmaría credenciales). El 429 re-renderiza el form con el MISMO texto genérico de credenciales inválidas (constante compartida `LOGIN_GENERIC_ERROR`), sin mencionar límites. Checkout: `scope='checkout'`, 10/10 min por IP+tenant (`RATE_LIMIT_CHECKOUT_LIMIT/PERIOD`), **todo** intento cuenta (card testing no manda payloads válidos), JSON 429 `code: RATE_LIMITED`.
- **Definición de Terminado (DoD Verificable):**
  - [x] Test Red → Green: login `200/302 != 429` confirmado; checkout `400 != 429` confirmado (tras corregir el arnés: el POST necesita `HTTP_HOST='localhost'` como en `test_emails` — el 404 inicial era del middleware, no un rojo válido); login legítimo bajo umbral → 302; contador no cruza IPs, usernames ni tenants (tests dedicados).
  - [x] Implementación mínima que pasa la suite completa: gatekeeper 133 tests OK (5 skip, +10 de esta card).
  - [x] Cero errores en Linter: ruff en verde, 5 archivos chequeados (intentos: 1).
  - [x] Sin side-effects: matriz `#AUD-03` (`test_login_tenant_authorization`) y aislamiento `#MED-02` (`tests_isolation`) verdes dentro de la suite completa; `makemigrations --check` limpio.

### ✅ [BOLT-05] `#FLOW-02` — `check_tenant_setup` como gate de calidad ampliado — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Multi-tenant
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/tenants/management/commands/check_tenant_setup.py` (replicado + ampliado), `apps/tenants/tests_check_tenant_setup.py` (nuevo plano, 10 tests)
- **⚠️ Hallazgo incidental (4º caso del mismo patrón):** la card asumía "el comando existe" — **no existía en esta rama**: vive solo en `feature/RanchocachimbaEtapa1` (`03f14e2`), nunca llegó a `develop` (como el `SKILL.md` de PILOT-02, el retiro de `managers.py` en BOLT-01 y `Procedimiento_Nuevo_Tenant.md`). Dependencias verificadas presentes acá (`primary_domain`, `email_settings`, `seo_configs`, `notify_mode`) → se replicó la versión commiteada base y se amplió; la branch en pausa no se tocó.
- **Resultado:** chequeos nuevos sobre la base: (1) `SEOConfig("home")` obligatorio con título/descripción no vacíos ni placeholder; (2) secciones activas sin marcadores de relleno — constante con `lorem`/`placeholder`/`xxx` case-insensitive con word-boundary y `TODO` **case-sensitive** (para no matchear "todo" en español, cubierto por test); (3) `ClientEmailSettings` presente cuando hay `FormConfig`, y `from_email` obligatorio si `notify_mode` envía emails. Con fallos → `CommandError` (exit ≠ 0) resumiendo cada `[FAIL]`; `--warn-only` conserva el modo informativo original. Sigue siendo 100 % lectura (test dedicado compara los datos antes/después).
- **Definición de Terminado (DoD Verificable):**
  - [x] Test Red → Green con `call_command`: contra la base replicada sin ampliar, 5× `CommandError not raised` (tenant incompleto pasaba en silencio) + `--warn-only` inexistente (`TypeError`). Verde: fallo por cada chequeo nuevo, tenant completo OK, sección inactiva con placeholder no falla.
  - [x] Implementación mínima que pasa la suite completa: gatekeeper 143 tests OK (5 skip, +10 de esta card).
  - [x] Cero errores en Linter: ruff en verde, 2 archivos (intentos: 1).
  - [x] Sin side-effects: comando solo lectura (verificado por test); `makemigrations --check` limpio.

### ✅ [BOLT-06] Guardia del contrato de tokens CSS (`docs/design-system.md` §1) — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** UI
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/core/tests/test_theme_token_contract.py` (nuevo, 3 tests) + **10 templates corregidos** (hallazgo incidental, ver abajo)
- **Contexto:** al auditar el hero de Cachimba contra su tema (feature branch) se encontraron 114 usos de `var(--primary|--secondary|--accent)` que ningún `:root` define. La clase de bug es general y silenciosa (CSS inválido no lanza error). Mismo patrón de test anti-regresión que `CLOUDINARY_PRESETS` en `#AUD-10` (estático, sin runtime).
- **Resultado:** el test recolecta las custom properties definidas en los `.html` de cada tema (`andesscale`, `servelec`, `themes/default`, `themes/electricidad`) y exige que todo `var(--x)` consumido **sin fallback** esté definido; `templates/components/` compartidos se validan contra la **intersección** de contratos. Decisiones de contrato documentadas en el test: `var(--x, fallback)` no es violación (comportamiento CSS definido — patrón legítimo de slots como `--hero-bg`); `--tw-*` whitelisteado. Rojo sintético con fixture en tmp dir (sin romper temas reales). Cuando la branch de Rancho se integre, atrapará sus 114 usos rotos automáticamente.
- **⚠️ Hallazgo incidental (previsto por la card):** la violación estaba vigente también en esta branch — `var(--primary|--secondary|--accent)` sin fallback en 10 archivos: navbar/footer de `servelec` y `themes/electricidad`, hero/hero_ctas/hero_overlay(_theme) de `themes/default`, y `components/slots/gallery_caption.html`+`hero_overlay.html`. Corregidos a `--color-*` (el fix RESTAURA el color de marca que el CSS inválido descartaba en silencio — los gradientes/botones afectados caían al valor heredado).
- **Definición de Terminado (DoD Verificable):**
  - [x] Test Red → Green: rojo sintético (el checker reporta exactamente `[('hero.html', '--primary')]` con fallback y `--tw-*` exentos) + rojo real (3 temas y components/ fallaban). Verde tras corregir los 10 archivos.
  - [x] Implementación mínima que pasa la suite completa: gatekeeper 146 tests OK (5 skip, +3 de esta card).
  - [x] Cero errores en Linter: ruff en verde (intentos: 1).
  - [x] Sin side-effects: los tests de rendering existentes de los temas siguen verdes; único "cambio visual" = el hallazgo incidental documentado.

### ✅ [BOLT-07] CTA del navbar compartido configurable por tenant — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Multi-tenant
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/tenants/models.py` (+migración `0023`), `templates/components/navbar_cta.html` (**nuevo** — única fuente del markup), `templates/components/navbar.html`, `templates/themes/default/components/navbar.html` y `templates/themes/electricidad/components/navbar.html` (includes de 1 línea), `apps/website/tests/test_navbar_cta.py` (4 tests)
- **⚠️ Hallazgo del piloto (premisa de la card incorrecta):** el `components/navbar.html` compartido está **shadowed**: `themes/default` y `themes/electricidad` tienen su propio `components/navbar.html` y el `TenantTemplateLoader` los resuelve primero — el "consumido por ambos temas, verificado por grep" vio los `{% include %}` de los `base.html`, no la resolución real del loader. El CTA implementado solo en el compartido no renderizaba nunca para esos temas (descubierto por el test en rojo tras la primera implementación).
- **Resultado:** `ClientSettings.navbar_cta_text` (max 60) y `navbar_cta_url` (CharField 255 — permite anclas `#contacto`), `blank=True` con default `''`. El markup del botón vive UNA sola vez en `components/navbar_cta.html` (parámetro `mode='mobile'`, mismo patrón que `media_collection`), incluido desde el navbar compartido y los dos overrides de tema (desktop + móvil en cada uno). Estilo con `var(--color-accent, var(--color-primary))` — compatible con la guardia de BOLT-06 (tokens en la intersección de contratos). Sin `navbar_cta_text` → cero cambios de HTML. `BrandingForm`: fuera de alcance, como pedía la card.
- **Definición de Terminado (DoD Verificable):**
  - [x] Test Red → Green: rojo estructural (`FieldError`, campos inexistentes) + rojo conductual clave (CTA en el compartido no renderizaba por el shadowing — llevó al diseño correcto). Verde: texto+href renderizados, `count=2` (desktop+móvil), tokens presentes junto al botón, tenant sin CTA sin botón nuevo.
  - [x] Implementación mínima + migración `0023` incluida; `makemigrations --check` limpio.
  - [x] Cero errores en Linter (intentos: 2 — el 1º falló por I001+3×F401 **preexistentes** en `apps/tenants/models.py`, activados al tocar el archivo; autofix de ruff, solo imports).
  - [x] Sin side-effects: navbars de `servelec`/`andesscale` intactos; suite completa en verde (150 tests).

### ✅ [BOLT-08] Generalizar `hero_ctas` a `templates/components/` (`design-system` §2a) — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** UI
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `templates/components/hero_ctas_base.html` (nuevo — única fuente del markup), `templates/servelec/components/hero_ctas.html` y `templates/themes/default/components/hero_ctas.html` (ahora wrappers de 1 `include` con parámetros), `apps/website/tests/test_hero_ctas_component.py` (nuevo, 5 tests)
- **Decisión de naming (desviación del literal de la card, justificada):** el compartido NO se llama `components/hero_ctas.html` como pedía la card — el `TenantTemplateLoader` resolvería ese nombre al wrapper del tema activo (`{tema}/components/hero_ctas.html`) y el include del wrapper **recursaría sobre sí mismo**. Es el mismo shadowing descubierto en BOLT-07; se usó `hero_ctas_base.html` (documentado en el propio template).
- **Resultado:** componente parametrizado imitando `media_collection`: `primary_text/href/style`, `secondary_text/href/style`; el secundario solo se renderiza si recibe texto (1 o 2 botones sin flags extra, §2b); defaults = tema default (tokens del contrato, compatibles con la guardia BOLT-06). Wrapper servelec preserva su verde de marca `#1DB954` y textos ('Solicitar cotización'/'Ver servicios'); wrapper default usa los defaults ('Contáctanos'/'Ver servicios'). HTML visible equivalente al anterior. Tema de Rancho: no existe en esta branch, no se adaptó (lo hará `#RC-20`).
- **Definición de Terminado (DoD Verificable):**
  - [x] Test Red → Green: rojo `TemplateDoesNotExist: components/hero_ctas_base.html` + wrappers con markup duplicado (fallo del test estático). Verde: CTAs actuales de ambos temas servidos desde el compartido (texto+href+estilo verificados), secundario omitido sin texto.
  - [x] `grep` confirma markup en un solo archivo: 2 `<svg>` en `hero_ctas_base.html`, 0 en ambos wrappers (además hay test estático permanente que lo vigila).
  - [x] Cero errores en Linter y suite completa en verde: gatekeeper 155 tests OK (5 skip, +5 de esta card), intentos: 1.
  - [x] Sin side-effects: HTML visible equivalente; guardia de tokens (BOLT-06) verde dentro de la suite.

### ✅ [BOLT-09] `#MED-04` (mitad automatizable) — Texto plano legible + link de soporte roto en emails — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Backend / Email
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/orders/services/email_service.py` (`_send_email`), `templates/emails/base_email.html`, `templates/emails/{payment_success,welcome,site_ready,token_expiring,set_password,contact_received}.txt` (6 nuevos), `apps/orders/tests/test_email_service.py` (+9 tests)
- **Contexto:** con `§2` agotado, se cumple la condición que la propia §3 dejó anotada para `#MED-04`: "la mitad automatizable puede promoverse a bolt cuando se agote §2". La mitad manual (probar en Gmail/Outlook móvil real) sigue bloqueada en §3, sin insumo del usuario.
- **⚠️ 2 hallazgos reales, verificados en vivo antes de tocar código (no hipotéticos):**
  1. `EmailService._send_email` generaba el texto plano con `strip_tags(html_content)`. `strip_tags` de Django no es consciente de `<style>`: deja el CSS completo de `base_email.html` (150+ líneas: `mso-table-lspace`, `-webkit-text-size-adjust`, etc.) como texto visible **al principio** de cada email de texto plano, antes de cualquier contenido real — confirmado renderizando `payment_success.html` directo con `manage.py shell`. Afectaba a los 6 emails que pasan por este servicio. El patrón correcto ya existía en el propio repo sin usarse acá: `apps/tenants/services/email_dispatcher.py` renderiza `.txt` dedicados para `contact_notification`/`contact_confirmation`.
  2. `templates/emails/base_email.html`: el link de soporte del footer (`¿Tienes dudas? Escríbenos a...`) apuntaba a `href="/cdn-cgi/l/email-protection#e59e9e..."` — un artefacto de ofuscación de Cloudflare que decodifica el email vía su JS del lado del navegador; ese JS nunca corre dentro de un cliente de correo, así que era un link muerto en el 100% de los casos, en los 6 templates que heredan el footer default (`payment_success`, `welcome`, `site_ready`, `token_expiring`, `set_password`, `contact_digest`).
- **Resultado:** `_send_email` ahora renderiza `emails/{template_name}.txt` (mismo patrón que `email_dispatcher.py`) en vez de `strip_tags`; se crearon los 6 `.txt` faltantes con el mismo estilo ASCII (`═══`/`───`) que ya usaban `contact_confirmation.txt`/`contact_notification.txt`. El link roto del footer pasa a `mailto:{{ support_email }}`. De paso, `base_email.html` suma `<meta name="color-scheme" content="light dark">` + `<meta name="supported-color-schemes" content="light dark">` (dark-mode friendly, trivial, sin romper nada existente — clientes que no lo soportan lo ignoran). El import de `strip_tags` se retiró de `email_service.py` (sin otro uso en el archivo).
- **Definición de Terminado (DoD Verificable):**
  - [x] Test Red → Green: rojo confirmado en vivo — 7 tests nuevos fallaron antes del fix (`mso-table-lspace`/`-webkit-text-size-adjust` presentes en `mail.outbox[-1].body` de los 6 emails; `cdn-cgi` presente en el HTML renderizado). Verde tras crear los `.txt` y cambiar `_send_email` + el link del footer.
  - [x] Implementación mínima que pasa la suite completa: gatekeeper 162 tests OK (5 skip, +9 de esta card sobre los 155 de BOLT-08 — 6 de texto plano limpio + 1 de link del footer, más 2 tests ya existentes que ahora ejercitan el nuevo camino).
  - [x] Cero errores en Linter: ruff en verde (intentos: 2 — 1º activó 4 hallazgos preexistentes en `email_service.py` al tocar el archivo — `I001`, 2×`F401`, `F541` — mismo patrón que BOLT-02/03/07; autofix de ruff, sin cambio de comportamiento).
  - [x] Sin side-effects fuera del alcance de la tarjeta: `makemigrations --check --dry-run` limpio; `contact_digest.html`/`contact_notification.html`/`contact_confirmation.html` no tocados (su flujo de texto plano ya era correcto); único cambio visual = el link del footer y los 2 meta tags nuevos.

### ✅ [BOLT-10] `CLAUDE.md`/`SKILL.md` — corregir cita de `THEME_CHOICES` desactualizada + guardia anti-drift — **DONE (2026-09-01)**
- **Estado:** ✅ DONE (2026-09-01)
- **Componente:** DevOps / Docs
- **Variables requeridas:** ninguna
- **Archivos esperados:** `CLAUDE.md` (línea ~47, ~52), `.claude/skills/andesscale-saas/SKILL.md`
  (línea ~25-26), test nuevo (sugerido: `apps/core/tests/test_docs_theme_choices.py` o ampliar
  `apps/tenants/tests_theme_consistency.py` si ya cubre algo similar — el Dev/Tester decide tras
  revisar ese archivo).
- **Contexto:** hallazgo de esta sesión (ver nota de SYNC arriba). `#DEUDA-03` (2026-08-24, `develop`)
  cambió `Client.THEME_CHOICES` a `[('themes/default', 'Tema Base...'), ('themes/servelec',
  'Electricidad (Servelec)')]` (movió `servelec` bajo `templates/themes/`, retiró el tema
  `'themes/industrial'` huérfano). Ni `CLAUDE.md` ni el skill de dominio se actualizaron: ambos
  siguen citando `THEME_CHOICES: 'themes/default', 'servelec', 'ranchocachimba'` — dos valores que
  ya no existen en el campo real (`'servelec'` sin el prefijo `themes/` nunca fue un valor válido
  del choices, era una referencia de carpeta antigua; `'ranchocachimba'` no está mergeado a
  `develop`). Cualquier agente/dev que confíe en esa cita para razonar sobre temas válidos en esta
  rama parte de un dato falso.
- **Spec del test (a escribir por Dev/Tester):** un test estático (mismo patrón que `BOLT-06`,
  `test_theme_token_contract.py`: leer el archivo fuente, no evaluar en runtime) que parsee
  `Client.THEME_CHOICES` desde `apps/tenants/models.py` y falle si `CLAUDE.md`/`SKILL.md` mencionan
  un valor de tema que no está en esa lista actual (o si falta alguno que sí está). Rojo esperado
  hoy: `'servelec'` y `'ranchocachimba'` aparecen citados sin estar en `THEME_CHOICES`.
- **Resultado:** `apps/core/tests/test_docs_theme_choices.py` (nuevo, 2 tests) lee `Client.THEME_CHOICES`
  en vivo (import real, no parsing de AST — a diferencia de `BOLT-06`, acá no hay riesgo de clave
  duplicada evaluada en runtime) y compara contra la cita literal `` `THEME_CHOICES`: `'v1'`,
  `'v2'`... `` extraída de `CLAUDE.md` y de `SKILL.md` con una regex — falla si un valor citado no
  está en el modelo real o si falta alguno. `CLAUDE.md` y `SKILL.md` corregidos a `'themes/default'`,
  `'themes/servelec'`; se agregó una nota aparte (fuera de la cita, así el regex de la guardia no
  la captura) aclarando que `'themes/ranchocachimba'` existe solo en `feature/RanchocachimbaEtapa1`.
  La lista de temas de "antes de escribir un componente nuevo" (línea ~52 de `CLAUDE.md`, ~31 del
  skill) también se corrigió por ser el mismo hallazgo, aunque no está cubierta por el test estático
  (es prosa libre, no una cita mecánica — cubrirla con regex sería frágil).
- **Definición de Terminado (DoD):**
  - [x] Test Red → Green: rojo confirmado (2/2 fallos exactos: `CLAUDE.md`/`SKILL.md` citaban
    `{'servelec', 'ranchocachimba'}` en vez de faltarles `'themes/servelec'` y sobrarles esos dos).
    Verde tras corregir ambos archivos.
  - [x] Gatekeeper en verde: 200 tests OK (5 skip, +2 de esta card), ruff limpio (1 archivo: el test
    nuevo), migraciones limpias. Intentos: 1.
  - [x] Sin tocar nada de Rancho Cachimba ni el contenido del resto de `CLAUDE.md`/`SKILL.md` fuera
    de la cita puntual de `THEME_CHOICES` — diff revisado línea por línea antes de aprobar (4
    líneas en `CLAUDE.md`, 10 en `SKILL.md`, ambas acotadas a los dos párrafos citados).

---

## §3 · BLOQUEADAS — requieren insumos externos (NO tomar, NO preguntar)

> Registro para que ningún agente las seleccione ni pregunte por ellas. Se desbloquean solo cuando el
> usuario provea el insumo indicado (columna derecha) y lo diga explícitamente.

| ID maestro | Tarea | Insumo faltante |
|---|---|---|
| `#AUD-04` (cabo) | Confirmar config activa en Render | Acceso al dashboard de Render |
| `#AUD-07`/`#PAY-03` (cabo) | SPF/DKIM Zoho + pasada manual sandbox MP | Panel Zoho/DNS + `MP_*` de test |
| `#SEC-02` (cabo) | CSP en `/checkout/` + securityheaders.com | Sandbox MP real + dominios deployados |
| `#MED-03` (cabo) | `EXPLAIN ANALYZE` contra datos reales | Acceso a la DB de producción (**Neon** — el maestro aún dice Supabase, corrección pospuesta por el usuario) |
| `#MED-01` (cabo) | Confirmar cron `*/5` en plan free de Render | Dashboard de Render |
| `#SEC-03` | Inventario de secretos + política de rotación | Lista real de env vars en Render (solo el usuario la ve) |
| `#MED-04` (mitad manual, resto **DONE** en `BOLT-09`) | Prueba visual en Gmail/Outlook móvil real | Casillas reales del usuario — la mitad automatizable (texto plano + link roto del footer) ya se cerró en `BOLT-09` |
| `#RC-*` completo | Todo Rancho Cachimba (incluida la maquetación del hero: `#RC-20` del maestro, cards `RC-BOLT-01..06` en `feature/RanchocachimbaEtapa1`) | **En pausa por decisión del usuario** — prohibido por §0.4. Las generalizaciones *de plataforma* derivadas de ese análisis de diseño sí son de este tablero: `BOLT-06..08` (§2) |
| `#DEUDA-05` (cabo) | Eliminar login muerto de `apps/accounts/` | Decisión explícita del usuario |
| `#DEUDA-05` (hallazgo nuevo, PILOT-02) | `.claude/skills/andesscale-saas/SKILL.md` nunca se commiteó en ninguna rama (solo vivía sin trackear en el checkout principal) — se copió a `agent/ai-dlc-pilot` para no bloquear PILOT-02, pero el checkout principal/`develop` siguen sin el commit real | Decisión del usuario: ¿commitear el skill en `develop`/`main`, o dejarlo intencionalmente local? |

---

## §4 · REGISTRO DE EJECUCIÓN

| Fecha | Card | Resultado | Gatekeeper (tests/ruff/migr) | Commit |
|---|---|---|---|---|
| 2026-08-22 | PILOT-01 | DONE | 107 tests OK (5 skip) / ruff limpio / migraciones limpias | `acb20a9`, `e9f783d` (`agent/ai-dlc-pilot`) |
| 2026-08-22 | PILOT-02 | DONE | 107 tests OK (5 skip) / ruff limpio (0 archivos .py tocados) / migraciones limpias | `78c4cdc`, `f539d81` (`agent/ai-dlc-pilot`) |
| 2026-08-22 | PILOT-03 | DONE | 112 tests OK (5 skip) / ruff limpio / migraciones limpias | `9e58de9` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-01 | DONE | 112 tests OK (5 skip) / ruff limpio / migraciones limpias | `7ff867a` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-02 | DONE | 115 tests OK (5 skip) / ruff limpio (2 archivos) / migraciones limpias | `d958064` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-03 | DONE | 123 tests OK (5 skip) / ruff limpio (4 archivos) / migraciones limpias | `f570cda` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-04 | DONE | 133 tests OK (5 skip) / ruff limpio (5 archivos) / migraciones limpias | `9e8ab83` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-05 | DONE | 143 tests OK (5 skip) / ruff limpio (2 archivos) / migraciones limpias | `40ffbfa` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-06 | DONE | 146 tests OK (5 skip) / ruff limpio / migraciones limpias | `bbbd99b` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-07 | DONE | 150 tests OK (5 skip) / ruff limpio (3 archivos) / migración 0023 incluida | `0725d09` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-08 | DONE | 155 tests OK (5 skip) / ruff limpio / migraciones limpias | `c3e9f3c` (`agent/ai-dlc-pilot`) |
| 2026-08-23 | BOLT-09 | DONE | 162 tests OK (5 skip) / ruff limpio (2 archivos, autofix) / migraciones limpias | `2593784` (`agent/ai-dlc-pilot`) |
| 2026-09-01 | SYNC (no es card) | rama actualizada a `develop` vía `git merge --ff-only` (traía 14 commits, incl. el merge del propio piloto `45eca7b` del 2026-08-24) | 198 tests OK (5 skip) / ruff limpio / migraciones limpias | `0e2e7c5` (tip post-sync, `agent/ai-dlc-pilot`) |
| 2026-09-01 | BOLT-10 | DONE | 200 tests OK (5 skip, +2) / ruff limpio (1 archivo) / migraciones limpias | *(pendiente, se completa tras el commit de este turno)* |

*(El validador (PILOT-02) agrega una fila por card cerrada o bloqueada. Este es el historial que el planificador lee al inicio de cada corrida.)*
