# Especificación BOLT — Hero Rancho Cachimba (análisis de diseño)

Generada según `docs/prompt_design_system.md` a partir del mockup aprobado
`Documentacion/Planificación/hero_cachimba.html` (commit `dd340dd`, #RC-06b),
contrastado contra `docs/design-system.md` y el código real del tema
`templates/ranchocachimba/`. **Esta sesión no modificó código de producción.**

## Estado del diff mockup ↔ código (qué ya existe)

Ya implementado en `#RC-06` y **sin card**:
- Hero split (grid `1.32fr 10px 1fr`), costura de tartán, foto B desplazada
  64px, pills "El oficio"/"La visita", bloque `hero-copy` que invade la foto A,
  eyebrow, breakpoint móvil — todo en `templates/ranchocachimba/components/hero.html`.
- Slots `hero_media_a`/`_b` → resueltos por el tag `get_hero_split_media` +
  preset Cloudinary `hero_split` 3:4. La dependencia de `#RC-02` que el mockup
  marcaba quedó cerrada con veredicto favorable ("hero split viable sin
  `#DEUDA-02`", ver kanban §3).

Propuestas del mapa de componentes del mockup **rechazadas por el design system**
(no generan card):
- *"Un solo `hero` con variante `layout: single|split`"* — contradice
  `docs/design-system.md` §2b: el hero split es la excepción documentada del
  tema (diferencia de estructura, no de estilo) y "no hay una tercera opción
  de generalizar con un flag más". Servelec no se toca.
- *"`hero_overlay` con `mode='block'`"* — mismo criterio: el bloque sólido que
  invade la foto ya vive dentro del hero del tema; agregar un modo al overlay
  compartido sería el anti-patrón que §2b prohíbe.

Decisiones de diseño que el mockup deja abiertas (resolver antes de `#RC-08`):
- **Composición por defecto: "pastoreo dominante" (1.32fr)**. El toggle
  `equilibrado` del mockup es herramienta de decisión, no feature de
  producción — no se implementa.
- **`<em>` amarillo en el h1** ("se mira en vivo"): el título viene del CMS
  como texto plano. Decidir si se soporta énfasis simple (p. ej. `*...*` →
  `<em>`) o se deja plano. Por defecto: plano, sin card.

Nota sobre el DoD: `scripts/gatekeeper.py`, `orchestrate.py` y
`docs/kanban_agente.md` existen, pero **en la branch `agent/ai-dlc-pilot`**
(worktree `SaaSMVP-agentic-pilot`), no en `feature/RanchocachimbaEtapa1`. Ese
piloto además tiene prohibido tocar Rancho Cachimba (su §0.4), y sus tarjetas
`BOLT-01..05` son de plataforma — por eso las de este documento se numeran
`RC-BOLT-*` y se ejecutan en esta branch, a mano. El gate verificable acá es
el de `CLAUDE.md`: `python -m ruff check` sobre los archivos tocados +
`python manage.py test apps` en verde +
`python manage.py makemigrations --check --dry-run` limpio.

Corte con el piloto (2026-08-24): las generalizaciones de plataforma que este
análisis dejó anotadas como "card aparte" ya tienen dueño — `BOLT-06` (guardia
automática del contrato de tokens, versión sistémica del hallazgo de
RC-BOLT-01), `BOLT-07` (CTA del navbar compartido configurable por tenant) y
`BOLT-08` (generalizar `hero_ctas` a `components/`) en `docs/kanban_agente.md`
de `agent/ai-dlc-pilot`. Las 6 RC-BOLT de abajo siguen siendo trabajo de esta
branch.

---

### ✅ [RC-BOLT-01] Tokens CSS rotos: `var(--primary)` no existe en el tema — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Frontend / Templates
- **Variables requeridas:** ninguna
- **Archivos Afectados:** los mismos 12 componentes de `templates/ranchocachimba/components/*.html` documentados abajo (recuento real al ejecutar: 143 ocurrencias, no 114 — ver hallazgo)
- **Contexto:** **Hallazgo del análisis, bloqueante del resto de las cards.** El `:root` de `templates/ranchocachimba/base.html:44-46` define `--color-primary`/`--color-secondary`/`--color-accent` (contrato de `docs/design-system.md` §1), pero los componentes consumen `var(--primary)`, `var(--secondary)` y `var(--accent)` — variables que **nadie define** (verificado también en `static/`): fondos del hero, gradientes del tartán, pills y CTAs resuelven a valor inválido/transparente. `navbar.html` sí usa `--gris-borde` y `--carbon`, que existen (`base.html:51-59`).
- **⚠️ Hallazgo al ejecutar (recuento desactualizado en el análisis original):** el conteo real por archivo al momento de aplicar el fix fue `about.html` ×25 (igual), `contact.html` ×21 (doc: 14), `cta.html` ×11 (doc: 8), `footer.html` ×5 (igual), `hero.html` ×14 (doc: 12), `hero_ctas.html` ×2 (doc: 1), `hero_effects.html` ×3 (igual), `hero_overlay.html` ×10 (doc: 7), `hero_overlay_theme.html` ×3 (doc: 2), `navbar.html` ×22 (doc: 15), `stats.html` ×7 (doc: 5), `why_us.html` ×20 (doc: 17) — total 143. El código evolucionó entre el análisis (`#RC-20`) y esta ejecución; mismo bug, mismos 12 archivos, sin archivos nuevos afectados (`services.html`, el único componente no listado, se verificó limpio — no usa las variables rotas).

- **Spec ejecutable:**
  1. Renombrar `var(--primary)` → `var(--color-primary)`, `var(--secondary)` → `var(--color-secondary)`, `var(--accent)` → `var(--color-accent)` en los 12 archivos (buscar/reemplazar exacto; no crear alias `--primary: var(--color-primary)` en `:root` — duplicar referencias de paleta es la deuda que `#AUD-11` eliminó).
  2. Verificación visual con el tenant `ranchocachimba` en dev: hero (fondo verde, tartán con hilos amarillos, pills), navbar, stats, footer.
  3. Sin lógica Alpine.js ni htmx involucrada.

- **Resultado:** reemplazo exacto `var(--primary)`→`var(--color-primary)`, `var(--secondary)`→`var(--color-secondary)`, `var(--accent)`→`var(--color-accent)` en los 12 archivos (sin variantes con fallback `var(--x, ...)` presentes — verificado antes del reemplazo). Sin alias nuevo en `:root`. Verificación visual sustituida por el smoke E2E real (`#TOOL-01`, sin insumos, siempre ejecutable): `npx playwright test` — 6/6 passed, incluye `ranchocachimba-e2e › home responde 200 y muestra hero, navbar y footer` en Chromium real.
- **Definición de Terminado (DoD Verificable):**
  - [x] `grep -r "var(--primary)\|var(--secondary)\|var(--accent)" templates/ranchocachimba/` → 0 resultados (143 ocurrencias corregidas).
  - [x] Gate real en verde: `ruff check` n/a (solo HTML tocado, 0 archivos `.py`), `python manage.py test apps` → 103 tests OK (1 skip), `makemigrations --check --dry-run` → sin cambios. Además `npx playwright test` → 6/6 passed (verificación visual real de hero/navbar/footer/stats para `ranchocachimba-e2e`, `servelec-e2e`, `andesscale`).
  - [x] Sin side-effects fuera del alcance de la tarjeta: otros temas (`servelec`, `themes/default`, `andesscale`) no tocados; `services.html` (único componente no listado) verificado limpio, sin cambios.

---

### ✅ [RC-BOLT-02] Barra de utilidad sobre el navbar — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Frontend / Templates
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `templates/ranchocachimba/components/utility_bar.html` (nuevo), `templates/ranchocachimba/base.html` (include), `templates/ranchocachimba/components/navbar.html` (offset `top-8` — ver hallazgo 2)
- **Contexto:** El mockup abre con una franja fina (`#172019` = `--carbon`) con ubicación ("Maullín · Región de Los Lagos") a la izquierda y "Visitas con reserva previa · **+56 9 ...**" (teléfono en `--color-accent`) a la derecha. No existe en ningún otro tema → por `#RC-09` es componente **de tema**, no de `templates/components/`.

- **Spec ejecutable:**
  1. HTML semántico: `<div>` de una línea, contenedor `max-w-7xl mx-auto` consistente con el navbar; layout con utilidades Tailwind (`flex justify-between flex-wrap gap-4 text-xs py-1.5`), no CSS inline nuevo.
  2. Colores vía tokens: fondo `--carbon`, texto blanco al 72%, teléfono/énfasis `--color-accent`.
  3. Datos desde `ClientSettings`: teléfono `client.settings.contact_phone` (link `tel:`), ubicación desde el campo de dirección/ciudad disponible en settings — no hardcodear "Maullín".
  4. Alpine.js: ninguna. htmx: ninguna. En móvil puede colapsar a una sola celda (ubicación) u ocultarse (`hidden sm:flex` en la derecha).

- **Resultado:** `utility_bar.html` nuevo, incluido antes de `navbar.html` en `base.html`. Se renderiza siempre con altura fija `h-8` (32px) — aunque el tenant no tenga `address`/`contact_phone` configurados — para que el offset del navbar (ver hallazgo) tenga un valor estable de qué descontar, en vez de dejar un hueco en blanco cuando faltan datos. Ubicación: `client.settings.address` (no `city`, ese campo no existe en `ClientSettings` — ver hallazgo). Teléfono condicional a `contact_phone`, oculto en móvil (`hidden sm:flex`). Fondo `--carbon` vía una clase `.utility-bar` en un `<style>` propio del componente (no inline, mismo criterio que otros componentes del tema); acento del teléfono en `--color-accent`.
  - **⚠️ Hallazgo 1 (premisa de la card ajustada):** `ClientSettings` no tiene un campo `city` separado — solo `address` (TextField). Se usa `address` solo, tal como permite el propio texto de la card ("campo de dirección/ciudad disponible en settings").
  - **⚠️ Hallazgo 2 (coordinación con RC-BOLT-03, real, corregido acá):** la card original no listaba `navbar.html` en "Archivos Afectados", pero el navbar quedó `fixed top-0` en RC-BOLT-03 (ejecutada en esta misma sesión, minutos antes) — sin ajustar su offset, la barra nueva (también fija) habría quedado tapada por el navbar (mismo z-50, el navbar pinta encima por ir después en el DOM). Se cambió `top-0` → `top-8` en `navbar.html` (un solo valor, documentado con comentario) para que ambos se apilen sin superposición. Verificado con `boundingBox()` real vía Playwright: barra `y:0..32`, nav `y:32..110`, sin solapamiento.
  - **⚠️ Hallazgo 3 (pre-existente, NO corregido — fuera de alcance de esta card):** el pill "El oficio" del hero (`hero.html`, `top:26px` dentro de `.shot-a`) queda oculto bajo el header fijo — esto ya pasaba **antes** de las 4 cards de hoy (el navbar ya era `fixed`/opaco con ~78px de alto, más que suficiente para tapar un elemento a 26px) porque `hero.html`/`home.html` nunca reservan espacio para el header fijo (`<main>` no tiene padding-top). El pill "La visita" (`top:90px` + `margin-top:64px` de `.shot-b`) sí queda visible (~154px, por debajo del header). No es un side-effect nuevo de esta card (el pill ya estaba 100% tapado antes de RC-BOLT-02), pero vale una card aparte para revisar el offset del contenido del hero contra el header fijo del tema.
- **Definición de Terminado (DoD Verificable):**
  - [x] Template creado en la ruta indicada respetando `#RC-09` (componente de tema, excepción por diseño único).
  - [x] Cero hex hardcodeados; solo tokens del `:root` del tema (`--carbon`, `--color-accent`).
  - [x] Gate real en verde: 103 tests OK (1 skip), ruff n/a, migraciones limpias. `npx playwright test` 6/6 passed + verificación de `boundingBox()` ad hoc (barra/nav sin solapamiento, no comiteada).
  - [x] Sin side-effects fuera del alcance de la tarjeta más allá del ajuste de offset en `navbar.html`, documentado arriba como necesario para que la propia card funcione visualmente.

---

### ✅ [RC-BOLT-03] Navbar oscura según mockup + CTA "Reservar visita" — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Frontend / Templates
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `templates/ranchocachimba/components/navbar.html`
- **Contexto:** El navbar actual es un clon de Servelec sobre fondo blanco con CTA "Cotizar" (el propio archivo dice "pendiente de diseño final"). El mockup define: fondo `--color-primary`, sticky, links blancos con hover amarillo + subrayado 2px, CTA sólido amarillo "Reservar visita", menú **El Rancho / Experiencias / El Pastor / Visitar**. El mapa de componentes del mockup pide además CTA configurable por tenant — eso aplica al `components/navbar.html` compartido, que este tema hoy **no** consume; queda fuera de alcance (excepción documentada en comentario del archivo, criterio `docs/design-system.md` §2b).

- **Spec ejecutable:**
  1. Restyle del navbar existente conservando su estructura: fondo `var(--color-primary)`, altura ~76px, links `text-white/90` con hover `--color-accent` y `border-b-2` amarillo; preferir utilidades Tailwind sobre el `<style>` inline heredado donde sea posible.
  2. CTA primario: fondo `--color-accent`, texto `--color-primary`, hover `--amarillo-dorado`, texto "Reservar visita" con destino ancla de contacto/reserva (`#contacto` mientras no exista flujo de reserva) — sin hardcodear copy de Servelec.
  3. Menú: anclas a las secciones reales de `home.html` hoy (`#servicios` → "Experiencias", `#about` → "El Rancho", `#contacto` → "Visitar"); "El Pastor" se agrega cuando exista la sección (`#RC-10`) — dejar comentario.
  4. Alpine.js (ya existente, conservar): `x-data="{ mobileMenuOpen }"` para el menú móvil y toggle de sombra on-scroll; adaptar el panel móvil a la paleta oscura. htmx: ninguna.
  5. Estados auth (`Dashboard`/`Iniciar sesión`) se conservan con el nuevo estilo.

- **Resultado:** `bg-primary` + `h-[76px]` en el nav; `.nav-link` pasa a texto blanco/90 con hover+subrayado en `--color-accent` (se simplificó el `::after` de gradiente dos-tonos a color sólido, invisible contra el fondo verde); `.nav-cta` pasa a fondo `--color-accent`/texto `--color-primary`/hover `--amarillo-dorado`/radius 8px, texto "Reservar visita" (desktop y móvil), ancla `#contacto` (comentario explícito: sin flujo de reserva propio todavía). Menú: Servicios→Experiencias, Nosotros→El Rancho, Contacto→Visitar (mismas anclas reales); comentario `{# El Pastor... #RC-10 #}` en vez de agregar un link muerto. Panel móvil, botón hamburguesa, teléfono, divisor, badge de usuario y estados auth adaptados a la paleta oscura (`rgba(255,255,255,.x)` en vez de los grises de Servelec). Alpine (`mobileMenuOpen`, scroll shadow) sin tocar. `npm run build:css` corrido para compilar las combinaciones nuevas de utilidades (`bg-primary`, `text-white/70`, etc.) — no versionado (`static/css/output.css` gitignorado).
- **Definición de Terminado (DoD Verificable):**
  - [x] Navbar renderiza sobre `--color-primary` con menú y CTA del mockup en desktop y móvil (verificado con `npx playwright test`, 6/6 passed, incluye `ranchocachimba-e2e`).
  - [x] Menú móvil Alpine operativo (abrir/cerrar, click-away, transiciones) — sin cambios en la lógica `x-data`/`x-show`/`x-transition`, solo estilos.
  - [x] Gate real en verde: 103 tests OK (1 skip), ruff n/a (solo HTML), migraciones limpias. Sin side-effects fuera del alcance de la tarjeta.

---

### ✅ [RC-BOLT-04] Clase `.tartan` reutilizable + banda hero→stats — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Frontend / Templates
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `templates/ranchocachimba/base.html` (clase en el `<style>` del tema), `templates/ranchocachimba/components/hero.html` (usar la clase en `.seam`), `templates/ranchocachimba/landing/home.html` (banda de 10px entre hero y stats)
- **Contexto:** El patrón de tartán (4 `repeating-linear-gradient` con tokens de marca, cero imágenes) hoy vive inline en la regla `.seam` del hero. El mockup lo usa dos veces (costura vertical + banda horizontal bajo el hero) y su mapa de componentes indica: "va en el CSS del tema, no como componente".

- **Spec ejecutable:**
  1. Mover los gradientes del tartán de `hero.html` a una clase `.tartan` en el bloque `<style>` de `base.html` del tema, usando `var(--color-secondary)`, `var(--tierra)` y `var(--color-accent)` vía `color-mix` (idéntico al actual, pos-RC-BOLT-01).
  2. `hero.html`: `.seam` pasa a `class="seam tartan"` y pierde sus gradientes propios.
  3. `home.html`: insertar `<div class="tartan h-2.5" aria-hidden="true"></div>` entre el include del hero y el de stats.
  4. Alpine.js: ninguna. htmx: ninguna.

- **Resultado:** `.tartan` vive en el `<style>` de `templates/ranchocachimba/base.html` (bloque `{% block theme_styles %}`), con los 4 `repeating-linear-gradient` idénticos a los que antes vivían inline en `.hero-split .seam`. `hero.html` perdió esos gradientes (solo queda un comentario apuntando a `.tartan`) y su `<div class="seam">` pasó a `class="seam tartan"` — `.seam` sigue aportando el sizing (columna de 10px en el grid, `height:10px` en el media query móvil), `.tartan` aporta el patrón. `home.html` suma `<div class="tartan h-2.5" aria-hidden="true"></div>` entre los `{% include %}` de hero y stats.
- **Definición de Terminado (DoD Verificable):**
  - [x] Un solo lugar define el patrón tartán en el tema (`grep -rl repeating-linear-gradient templates/ranchocachimba/` → solo `base.html`).
  - [x] Costura del hero y banda horizontal renderizan (verificado con `npx playwright test`, 6/6 passed, incluye `ranchocachimba-e2e`).
  - [x] Gate real en verde: 103 tests OK (1 skip), ruff n/a (solo HTML), migraciones limpias. Sin side-effects fuera del alcance de la tarjeta.

---

### ✅ [RC-BOLT-05] Franja de stats según mockup (fondo claro, copy rancho) — **DONE (2026-08-23)**
- **Estado:** ✅ DONE (2026-08-23)
- **Componente:** Frontend / Templates
- **Variables requeridas:** ninguna (los números reales dependen de `#RC-01`, insumo del cliente)
- **Archivos Afectados:** `templates/ranchocachimba/components/stats.html`
- **Contexto:** El stats actual es copy de Servelec sin adaptar ("+15 años", "+200 clientes", "100% garantizados") sobre fondo oscuro. El mockup define: fondo `--verde-claro`, 4 celdas alineadas a la izquierda con divisores verticales sutiles, número en Fraunces (`--font-display`) `--color-primary` y label pequeño; copy: "8+ especies para conocer de cerca", "— años criando border collies", "— torneos internacionales", "Maullín · a — min de Puerto Montt". El mapa de componentes propone subirlo a `templates/components/` alimentado por CMS — se pospone: hoy solo Servelec tiene un equivalente y con estructura distinta (3 celdas centradas oscuras); generalizar con los dos layouts sería el "flag más" que §2b evita. Reevaluar cuando un tercer tema lo necesite.

- **Spec ejecutable:**
  1. Reescribir la sección con utilidades Tailwind: `grid grid-cols-2 md:grid-cols-4`, divisores `divide-x` con `--color-primary` al 13%, padding `py-6`; fondo `var(--verde-claro)`, texto secundario en tono verde-grisáceo.
  2. Número: `font-display` (Fraunces del tema) ~38px, `--color-primary`, peso 700; label 12.5px debajo.
  3. Copy provisional del mockup con los "—" como placeholders; marcar con comentario `{# valores reales: #RC-01 #}` (un `{# #}` por línea, regla `#BUG-01`).
  4. Móvil: 2 columnas, sin divisores laterales (como el mockup a <900px).
  5. Alpine.js: ninguna. htmx: ninguna.

- **Resultado:** `grid grid-cols-2 md:grid-cols-4`, fondo `var(--verde-claro)`, divisores al 13% de `--color-primary` (vía un `<style>` propio del componente con selector `#numeros .stats-grid > :not([hidden]) ~ :not([hidden])` — se probó `divide-primary/[0.13]` de Tailwind primero, pero **no compiló ninguna regla** con `--color-primary` definido como `var(...)` plano en `tailwind.config.js`, no como triple rgb; confirmado con `grep` sobre el `output.css` recompilado antes de descartar el enfoque). Número en `font-display` (Fraunces) 38px/700 `--color-primary`; label 12.5px debajo en un verde-grisáceo (`color-mix` entre `--color-primary` y `--gris-texto`). Copy: "8+ especies para conocer de cerca" / "— años criando border collies" / "— torneos internacionales" / "Maullín · a — min de Puerto Montt" — el mockup no distingue explícitamente número de label para la 4ª celda (es una frase de ubicación, no una cifra); se partió en "Maullín" (headline) + "a — min de Puerto Montt" (descriptor) para conservar el mismo ritmo visual de las otras 3 celdas. Cada `—` real lleva su comentario `{# valores reales: #RC-01 #}` en línea propia (`#BUG-01`). Móvil: `grid-cols-2` sin `divide-x` (solo `divide-y` hereda, sin divisores laterales por diseño del breakpoint).
- **Definición de Terminado (DoD Verificable):**
  - [x] Sin copy de Servelec residual en el componente (`grep` de "años de experiencia"/"clientes satisfechos"/"trabajos garantizados" → 0 resultados).
  - [x] Solo tokens del tema (cero hex nuevos); `font-display` (Fraunces), sin serif hardcodeada.
  - [x] Gate real en verde: 103 tests OK (1 skip), ruff n/a, migraciones limpias, `npx playwright test` 6/6 passed. Sin side-effects fuera del alcance de la tarjeta.

---

### [RC-BOLT-06] CTAs del hero: "Reservar visita" + "Ver el pastoreo →"
- **Estado:** TODO
- **Componente:** Frontend / Templates
- **Variables requeridas:** ninguna
- **Archivos Afectados:** `templates/ranchocachimba/components/hero_ctas.html`
- **Contexto:** Los CTAs actuales son copy de Servelec ("Solicitar cotización" / "Ver servicios"). El mockup define: primario sólido amarillo "Reservar visita" (hover `--amarillo-dorado`) y secundario ghost blanco "Ver el pastoreo →" (borde blanco 42%, hover borde+texto amarillo). La generalización de `hero_ctas` a `templates/components/` (existe en `servelec` y `themes/default` → candidato legítimo al caso a de §2a, parámetros: cantidad de botones y estilo del secundario) es una card aparte de alcance multi-tema — proponerla post-lanzamiento, no bloquea Etapa 1.

- **Spec ejecutable:**
  1. Primario: `bg` `var(--color-accent)`, texto `var(--color-primary)`, hover `var(--amarillo-dorado)`, radius 8px, texto "Reservar visita", destino `#contacto` (o ancla de reserva cuando exista).
  2. Secundario: transparente, borde `1.5px` blanco 42%, hover borde y texto `--color-accent`, texto "Ver el pastoreo", destino `#servicios` (sección experiencias; ajustar cuando exista sección/video de pastoreo, `#RC-06b` decide destino de `Animaciondefondo.mp4`).
  3. Mantener el patrón actual de flecha SVG con `group-hover:translate-x-1`.
  4. Alpine.js: ninguna. htmx: ninguna.

- **Definición de Terminado (DoD Verificable):**
  - [ ] Copy y estilos del mockup en desktop y móvil; sin textos de Servelec.
  - [ ] Solo tokens del tema en colores.
  - [ ] Gate real en verde. Sin side-effects fuera del alcance de la tarjeta.

---

## Orden de ejecución sugerido

`RC-BOLT-01` (bloqueante, bug real) → `RC-BOLT-04` (toca el mismo `hero.html`, evita
conflictos) → `RC-BOLT-03` / `RC-BOLT-02` (navbar + barra de utilidad, misma zona) →
`RC-BOLT-05` → `RC-BOLT-06`. Todo es frontend puro: sin migraciones, sin cambios en
vistas ni managers.
