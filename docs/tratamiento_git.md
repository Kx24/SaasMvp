# tratamiento_git.md — Git con agentes: comandos y buenas prácticas

> Guía operativa para el trabajo en paralelo entre el usuario y los agentes
> (piloto AI-DLC). Regla que resume todo: **la rama del agente es un buffer de
> trabajo verificado, no un lugar donde el trabajo vive.** Push por card, PR
> corto, merge con gate, rama muerta.

---

## 1. Principios

1. **Una rama + un worktree por flujo de agente.** El agente nunca opera en el
   checkout principal ni comparte rama con otro agente o con el usuario. WIP=1
   dentro de cada rama.
2. **Ramas de agente de vida corta.** Se crean desde `develop`, se integran por
   PR en días, y se borran. Las ramas largas fabrican "verdades" que el resto
   del repo no ve (el piloto encontró 4 artefactos varados en
   `feature/RanchocachimbaEtapa1` que el kanban daba por entregados).
3. **Push después de cada card, no al final de la sesión.** Pushear no es
   integrar: solo hace el trabajo visible y recuperable. "N commits sin pushear"
   es un estado que no debería existir al cerrar una card.
4. **Integrar por PR completo, no por cherry-pick.** El cherry-pick duplica
   contenido bajo hashes distintos y deja commits fuera del linaje de `develop`
   — exactamente la enfermedad detectada. Con PR, o el trabajo está en
   `develop`, o no está.
5. **El gate decide el merge.** `scripts/gatekeeper.py` (exit 0 ⇔ verde) debería
   correr como check del PR (GitHub Action pendiente); mientras tanto, ningún
   merge sin el JSON del gate en verde en el último commit.
6. **Un commit por card**, ID en la primera línea, kanban actualizado en el
   mismo commit, hallazgos incidentales documentados en el cuerpo.
7. **Nunca `git add -A` / `git add .`** en el worktree del agente: se arrastra
   el `.env` local o archivos sueltos. Siempre rutas explícitas.
8. **El stash es compartido** entre el checkout principal y todos los worktrees.
   Preferir un commit WIP temporal; si hay que stashear, hacerlo con tag único y
   `apply` (no `pop`) — ver §2.6.

---

## 2. Comandos por situación

### 2.1 Crear el entorno de un agente nuevo

```bash
# Desde el checkout principal, rama nueva desde develop + worktree hermano
git fetch origin
git worktree add ../SaaSMVP-<nombre-agente> -b agent/<nombre> origin/develop

# El .env NO se copia solo: recrearlo con los 4 valores dummy
# (SECRET_KEY, MP_PUBLIC_KEY, MP_ACCESS_TOKEN, MP_WEBHOOK_SECRET)
# y verificar el gate antes de la primera card:
cd ../SaaSMVP-<nombre-agente> && python scripts/gatekeeper.py
```

### 2.2 Verificar estado antes de asumir nada

```bash
git status --short --branch                      # rama, ahead/behind, sucio/limpio
git log origin/<rama>..<rama> --oneline          # qué hay local sin pushear
git log --all --oneline -- <ruta>                # ¿en qué ramas existe/existió un archivo?
git branch --all --contains <hash>               # ¿qué ramas contienen un commit?
git ls-files <ruta>                              # ¿está trackeado en ESTA rama?
```

### 2.3 Cierre de card (turno del validador)

```bash
git add <archivos tocados, explícitos> docs/kanban_agente.md
git commit -m "<CARD-ID>: <qué y por qué>"
git push                                          # ← parte del cierre, no opcional
```

### 2.4 Mantener la rama del agente fresca (si vive más de unos días)

```bash
git fetch origin
git rebase origin/develop        # conflictos chicos y frescos, no acumulados
# (si la rama ya fue pusheada y rebasada: git push --force-with-lease, NUNCA --force)
python scripts/gatekeeper.py     # re-verificar el gate después de todo rebase/merge
```

### 2.5 Integrar y matar la rama

```bash
git push -u origin agent/<nombre>
# PR agent/<nombre> → develop (gh pr create, o el link de compare de GitHub)
# Tras el merge:
git branch -d agent/<nombre>
git push origin --delete agent/<nombre>
git worktree remove ../SaaSMVP-<nombre-agente>
git worktree prune
```

### 2.6 Apartar trabajo a medias (stash compartido entre worktrees)

```bash
# Preferido: commit WIP temporal en la rama del agente
git add <rutas> && git commit -m "WIP <CARD-ID> (squashear antes del cierre)"

# Si hay que stashear sí o sí:
git stash push -u -m "agente-<nombre>-<card>"     # tag único
git stash list --format='%H %gs'                  # capturar el SHA propio
git stash apply <sha>                             # apply, no pop
git stash drop stash@{n}                          # re-ubicar por tag antes de drop
```

### 2.7 Diagnóstico de divergencias entre ramas

```bash
git log develop..feature/X --oneline              # qué tiene X que develop no
git diff develop...feature/X -- <ruta>            # diff de un archivo desde el ancestro común
git show <rama>:<ruta>                            # leer un archivo de otra rama sin checkout
git merge-base develop feature/X                  # ancestro común
```

---

## 3. Qué NO hacer

- ❌ Cherry-pick como mecanismo habitual de integración (solo para hotfix puntual
  y consciente del costo).
- ❌ Dejar una sesión de agente terminada sin pushear.
- ❌ `git stash` / `git stash pop` a secas en un worktree (pisa stashes ajenos).
- ❌ `git push --force` (si un rebase lo exige: `--force-with-lease`).
- ❌ Commitear con la suite en rojo, o "para probar en CI".
- ❌ Tocar `feature/RanchocachimbaEtapa1` desde un agente (en pausa por decisión
  del usuario; leer sus commits está bien, escribir no).
- ❌ Asumir que una branch está al día en GitHub sin correr los comandos de §2.2.

---

## 4. Flujo de integración de referencia

```
develop ──┬─▶ agent/<lote-1> ──(cards + push por card)──▶ PR ──merge──▶ develop
          │                                                              │
          └──────────────── siguiente lote arranca de develop fresco ◀───┘
develop ──▶ main : decisión de release del usuario, fuera del flujo de agentes.
```

Caso especial pendiente: al retomar `feature/RanchocachimbaEtapa1`, primero
`git merge develop` hacia esa rama — los cambios replicados por el piloto
(managers.py, check_tenant_setup) convergen sin conflicto, y la guardia de
tokens CSS (BOLT-06) marcará automáticamente los 114 usos rotos del hero.
