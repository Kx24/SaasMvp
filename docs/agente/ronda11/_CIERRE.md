# Cierre documental (común a todas las cards de la ronda 11)

Va en el mismo cambio que el código. Tres ediciones, nada más:

1. `Documentacion/KANBAN_PROYECTO.md`: borra la fila de la card maestra de su tabla (o acótala si
   el spec dice "parcial"). Si la card aparece en las tablas del "Plan de ejecución", deja el ID
   pero agrégale ` ✅`. No reescribas otras secciones ni "Retomar aquí".
2. `Documentacion/historico/KANBAN_HISTORICO.md`: agrega **una línea** al final de la sección de
   cards cerradas que corresponda al prefijo, con el formato de las líneas vecinas:
   `- **\`<MAESTRA>\` <título>** (<fecha de hoy, AAAA-MM-DD>, \`BOLT-XX\`): <qué quedó hecho, una frase>.`
3. Si descubriste un hallazgo incidental que **no** arreglaste, agrégalo como fila nueva en la
   tabla del prefijo que corresponda en `KANBAN_PROYECTO.md` (ID siguiente libre, prioridad y
   esfuerzo estimados, "Hallado por `BOLT-XX`").

No toques `docs/kanban_agente.md` (histórico de las rondas 1–3) ni `docs/agente/` (el estado de
la ronda lo escribe el orquestador).

**Cards "parte N de M" de una misma maestra:** solo la última borra la fila del kanban; las
anteriores la acotan (actualizan los números o lo que falta) y anotan `<MAESTRA> (parte)` en el
histórico.

---

# Contrato común de las cards `COMP-01` (generalizar un componente)

Aplica a toda card de esta ronda cuya maestra sea `COMP-01`. Lee antes `docs/design-system.md`
(contrato de componentes) y el precedente `templates/components/media_collection.html`
(parámetro `mode` + slots de override por ruta de plantilla, `templates/components/slots/`).

1. **Una sola implementación** en `templates/components/<nombre>.html`. Las variantes entre temas
   se expresan con parámetros (`{% include … with mode='…' %}`) y con *slots*: fragmentos que el
   tema sobreescribe por ruta (`templates/<tema>/components/slots/<nombre>_<slot>.html`), resueltos
   por `TenantTemplateLoader` con fallback al slot por defecto.
2. El archivo del tema (`templates/<tema>/components/<nombre>.html`) queda como **envoltorio
   fino** (un `{% include %}` con sus parámetros) o desaparece si el `home.html` del tema puede
   incluir el compartido directamente. Nada de copiar y pegar el marcado.
3. **El HTML que ve el visitante no cambia.** Antes de tocar nada, guarda como *fixture* el HTML
   renderizado del componente en cada tema que lo usa (`themes/default`, `themes/servelec`,
   `andesscale`), normalizando espacios; después del cambio, un test compara el render nuevo con
   esa fixture. Diferencias aceptables: solo espacios en blanco. Cualquier otra diferencia se
   corrige o, si es una mejora inevitable (por ejemplo un atributo de accesibilidad que faltaba en
   un tema), se lista una por una en `revisar_humano`.
4. Marca por tokens: colores y fuentes salen de las CSS custom properties de `ClientSettings`;
   ningún color de marca escrito a mano. Utilidades Tailwind, sin `style=""` en línea nuevo. La
   guardia `apps/core/tests/test_theme_token_contract.py` sigue verde sin editarla.
5. No se toca `templates/themes/ranchocachimba/` ni la rama de Rancho Cachimba.
6. Verde obligatorio: tests de render por tema (`apps/website/tests/test_home_render.py`),
   Playwright (`smoke` y `a11y`) y la suite completa.
7. En `revisar_humano`: "revisar en el navegador la sección <nombre> en Servelec, en el tema base
   y en andesscale", más las diferencias de HTML aceptadas.
