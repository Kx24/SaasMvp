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

### 0.0 Estructura real del repo (verificada 2026-08-22 — NO usar `docs/Structure.md`, está desactualizado)

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

### [PILOT-03] Script orquestador con manejo de turnos
- **Estado:** TODO
- **Componente:** DevOps
- **Variables requeridas:** ninguna (el runner del agente provee su propia autenticación; el script no maneja API keys en código)
- **Archivos Afectados:** `orchestrate.py` (raíz, nuevo)
- **Contexto:** depende de PILOT-01 (gate parseable) y PILOT-02 (roles). Cierra el circuito planificador → dev → validador.
- **Spec ejecutable:** `python orchestrate.py [--max-cards N] [--dry-run]` ejecuta el ciclo: turno planificador → turno dev/tester → gatekeeper → turno validador. Máximo **3 reintentos** por card en el paso REPAIR; al agotarlos marca la card `BLOCKED` con el último JSON del gatekeeper como diagnóstico y **pasa a la siguiente o termina** (nunca queda en loop). Log estructurado por turno en `scripts/output/orchestrator_{timestamp}.jsonl` (carpeta ya gitignorada, `#AUD-10`). `--dry-run` simula los turnos sin invocar agentes (para testear la máquina de estados sin costo).
- **Definición de Terminado (DoD Verificable):**
  - [ ] Test de la máquina de estados escrito (Red → Green) con agentes stub: happy path (1 card → DONE), reintento (2 fallos + 1 éxito → DONE con `attempts: 3`), agotamiento (4 fallos → BLOCKED, sin 4º reintento).
  - [ ] Implementación mínima que pase la suite de pruebas.
  - [ ] Cero errores en Linter (`ruff check orchestrate.py`).
  - [ ] Sin side-effects fuera del alcance de la tarjeta (no commitea por sí solo sin gate en verde; `--dry-run` no escribe nada fuera de `scripts/output/`).

---

## §2 · ATOMIC BOLTS DE PRODUCTO (Backlog de Corto Plazo)

> Seleccionados del kanban maestro por ser 100 % ejecutables desde el repo (sin secretos, sin insumos
> del cliente, sin dashboards externos), de bajo acoplamiento entre sí y de 15–45 min cada uno.
> Orden sugerido: BOLT-01 primero (asegura terreno firme); el resto es independiente.

### [BOLT-01] Confirmar suite en verde tras el retiro de `apps/core/managers.py`
- **Estado:** TODO
- **Componente:** Backend
- **Variables requeridas:** ninguna
- **Archivos Afectados:** ninguno esperado (solo ejecución + actualización de `Documentacion/KANBAN_PROYECTO.md` §"Retomar aquí" y este archivo)
- **Contexto:** `#DEUDA-05` eliminó la copia muerta de `TenantAwareManager` en `apps/core/managers.py`, pero esa sesión **no pudo correr la suite completa** (bloqueada por el runner). El import en frío funcionó; falta la confirmación formal. Es el único cabo suelto verificable desde el repo que quedó abierto.
- **Definición de Terminado (DoD Verificable):**
  - [ ] `python manage.py test apps -v 1` completa en verde (≈103 tests, 1 skip) — la suite entera ES el test de esta card; si algo falla por el archivo eliminado, restaurar el import mínimo roto es el fix.
  - [ ] `python -m ruff check apps/ config/` sin errores nuevos y `makemigrations --check --dry-run` limpio.
  - [ ] Nota de cierre del pendiente registrada en `KANBAN_PROYECTO.md` (§"Retomar aquí" y card `#DEUDA-05`).
  - [ ] Sin side-effects fuera del alcance de la tarjeta.

### [BOLT-02] Slugs reservados en `Plan` — cierre del DoD de `#AUD-01`
- **Estado:** TODO
- **Componente:** Backend
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/orders/models.py` (validación en `Plan`), `apps/orders/tests/test_models.py` (o `test_urls.py`), migración solo si se agrega `validators=` a nivel de campo
- **Contexto:** cabo suelto explícito del kanban maestro (§7, `#AUD-01`, checkbox abierto): un `Plan` con slug `process`, `success` o `error` queda inalcanzable en silencio — `apps/orders/urls.py` resuelve esas rutas literales antes que `<slug:plan_slug>/`.
- **Spec ejecutable:** `Plan.clean()` (y/o validator del campo `slug`) rechaza `{'process', 'success', 'error'}` con `ValidationError` que nombra el conflicto de ruta. Cubrir también `full_clean()` en `save()` si el modelo no lo llama hoy (verificar patrón existente del modelo antes de imponerlo).
- **Definición de Terminado (DoD Verificable):**
  - [ ] Test escrito que exprese la funcionalidad (Red → Green): crear `Plan(slug='process')` lanza `ValidationError`; los 3 slugs reservados cubiertos; un slug normal sigue pasando.
  - [ ] Implementación mínima que pase la suite de pruebas.
  - [ ] Cero errores en Linter (`ruff check`).
  - [ ] Sin side-effects fuera del alcance de la tarjeta (planes existentes con slugs válidos no se ven afectados; `makemigrations --check` limpio o migración incluida).

