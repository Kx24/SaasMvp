# Procedimiento: cómo afrontar diseño de frontend

Leer esto **al empezar** una sesión de trabajo visual/de diseño (hoy el caso real es Rancho Cachimba, `#RC-09` en adelante — landing por componente, sección por sección). No reemplaza `docs/design-system.md` (el contrato técnico: qué token, qué componente reusar) — este documento es el *proceso* para llegar a ese contrato desde una inspiración suelta, no el contrato en sí.

> Precedente real que ya funcionó con este mismo método: `#RC-20` (hero de Rancho Cachimba). Mockup → spec escrita (`Documentacion/Planificación/spec_bolt_hero_cachimba.md`) analizada contra `docs/design-system.md` → 6 cards atómicas (`RC-BOLT-01..06`) → implementadas con TDD. Cerraron las 6 sin retrabajo. Este documento generaliza ese método para que no haya que re-derivarlo cada vez.

---

## 0. Qué traer a la sesión

El usuario llega con **insumos crudos**, no con un brief formal: links de páginas de referencia, recortes/capturas de pantalla, screenshots de componentes o animaciones que le gustaron. Eso es exactamente lo que hace falta — no hace falta que vengan organizados. El trabajo de las fases 1-2 de abajo es justamente convertir eso en algo accionable.

Si el insumo es *"me gustó cómo hace esto tal sitio"* sin captura ni link, primer paso: usar `claude-in-chrome` para ir a verlo juntos ahí mismo, en vivo, en vez de trabajar de memoria.

---

## 1. Las herramientas, y qué rol cumple cada una (no se solapan)

| Herramienta | Rol | Estado |
|---|---|---|
| `claude-in-chrome` (skill) | Navegar sitios de referencia, capturar screenshots, leer estructura/CSS de una página real. Es el punto de entrada para "quiero que se vea como X". | ✅ Disponible |
| `frontend-design` (plugin, marketplace oficial `claude-plugins-official`) | Metodología de dirección de arte: obliga a elegir paleta/tipografía/layout deliberados en vez de caer en los 3 looks genéricos que produce cualquier IA por default (crema+serif+terracota / negro+acento ácido / broadsheet con hairlines). Proceso propio: brainstorm de un token system (color/tipo/layout/signature) → crítica contra el brief → recién ahí construir. | ⏳ Pendiente instalar (`/plugin install frontend-design@claude-plugins-official`) — verificar que cargó antes de asumir que está activo |
| `docs/design-system.md` | El contrato **técnico** de este repo: qué variables CSS son obligatorias, cuándo un componente nuevo debe generalizarse a `templates/components/` vs quedar como excepción de tema (`ranchocachimba/components/hero.html` ya es el precedente real de "layout distinto, no generalizar"). Toda idea de la fase 2 pasa por acá antes de volverse una card. | ✅ Disponible |
| `/design` (skill de Claude Code) | Canvas de mockup, editable a mano, publicado como Artifact — para materializar visualmente una dirección ya elegida y iterarla con el usuario antes de tocar código real. | ✅ Disponible |
| Playwright (`@playwright/test`, ya en el repo) | **No es para inspiración.** Está armado para testear contra el dev server local de este proyecto (`playwright.config.js`), incluido el gate de accesibilidad real desde `#DS-03` (`tests/e2e/a11y.spec.js`, `@axe-core/playwright`). Se usa en la fase 5 (verificación), no en la 1-2. | ✅ Disponible, ya integrado al gate |

---

## 2. El flujo, fase por fase

### Fase 1 — Inspiración concreta, no vibes
Con `claude-in-chrome`: visitar cada referencia que trae el usuario, screenshot de lo puntual que le gustó (no "el sitio entero" — el hover de esa card, esa transición de scroll, esa combinación tipográfica). Anotar **qué** de cada referencia es lo que importa; una lista de 3-4 elementos concretos vale más que 10 capturas sin comentar.

### Fase 2 — Dirección de arte (con `frontend-design` si ya está instalado)
Tomar las referencias de la fase 1 + el brief real (para Rancho Cachimba: turismo rural, pastoreo con perros ovejeros, Maullín, Región de Los Lagos — el "mundo" del cliente, no una plantilla de "sitio rural genérico"). Producir un token system compacto: 4-6 hex con nombre, 2+ tipografías con rol, un concepto de layout en prosa + wireframe ASCII, y el "elemento firma" — la única cosa por la que se va a recordar esta pieza. Criticarlo contra el brief antes de seguir: si algo de la propuesta es el default genérico que saldría para cualquier brief similar, revisar esa parte.

