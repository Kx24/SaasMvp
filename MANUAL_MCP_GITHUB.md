# Manual MCP GitHub

Guía técnica replicable para instalar, configurar y operar el **GitHub MCP Server** dentro de Claude Code en este proyecto (y en cualquier otro repo del equipo).

> **Nota sobre el paquete usado.** El paquete npm `@modelcontextprotocol/server-github` (el "reference server" original de la comunidad) está archivado. GitHub mantiene hoy su propio servidor oficial, [`github/github-mcp-server`](https://github.com/github/github-mcp-server), que se puede consumir de dos formas: **remoto** (hosteado por GitHub, auth por OAuth) o **local** (binario/Docker, auth por Personal Access Token).
>
> **Probado en este repo:** la variante remota (`https://api.githubcopilot.com/mcp/` + `claude mcp login github`) **falla** con `Incompatible auth server: does not support dynamic client registration` — ese endpoint exige un cliente OAuth pre-registrado con GitHub (pensado para clientes que GitHub ya vetó, como Copilot en VS Code) y Claude Code no lo tiene. No es un error de configuración, es una incompatibilidad real entre Claude Code y ese endpoint específico a la fecha de este manual. Por eso la variante que quedó **activa en este repo es local + PAT** (binario oficial, sin Docker); la remota queda documentada abajo solo como referencia si en el futuro se resuelve la incompatibilidad.

## 1. Propósito e Impacto

Este setup ataca tres ineficiencias detectadas en el flujo de trabajo real del proyecto (ver diagnóstico de comportamiento Git):

| Ineficiencia detectada | Mitigación con MCP |
|---|---|
| Context-switching constante entre VS Code/terminal y la interfaz web de GitHub para crear PRs o revisar CI | Herramientas de PR, branches y CI quedan disponibles como *tool calls* dentro de la misma sesión de Claude Code — cero saltos de ventana |
| Commits locales que quedan sin pushear al cerrar una tarea o cambiar de rama (ej. `fad374d` en `main`, detectado en auditoría) | Regla operativa en `CLAUDE.md` (§ Automatización Git/GitHub) que obliga a chequear `git status`/`log origin/<branch>..<branch>` antes de cerrar o cambiar de contexto |
| Cero uso de `gh` CLI — cherry-picks y PRs se hacían a mano, sin protocolo de confirmación | El MCP expone `create_pull_request`, `list_branches`, etc. directamente en el chat; las reglas en `CLAUDE.md` fuerzan confirmación explícita antes de cherry-pick o de abrir un PR, evitando acciones silenciosas sobre estado compartido |

El impacto esperado no es "escribir menos comandos" sino **reducir el número de veces que salís del flujo de la tarea** para ir a revisar algo en github.com, y **cerrar la brecha de sincronización** que ya causó pérdida de trabajo pusheado.

## 2. Requisitos Previos

- **Node.js ≥ 18** y `npx` disponibles (usados por otros MCP servers stdio del proyecto; el GitHub MCP remoto en sí no depende de Node). Verificado en esta máquina: Node `v22.19.0`, npx `10.9.3`.
- **Git ≥ 2.x** (verificado: `2.51.0`).
- **Claude Code CLI** actualizado (verificado: `2.1.268`) — la subcomanda `claude mcp` requiere una versión reciente.
- **Cuenta de GitHub** con acceso al repositorio.
- **Personal Access Token (PAT)** — requisito para la variante activa en este repo (sección 3.1), no opcional acá: un *Personal Access Token* **classic** (⚠️ no fine-grained — el servidor MCP espera los nombres de permisos/scopes tradicionales de los tokens clásicos, un fine-grained token no expone `repo`/`workflow`/`read:org` de la misma forma y no es compatible) con los scopes:
  - `repo` — leer/escribir contenido, PRs, branches (marcar la casilla principal selecciona todas las subcasillas).
  - `workflow` — leer/disparar GitHub Actions.
  - `read:org` — dentro del grupo `admin:org`, marcar **únicamente** esa opción (no todo el grupo) si el repo pertenece a una organización.

  Generarlo en GitHub → *Settings* → *Developer settings* → *Personal access tokens* → **Tokens (classic)** → *Generate new token (classic)*. Copiar el token apenas se genera (empieza con `ghp_...`) — GitHub no lo vuelve a mostrar. **No pegues el token en el chat de Claude** — se queda en el historial de la conversación. Setealo como variable de entorno del sistema (`GITHUB_PERSONAL_ACCESS_TOKEN`), nunca escrito literal en `.mcp.json`. Si la cuenta pertenece a una organización con **SSO/SAML forzado** (típico en cuentas Teams/Enterprise), el token classic queda creado pero **sin autorizar** para esa org hasta que hagas *Configure SSO* → *Authorize* sobre el token recién generado en la misma pantalla de *Personal access tokens* — si el MCP conecta pero las tools devuelven 403/404 en repos de la org, este es el primer sospechoso.
- **Docker** — no lo necesitás para la variante activa (binario directo). Solo si preferís la variante 3.3.
- **`gh` CLI**: no está instalado en este equipo y **no es un requisito** para el MCP (son dos integraciones independientes). Si igual lo querés para uso manual en terminal: `winget install --id GitHub.cli`, luego `gh auth login`.

## 3. Instalación Paso a Paso

### 3.1 Variante activa en este repo — binario local + PAT (sin Docker)

No requiere Docker (no está instalado en esta máquina) — se usa el binario oficial de Windows publicado en [releases de `github/github-mcp-server`](https://github.com/github/github-mcp-server/releases/latest).

```powershell
# 1. Crear el PAT en GitHub (Settings -> Developer settings -> Personal access tokens (classic))
#    Scopes: repo, workflow, read:org (ver sección 2 sobre classic vs fine-grained y SSO). NO lo pegues en el chat de Claude.

# 2. Descargar el binario para Windows del último release (assets del release, github-mcp-server_Windows_x86_64.zip)
#    y extraerlo, ej.:
#    C:\Users\sanch\tools\github-mcp-server\github-mcp-server.exe

# 3. Setear el PAT como variable de entorno de usuario (una sola vez, persiste entre sesiones)
[Environment]::SetEnvironmentVariable("GITHUB_PERSONAL_ACCESS_TOKEN", "ghp_xxx...", "User")
# Paso crítico de recarga: cerrá TODAS las ventanas abiertas de PowerShell y de VS Code
# (no alcanza con abrir una pestaña nueva) para que Windows registre la variable a nivel usuario.
# Verificá en una ventana nueva:
$env:GITHUB_PERSONAL_ACCESS_TOKEN   # debe imprimir el token, empieza con ghp_...

# 4. Registrar el servidor en Claude Code (scope de proyecto, queda en .mcp.json)
claude mcp add --scope project github -e GITHUB_PERSONAL_ACCESS_TOKEN -- "C:\Users\sanch\tools\github-mcp-server\github-mcp-server.exe" stdio
# Si la CLI rechaza esto con "Invalid environment variable format: GITHUB_PERSONAL_ACCESS_TOKEN,
# environment variables should be added as: -e KEY1=value1 -e KEY2=value2" (le pasó a un miembro
# del equipo con su versión de Claude Code), usar el formato KEY=VALUE explícito en su lugar:
claude mcp add --scope project github -e GITHUB_PERSONAL_ACCESS_TOKEN=$env:GITHUB_PERSONAL_ACCESS_TOKEN -- "C:\Users\sanch\tools\github-mcp-server\github-mcp-server.exe" stdio

# 5. Verificar
claude mcp list
claude mcp get github
# Si el estado es "⏸ Pending approval (run `claude` to approve)": abrí una sesión interactiva
# con `claude`, aceptá (y) cuando pregunte si autorizás ejecutar github-mcp-server.exe, salí
# (Ctrl+C o /exit) y volvé a correr `claude mcp list` — debería quedar en "✔ Connected".
```

Con `-e GITHUB_PERSONAL_ACCESS_TOKEN` (sin `=valor`) Claude Code toma el valor del entorno del proceso en el momento de lanzar el server, así el token nunca queda escrito en `.mcp.json`, solo el nombre de la variable — es el formato preferido; usar `=valor` explícito (paso 4, variante de fallback) solo si tu versión de la CLI rechaza la forma corta.

### 3.2 Variante no funcional en este cliente — servidor remoto + OAuth

Documentada solo como referencia. Falla con `Incompatible auth server: does not support dynamic client registration` (ver nota al inicio del manual):

```bash
claude mcp add --transport http --scope project github https://api.githubcopilot.com/mcp/
claude mcp login github   # falla en el paso de auth
```

Si en el futuro GitHub o Claude Code resuelven la incompatibilidad, o si tu organización registra una OAuth App propia (`claude mcp add ... --client-id <id> --client-secret`), esta variante evita manejar un PAT — pero **hoy no es viable de forma directa** con `api.githubcopilot.com/mcp/`.

### 3.3 Variante equivalente con Docker

Si preferís no distribuir el binario y ya tenés Docker instalado:

```bash
claude mcp add --scope project github \
  -e GITHUB_PERSONAL_ACCESS_TOKEN \
  -- docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server
```

### 3.4 Solución de problemas conocidos (variante binario local + PAT)

Tres errores reales encontrados instalando esto, en el orden en que suelen aparecer:

1. **`Invalid environment variable format: GITHUB_PERSONAL_ACCESS_TOKEN, environment variables should be added as: -e KEY1=value1 -e KEY2=value2`** al correr el paso 4. Depende de la versión de Claude Code CLI — algunas exigen el formato `-e KEY=VALUE` explícito y no aceptan pasar solo el nombre de la variable. Solución: usar `-e GITHUB_PERSONAL_ACCESS_TOKEN=$env:GITHUB_PERSONAL_ACCESS_TOKEN` (PowerShell resuelve el valor antes de pasarlo a la CLI, no queda hardcodeado en ningún archivo del repo).

2. **`⏸ Pending approval (run \`claude\` to approve)`** en `claude mcp list` tras registrar el server. Es la política normal de Claude Code de pedir aprobación explícita la primera vez que un proyecto define un servidor MCP local (ver también nota de aprobación en la sección 6). Se resuelve abriendo una sesión interactiva (`claude`), aprobando con `y` cuando pregunta si autorizás ejecutar `github-mcp-server.exe`, y saliendo.

3. **`EUNKNOWN: unknown error, uv_spawn`** en `claude mcp list`/`claude mcp get github`, con el server registrado y el paso 2 aprobado. En Windows esto puede no ser un problema de configuración de Claude Code sino el sistema operativo bloqueando el binario antes de que llegue a ejecutarse. Para diagnosticarlo, correr el `.exe` directo:
   ```powershell
   & "C:\Users\sanch\tools\github-mcp-server\github-mcp-server.exe" --version
   ```
   Si PowerShell devuelve algo como *"Una directiva de Control de aplicaciones bloqueó este archivo"*, es **Smart App Control de Windows** rechazando un binario sin firma/reputación reconocida — confirmable con:
   ```powershell
   Get-ItemPropertyValue -Path "HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy" -Name "VerifiedAndReputablePolicyState"
   # 0 = apagado · 1 = activo (enforcement) · 2 = modo evaluación
   ```
   No hay forma de aprobar una excepción puntual para un binario específico bajo Smart App Control — las opciones son (a) desactivarlo en *Configuración → Privacidad y seguridad → Seguridad de Windows → Control de aplicaciones y navegador* (baja la postura de seguridad general del equipo, no solo para este binario, y **si Windows ya lo desactivó automáticamente en algún momento no se puede reactivar sin reinstalar el sistema**), o (b) usar la variante Docker (sección 3.3) — Docker Desktop corre como servicio ya confiado por el sistema, así que no dispara este bloqueo. En equipos gestionados por IT (frecuente en cuentas Teams/Enterprise, ver sección 6) esta política puede estar forzada por MDM y ni siquiera ser desactivable por el usuario — ahí Docker o pedir a IT que firme/allowliste el binario son las únicas rutas.

## 4. Plantilla de Configuración (`mcp.json`)

Esto es lo que va a quedar escrito en `.mcp.json` en la raíz de este repo una vez que corras el paso 4 de la sección 3.1 (variante binario local + PAT — sin secretos en el archivo, apto para commitear):

```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "C:\\Users\\sanch\\tools\\github-mcp-server\\github-mcp-server.exe",
      "args": ["stdio"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

Variante Docker equivalente (si preferís no distribuir el binario, sección 3.3):

```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

Para copiar esto a otro proyecto: pegar el bloque en un `.mcp.json` nuevo en la raíz de ese repo, o correr el comando equivalente de `claude mcp add` de la sección 3 directamente ahí.

## 5. Comandos MCP y Flujos de Uso

Los nombres exactos de las tools quedan expuestos por el servidor al conectarse (podés listarlos en cualquier momento preguntándole a Claude "qué herramientas tenés del MCP de github" dentro de la sesión). Las que vas a usar con más frecuencia para los flujos de este proyecto:

| Tool | Qué hace | Prompt natural de ejemplo |
|---|---|---|
| `create_pull_request` | Crea un PR desde una branch hacia otra | *"Creá un PR de `feature/RanchocachimbaEtapa1` hacia `develop` con los últimos 3 commits RC-BOLT"* |
| `list_pull_requests` / `get_pull_request` | Lista/inspecciona PRs abiertos | *"¿Qué PRs están abiertos contra `develop` ahora mismo?"* |
| `list_branches` | Lista branches remotas | *"Listá las branches del repo y decime cuáles no tienen actividad hace más de 30 días"* |
| `list_commits` / `get_commit` | Compara/inspecciona commits | *"Compará qué commits tiene `feature/Mejora_Login` que no están en `develop`"* |
| `list_workflow_runs` / `get_workflow_run` | Estado de CI (GitHub Actions) | *"¿Cómo quedó el último run de CI en `develop`?"* |
| `create_issue_comment` / `list_issues` | Comentar o leer issues | *"Comentá en el issue #12 que el fix ya está en el PR #34"* |

Flujos combinados con las reglas ya escritas en `CLAUDE.md` (§ Automatización Git/GitHub):

- **Antes de cerrar sesión o cambiar de branch:** Claude corre el chequeo de sincronización local (`git status --short --branch`, `git log origin/<branch>..<branch>`) y avisa si hay commits sin pushear — no requiere el MCP, es git plano, pero se apoya en las mismas tools de branches/commits si preferís pedirle el estado remoto vía MCP en vez de git local.
- **Cherry-pick hacia `develop`:** pedile a Claude *"aplicá cherry-pick del commit AUD-14 a develop"* — va a mostrarte el diff exacto primero y esperar tu confirmación antes de ejecutar el `git cherry-pick`.
- **PR al cerrar una tanda de commits:** pedile *"cerrá el PR de la tanda RC-BOLT hacia develop"* — prepara título/resumen a partir de los commits con ese prefijo y te confirma antes de llamar a `create_pull_request`.

## 6. Adaptación para Cuentas Claude Teams

### 6.1 Dos identidades separadas: Claude Teams (login) y GitHub (PAT)

Punto de confusión frecuente al pasar de "una persona en su máquina" a "equipo con Claude Teams": **son dos sistemas de autenticación completamente independientes**, uno no le da acceso al otro.

- **Identidad Claude**: con qué cuenta iniciás sesión en Claude Code/claude.ai. En un plan Teams, típicamente se administra por SSO corporativo o por invitación a un correo — si tu organización usa Microsoft 365, eso puede ser tu cuenta de **Outlook/Entra ID**. Esta identidad controla qué *seat* de Claude Teams usás, políticas de la consola admin, límites de uso, etc. **No tiene nada que ver con GitHub.**
- **Identidad GitHub**: la cuenta dueña del PAT que registraste en el paso 3 de la sección 3.1. El MCP se autentica contra GitHub con *ese* PAT, sin importar con qué correo iniciaste sesión en Claude. Si mañana tu empresa te da un usuario de Claude Teams con tu correo corporativo, pero seguís usando tu PAT de tu cuenta personal de GitHub, el MCP sigue operando como **vos, en GitHub, con los permisos de tu cuenta personal** — Claude Teams no eleva ni cambia esos permisos.

**Consecuencia práctica:** loguearte a Claude Code con un correo Outlook/corporativo (Teams) no te da ni le quita acceso a ningún repo de GitHub. El acceso a un repo lo define GitHub (dueño del repo, colaboradores, organización), siempre.

### 6.2 Tu caso: repos personales compartidos con un colega (sin organización de GitHub)

Respondiendo directo a la duda: **sí, podés usar tu PAT personal para el MCP de ese proyecto**, con una condición — que tu cuenta personal de GitHub tenga acceso al repo que vas a compartir (como dueño, o agregado como *colaborador* si el repo es de tu colega). El PAT solo puede hacer lo que tu cuenta de GitHub ya puede hacer manualmente en ese repo; no amplía ni reduce permisos por sí mismo.

Cómo queda el setup en este escenario (dos personas, repos personales, sin org):

1. **Cada persona usa su propio PAT**, generado desde su propia cuenta de GitHub — vos no le pasás tu PAT a tu colega, ni usás el de él. Si tu colega es dueño del repo, te agrega como **colaborador** (*Settings → Collaborators* en GitHub) con permiso de escritura antes de que tu PAT sirva de algo ahí.
2. **`repo` alcanza como scope** para repos personales — `read:org` no aplica si no hay organización de por medio (podés dejarlo sin marcar, no rompe nada tenerlo pero no hace nada). `workflow` seguí necesitándolo si el repo tiene GitHub Actions.
3. **El mismo `.mcp.json` del repo sirve para los dos**: si lo commiteás con la plantilla de la sección 4 (`"${GITHUB_PERSONAL_ACCESS_TOKEN}"`, sin el valor real), tu colega clona el repo, corre sus propios pasos 1-4 de la sección 3.1 con **su** PAT, y el MCP le funciona igual del lado suyo — cada uno autenticado como sí mismo contra GitHub.
4. **No hace falta Claude Teams para esto en absoluto** — es 100% una cuestión de permisos de GitHub entre cuentas personales. Claude Teams solo importaría acá si además de compartir código quisieran compartir *contexto de Claude* (historial de sesiones, políticas de uso) entre ustedes dos — algo separado del MCP.

### 6.3 Operar 100% por consola, sin instalar `gh` CLI

Todo lo de este manual (secciones 3.1-3.4) usa exclusivamente `claude` (CLI de Claude Code) y comandos nativos de PowerShell (`[Environment]::SetEnvironmentVariable`, `$env:...`) — en ningún paso hace falta `gh` CLI. Una vez que el MCP está `✔ Connected`, el uso del día a día tampoco requiere `gh`: le pedís a Claude en lenguaje natural las acciones de la tabla de la sección 5 (crear PR, listar branches, revisar CI, comentar issues) y las tools del MCP las ejecutan directo contra la API de GitHub — el único lugar donde `gh` aparece en este manual es como alternativa opcional si preferís invocar esas mismas acciones vos mismo desde la terminal en vez de pedírselas a Claude (sección 2), nunca como requisito del MCP.

### 6.4 Buenas prácticas adicionales si más adelante hay organización/Enterprise

Para estandarizar esto en un equipo más grande (no solo en esta máquina):

- **`.mcp.json` versionado en el repo** (como quedó acá): todo el equipo obtiene la misma definición de servidor al clonar, pero el valor del PAT nunca viaja con el archivo (queda como `${GITHUB_PERSONAL_ACCESS_TOKEN}`, cada integrante lo setea localmente en su propio entorno). Como la variante activa es PAT y no OAuth, cada desarrollador necesita su **propio PAT personal** (mismos 3 scopes) — no reusar el PAT de otra persona.
- **PAT corporativo solo para service accounts**, nunca para desarrolladores individuales: si el equipo necesita un pipeline (CI, bot de release) que use el MCP sin intervención humana, usar la variante Docker de la sección 3.3 con un PAT de una cuenta de servicio dedicada, con los scopes mínimos (`repo`, `workflow`, `read:org`) y rotación periódica — nunca el PAT personal de un desarrollador.
- **Secretos compartidos**: si el PAT de service account debe llegar a varias máquinas/CI, gestionarlo por el secret manager que ya use la organización (GitHub Actions secrets, Vault, etc.), nunca por Slack/email/`.mcp.json` commiteado.
- **`CLAUDE.md` como contrato de equipo**: la sección "Automatización Git/GitHub (MCP)" de este repo (reglas de sincronización, cherry-pick asistido y PR con confirmación) es el patrón a replicar textualmente en el `CLAUDE.md` de cualquier otro repo del equipo que adopte este MCP — así el comportamiento de Claude Code es consistente entre proyectos, sin depender de que cada developer recuerde pedirlo.
- **Política de aprobación de `.mcp.json`**: Claude Code pide aprobar servidores definidos en `.mcp.json` la primera vez que se abre el proyecto (pantalla de *Pending approval*, ver sección 3.4 punto 2). Es intencional — comunicar al equipo que aprobar el servidor `github` en este repo es seguro (es el oficial de GitHub), para que no lo rechacen por desconocimiento.
- **SSO/SAML de la organización**: si la cuenta de GitHub de la organización fuerza SSO (común en cuentas Enterprise), cada PAT classic individual necesita el paso extra *Configure SSO → Authorize* (sección 2) antes de poder leer/escribir en los repos de esa org — sin eso el MCP conecta pero las tools fallan con 403/404 en vez de un error de auth claro. Documentarlo explícitamente al onboardear gente nueva, porque el síntoma no apunta obviamente a la causa.
- **Verificar el `scope` al registrar en cada máquina**: `claude mcp add --scope project` escribe en el `.mcp.json` del repo (compartible, sin secretos); sin ese flag, o con `--scope user`, Claude Code puede registrar el server en la config global del usuario (`~/.mcp.json` o el `~/.claude.json` de esa cuenta) en vez del archivo del proyecto — dos desarrolladores pueden terminar con configuraciones distintas para "el mismo" server si no todos usan el mismo scope. En equipo, estandarizar siempre en `--scope project`.
- **Endpoint management / MDM corporativo**: en equipos con laptops gestionadas por IT, políticas como Smart App Control (sección 3.4 punto 3), Windows Defender Application Control o EDRs corporativos pueden bloquear la ejecución de binarios descargados manualmente aunque el usuario tenga permisos de admin local — no asumir que un fallo de conexión es un problema de Claude Code o del token antes de descartar esto. La variante Docker (sección 3.3) suele evitar el problema porque el binario corre dentro de un contenedor gestionado por un servicio ya confiado, en vez de como un `.exe` suelto.
- **Rotación y expiración forzada de PATs**: cuentas Enterprise suelen tener políticas de organización que limitan la expiración máxima de un PAT classic (ej. 90 días) o prohíben tokens sin expiración. Si el MCP empieza a fallar con errores de auth (no `uv_spawn`, no `Pending approval`) después de haber funcionado, el PAT vencido/revocado por política de la org es la primera causa a revisar — regenerarlo y re-setear la variable de entorno (paso 3 de la sección 3.1), no hace falta volver a correr `claude mcp add`.

## 7. Repo catálogo para perfiles/agentes de equipo

Idea para escalar esto de "un MCP en un repo" a "profesionalizar cómo el equipo trabaja con IA": un repositorio propio, separado de los proyectos de producto (`SaaSMVP`, el dashboard del jefe de área, etc.), que actúe como catálogo versionado de configuración de Claude Code para el equipo — manuales, plantillas de `CLAUDE.md` por tipo de rol/proyecto, y agentes/skills reutilizables.

### 7.1 Cómo se comparte

Mismo modelo de permisos ya descrito en 6.2: repo propio (o de quien lo cree), colaboradores agregados a mano, cambios propuestos vía PR — de hecho es un buen primer caso de uso real para practicar el flujo de commit/PR/aprobación con el jefe de desarrollo antes de llevarlo a `SaaSMVP`.

### 7.2 Qué SÍ viaja automáticamente al clonar, y qué no

Punto técnico clave para no armar expectativas equivocadas:

- **`.claude/agents/*.md` y `.claude/skills/*/SKILL.md` dentro de un repo** (commiteados) → se activan solos: cualquiera que clone ese repo y trabaje ahí con Claude Code los tiene disponibles de inmediato, sin instalar nada aparte. Es "configuración como código", igual que `.mcp.json` o `CLAUDE.md`.
- **`~/.claude/agents/` a nivel de usuario** (fuera de cualquier repo) → personal de cada máquina, no viaja con git.
- **Consecuencia:** un repo-catálogo separado de `SaaSMVP`/dashboard **no se "activa" solo por existir en GitHub**. Si alguien clona el catálogo pero trabaja del día a día en otro repo (`SaaSMVP`), los agentes/skills del catálogo no aparecen ahí automáticamente — hay que copiar los archivos relevantes al `.claude/` de ese proyecto de trabajo (o al `~/.claude/` de usuario si se quieren globales en la máquina). El catálogo es un repositorio **para copiar**, no un plugin que se "instala" con solo clonarlo.

### 7.3 Qué pondría este repo catálogo

- `MANUAL_MCP_GITHUB.md` (este manual, en versión genérica sin rutas/tokens de un proyecto puntual).
- `templates/CLAUDE.md.<perfil>.md` — una base por tipo de rol/proyecto (ej. `CLAUDE.md.dev-lead.md` con reglas de aprobación de PR y gestión de versiones; `CLAUDE.md.explorador-plantillas.md` con reglas acotadas a plantillas/exploración, sin tocar infraestructura ni abrir PRs a `main` sin pedirlo).
- `.claude/agents/` y `.claude/skills/` reutilizables entre proyectos (ej. un agente "revisor de PR", uno "gestor de versiones/changelog", uno "explorador de plantillas").
- Un `README.md` que explique el paso manual de adopción: *"cloná este repo, copiá la carpeta `.claude/` (o los archivos puntuales que necesites) dentro del repo de trabajo correspondiente a tu rol, y el `CLAUDE.md.<perfil>.md` que aplique renómbralo a `CLAUDE.md` ahí"*.

### 7.4 Dónde está esto en el plan del equipo ahora mismo

Esto queda **anotado como idea a futuro, no priorizado todavía**. El orden acordado con el usuario es: (1) primero probar commit/PR con el jefe de desarrollo sobre `SaaSMVP`, (2) esperar a que se cree la rama/repo del piloto de dashboard, (3) recién ahí definir entre los tres (usuario, jefe de desarrollo, jefe de área) cómo se reparten los roles y permisos — sin adelantar esa decisión unilateralmente. El repo catálogo de este apartado sería un paso posterior, cuando ya haya al menos dos perfiles reales probados y valga la pena generalizar la plantilla en vez de reescribirla desde cero.

---

*Generado como parte de la configuración de automatización Git/GitHub de este workspace. Ver también `CLAUDE.md` (§ Automatización Git/GitHub) para las reglas operativas que consumen este MCP. Secciones 2 (classic vs fine-grained, SSO), 3.1 (recarga de variable, formato `-e KEY=VALUE`, aprobación pendiente) y 3.4 incorporan el paso a paso verificado en `Documentacion/Guia Detallada de Instalacion y Resolucion GitHub MCP Server.md`.*