### [BOLT-03] `#MED-05` (a) — IP confiable detrás del proxy de Render
- **Estado:** TODO
- **Componente:** Backend
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/core/rate_limit.py`, `apps/orders/views.py` (copia de `get_client_ip` en línea ~462), `apps/website/views.py` (segunda copia, línea ~52), tests nuevos en `apps/core/tests/`
- **Contexto:** hallazgo de auditoría (§1.2 del maestro): `get_client_ip()` confía en `X-Forwarded-For` completo → el rate-limit se evade spoofeando el header. Hay **dos copias duplicadas** de la función (verificado por grep: `apps/website/views.py:52` y `apps/orders/views.py:462`). Render (único proxy real delante de la app) escribe la IP del cliente en una posición conocida del XFF.
- **Spec ejecutable:** una única función canónica de resolución de IP en `apps/core/` (junto a `rate_limit.py`, que ya es el hogar de esta infraestructura), reemplazando ambas copias que tome la IP del **último salto confiable** (primer valor no confiable desde la derecha del XFF, con número de proxies confiables configurable vía setting con default 1) y caiga a `REMOTE_ADDR` sin header. Nada de listas de IPs hardcodeadas.
- **Definición de Terminado (DoD Verificable):**
  - [ ] Test escrito (Red → Green): XFF spoofeado con cadena larga no cambia la IP efectiva (el rojo se confirma mostrando que hoy sí la cambia); sin XFF usa `REMOTE_ADDR`; ambos consumidores (rate limit de contacto y checkout) usan la función canónica.
  - [ ] Implementación mínima que pase la suite de pruebas.
  - [ ] Cero errores en Linter (`ruff check`).
  - [ ] Sin side-effects fuera del alcance de la tarjeta (el rate limit de contacto existente sigue verde en su suite).

### [BOLT-04] `#MED-05` (b) — Rate limit en login y checkout
- **Estado:** TODO
- **Componente:** Auth
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/website/auth_views.py` (`client_login`), `apps/orders/views.py` (`process_payment_view`), `apps/core/rate_limit.py` (scopes nuevos), tests en `apps/website/tests/` y `apps/orders/tests/`
- **Contexto:** segunda mitad de `#MED-05`; depende de BOLT-03 (la IP debe ser confiable antes de limitar por IP). `RateLimiter` ya existe y está probado en el formulario de contacto — extender, no reescribir.
- **Spec ejecutable:** `scope='login'` (p. ej. 5 intentos/5 min por IP+username) sobre `client_login` y `scope='checkout'` sobre `process_payment_view`, con respuesta 429 y mensaje genérico (indistinguible del mensaje de credenciales inválidas de `#AUD-03` — no filtrar información). Límites como settings con defaults, no números mágicos inline.
- **Definición de Terminado (DoD Verificable):**
  - [ ] Test escrito (Red → Green): N+1 intentos de login fallidos → 429 (rojo: hoy responde 200/302 siempre); mismo patrón en checkout; un login legítimo bajo el umbral no se ve afectado; el contador no cruza tenants ni IPs.
  - [ ] Implementación mínima que pase la suite de pruebas.
  - [ ] Cero errores en Linter (`ruff check`).
  - [ ] Sin side-effects fuera del alcance de la tarjeta (matriz de `#AUD-03` y suite de aislamiento `#MED-02` siguen en verde).

### [BOLT-05] `#FLOW-02` — `check_tenant_setup` como gate de calidad ampliado
- **Estado:** TODO
- **Componente:** Multi-tenant
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `apps/tenants/management/commands/check_tenant_setup.py`, `apps/tenants/tests_check_tenant_setup.py` (nuevo — patrón plano `tests_*.py` de la app, ver §0.0; NO crear `apps/tenants/tests/`)
- **Contexto:** parte automatizable del flujo comercial repetible (`#FLOW-01/02` del maestro). El comando existe y verifica tema/dominio; el maestro pide ampliarlo: `SEOConfig` completo, cero placeholders visibles, `ClientEmailSettings` configurado.
- **Spec ejecutable:** agregar chequeos: (1) `SEOConfig` del tenant con título/descripción no vacíos ni placeholder; (2) contenido de secciones activas sin marcadores obvios (`lorem`, `placeholder`, `TODO`, `xxx` — lista en una constante del comando); (3) `ClientEmailSettings` presente y con remitente válido cuando el tenant tiene formulario de contacto. Salida con veredicto por chequeo y exit code ≠ 0 si algo falla (hoy es informativo — conservar `--warn-only` para el comportamiento actual si algún flujo lo consume).
- **Definición de Terminado (DoD Verificable):**
  - [ ] Test escrito (Red → Green) con `call_command`: tenant de prueba incompleto → exit/reporte de fallo por cada chequeo nuevo (rojo: hoy pasan en silencio); tenant completo → OK.
  - [ ] Implementación mínima que pase la suite de pruebas.
  - [ ] Cero errores en Linter (`ruff check`).
  - [ ] Sin side-effects fuera del alcance de la tarjeta (el comando sigue sin modificar datos — es solo lectura, como hoy).

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
| `#MED-04` (mitad manual) | Prueba visual en Gmail/Outlook móvil | Casillas reales del usuario (la mitad automatizable puede promoverse a bolt cuando se agote §2) |
| `#RC-*` completo | Todo Rancho Cachimba | **En pausa por decisión del usuario** — prohibido por §0.4 |
| `#DEUDA-05` (cabo) | Eliminar login muerto de `apps/accounts/` | Decisión explícita del usuario |

---

## §4 · REGISTRO DE EJECUCIÓN

| Fecha | Card | Resultado | Gatekeeper (tests/ruff/migr) | Commit |
|---|---|---|---|---|
| 2026-08-22 | PILOT-01 | DONE | 107 tests OK (5 skip) / ruff limpio / migraciones limpias | `acb20a9`, `e9f783d` (`agent/ai-dlc-pilot`) |
| 2026-08-22 | PILOT-02 | DONE | 107 tests OK (5 skip) / ruff limpio (0 archivos .py tocados) / migraciones limpias | *(pendiente — se completa al commitear)* |

*(El validador (PILOT-02) agrega una fila por card cerrada o bloqueada. Este es el historial que el planificador lee al inicio de cada corrida.)*