Si `frontend-design` todavía no está instalado, este paso se hace igual pero a pulso — la vara sigue siendo "¿esto es una elección deliberada para Rancho Cachimba, o el default que pondría para cualquier sitio rural?".

### Fase 3 — Reconciliar contra `docs/design-system.md`
Acá es donde la dirección de arte se vuelve implementable. Preguntas obligatorias:
- ¿La diferencia entre esto y lo que ya existe es de *estilo* (colores, tipografía, efectos) → slot de override sobre un componente compartido (`media_collection.html`, `hero_ctas_base.html`)? ¿O es de *estructura* (otra grilla, otro número de elementos) → componente propio del tema, documentado como excepción explícita (precedente: `ranchocachimba/components/hero.html`)?
- ¿Qué token CSS nuevo hace falta? Si es de marca (color/fuente), va a `ClientSettings` — nunca hardcodeado (la guardia estática de `#BOLT-06`, `apps/core/tests/test_theme_token_contract.py`, lo va a atrapar igual si se hardcodea sin fallback).
- ¿Ya existe un componente equivalente en 2+ temas que debería generalizarse en vez de duplicarse?

Este es el paso que en `#RC-20` encontró que la cita "`hero` con variante `layout: single|split`" no existía en el código — verificar contra el código real, no contra lo que dice la documentación vieja, es parte del método, no un extra.

### Fase 4 — Spec escrita → cards atómicas
Mismo formato que `Documentacion/Planificación/spec_bolt_hero_cachimba.md`: un documento que analiza el mockup/dirección contra el contrato técnico, documenta qué propuestas se rechazan y por qué, y termina en una lista de cards atómicas — cada una con alcance chico, DoD claro, y numeradas `RC-BOLT-NN` (para no chocar con los `BOLT-NN` de `docs/kanban_agente.md` en `agent/ai-dlc-pilot`, que por regla `§0.4` no toca nada de Rancho Cachimba).

### Fase 5 — Implementar con el mismo gate de siempre
TDD (rojo confirmado antes del fix), `ruff check` en los archivos tocados, suite Django completa, `npx playwright test` — que desde `#DS-03` incluye el gate de accesibilidad real (`WCAG2A/AA` vía `axe-core`, 0 violaciones exigido). Cualquier componente nuevo que use texto sobre `var(--color-primary)`/`bg-primary` en fondo claro: usar `.text-primary-a11y`/`.bg-primary-a11y` (`static/css/input.css`, agregadas en `#DS-03`) en vez de las utilidades crudas — el color de marca del tenant no garantiza 4.5:1 por sí solo.

---

## 3. Checklist de inicio de sesión

1. Leer este documento (ya hecho si estás leyendo esto).
2. Confirmar branch: `feature/RanchocachimbaEtapa1` — nada de esto se toca desde `develop` ni desde `agent/ai-dlc-pilot`.
3. Revisar `Documentacion/KANBAN_PROYECTO.md` §"Retomar aquí" y la card `#RC-09` (o la que corresponda) para el estado más reciente.
4. Confirmar si `#RC-01` (inventario de material del cliente) y `#RC-06b` (fotos reales, hoy con placeholders `zar.jpeg`/`FotoGaleria.jpeg`) ya tienen insumos nuevos — siguen siendo el bloqueador real para publicar, no el diseño en sí.
5. Reunir lo que trae el usuario (fase 0) y arrancar en fase 1.

---

## 4. Guardrails específicos de este repo

- **Utilidades Tailwind sobre `style=""` inline** en templates nuevos (preferencia explícita del usuario, ya en `CLAUDE.md`).
- **No generalizar con un flag más** cuando la diferencia es estructural — es el anti-patrón que `#AUD-11` vino a sacar (el `tailwind.config` duplicado, dos veces la misma paleta sin referenciarse). Excepción documentada explícita > componente con 5 flags.
- **Nada de esto toca `agent/ai-dlc-pilot`** — ese piloto tiene prohibido por regla propia (`§0.4` de `docs/kanban_agente.md`) tocar cualquier cosa de Rancho Cachimba. Los `BOLT-*` de plataforma que salgan de un análisis de diseño (como pasó con `#RC-20` → `BOLT-06..08`) se separan a mano, no los ejecuta el piloto.
- **Comentarios Django `{# ... #}` nunca cruzan un salto de línea** (`#BUG-01`) — partir en uno por línea, sin excepción, en cualquier template nuevo.
- **El hallazgo pendiente de `#RC-20`** (el pill "El oficio" tapado bajo el header fijo) sigue sin card propia — si el trabajo de esta sesión toca el offset del contenido bajo el header, es buen momento para resolverlo de paso.
