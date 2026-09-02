# Prompt para Stitch — Home Rancho Interactivo Cachimba

**Uso:** pegar en Stitch (MCP) como dirección de arte para redisñar el Home. Es referencia visual, no código de producción — el resultado se reconcilia después contra `docs/design-system.md` y se traduce a los templates reales listados en la sección 6.

**Por qué este prompt es distinto del brief original:** el brief original describía 12 secciones "ideales" de una web de granja/Border Collie que no existen como componentes en este repo (Animales, Transición Border Collie, Información visitantes, Ubicación con mapa). Stitch generaría diseño sin destino de implementación. Este prompt está recortado a los **11 bloques que existen hoy** en `templates/ranchocachimba/`, en su orden real, con su copy y CTAs reales — y usa uno de ellos, hoy sin usar, para resolver el pilar Border Collie sin inventar estructura nueva.

---

## 1. Contexto del negocio (sin cambios respecto al brief original)

Rancho Interactivo Cachimba, Maullín, Chile. Dos líneas de negocio conviviendo en una misma marca:

**A) Rancho interactivo / granja** — cercanía, naturaleza, familia, autenticidad, vida rural. Familiar ≠ infantil: nada de estética de jardín infantil ni zoológico caricaturesco.

**B) Border Collie / crianza y adiestramiento** — el dueño tiene trayectoria y prestigio internacional en crianza, adiestramiento y pastoreo con Border Collie. Debe transmitir autoridad, precisión, conocimiento — no "una sección de perros".

Concepto central: **"Naturaleza + experiencia + animales + Border Collie"**. Ritmo visual, no Hero→Cards→Cards→CTA.

---

## 2. Identidad visual — tokens reales, no a definir

Esta paleta ya está en `templates/ranchocachimba/base.html` como variables CSS (`--color-primary`, `--color-secondary`, `--color-accent`, más fijos de marca). Úsala literal, no la reinterpretes:

| Rol en la interfaz | Nombre | Hex | Variable CSS |
|---|---|---|---|
| Base / navbar / footer / fondos oscuros | Verde Rancho | `#064B20` | `--color-primary` |
| Hover, secciones secundarias | Verde Bosque | `#0B642B` | `--color-secondary` |
| CTA principal, acentos | Amarillo Cachimba | `#FFD500` | `--color-accent` |
| Hover de CTA, bordes | Amarillo Dorado | `#EFB900` | `--amarillo-dorado` |
| Fondos suaves, tarjetas info | Verde Muy Claro | `#EAF4EC` | `--verde-claro` |
| Detalles naturales, madera | Tierra | `#6B4F32` | `--tierra` |
| Texto principal | Carbón | `#172019` | `--carbon` |
| Fondos claros / texto sobre oscuro | Blanco | `#FFFFFF` | `--blanco` |

Distribución: 60% verde/blanco, 30% verde claro/carbón, 10% amarillo. El amarillo nunca es el fondo de una sección completa, solo CTA y acentos puntuales.

**Tipografía ya decidida:** Fraunces (display, títulos — variable `--font-display`) + Inter (cuerpo, navegación — variable `--font-sans`, personalizable por tenant pero Inter es el default de marca). No propongas otra combinación; trabaja el contraste de peso/tamaño entre ambas.

**Elemento de marca ya existente — úsalo como firma visual:** un patrón de "tartán" (clase `.tartan` en `base.html`) hecho con gradientes CSS repetidos en verde/tierra/amarillo, usado hoy como costura entre las dos fotos del Hero y como banda divisoria Hero→Stats. Es la textura distintiva de esta marca — repetirla con moderación (bordes, divisores, detalles) da continuidad sin caer en ilustración.

---

## 3. Dirección artística (sin cambios respecto al brief original)

Natural, rural contemporánea, cálida, profesional, fotográfica, editorial, premium pero cercana.

Evitar: estética infantil, exceso de ilustraciones/iconos/emojis, cards genéricas en cuadrícula de 12, gradientes SaaS, frialdad corporativa, minimalismo que borre la personalidad rural, stock photography evidente.

Fotografía protagonista y documental: animales, Border Collie trabajando, pastoreo, familias interactuando, campo real — no stock genérico.

---

## 4. Logo

Logo oficial como está, sin rediseñar ni recolorear. La interfaz lo complementa, no compite con él.

---

## 5. Jerarquía de CTA — copy ya definido, no genérico

El amarillo (`--color-accent`) es solo para estas acciones, y con este texto exacto donde ya existe implementado (mantenlo; si Stitch propone variantes, que sean estas u otras igual de específicas, nunca "Ver más" / "Conocer más" genérico):

- CTA principal navbar/hero: **"Reservar visita"**
- CTA secundario hero: **"Ver el pastoreo"**
- CTA sección Border Collie (nueva, ver §6.7): **"Conocer el criadero"**
- CTA contacto: **"Escribir por WhatsApp"** (hoy no hay formulario, el canal de contacto real es WhatsApp directo — no diseñes un formulario multi-campo como pieza central de esta sección)

No pintar todos los botones de amarillo — solo estos.

---

## 6. Estructura del Home — los 11 bloques reales, en orden, con su identidad técnica

Diseña **estos bloques, en este orden, sin agregar ni quitar secciones**. Cada uno indica si su contenido es fijo (vos lo diseñás completo) o viene de un CMS (el cliente lo edita — diseñá el contenedor y el patrón de tarjeta/layout, no copy final).

### 6.1 Utility bar (fija, franja superior, h-8)
Fondo carbón (`--carbon`). Ubicación + teléfono de contacto. Discreta, casi invisible, información de trámite rápido antes del navbar.

### 6.2 Navbar (fija, oscura, sobre la utility bar)
Fondo `--color-primary`. Logo a la izquierda. Links: **Experiencias · El Rancho · Visitar** (anclan a servicios/about/contacto — no agregues links a secciones que no existen). CTA amarillo "Reservar visita" a la derecha. Buscá que el link a la futura sección Border Collie (§6.7) tenga un lugar natural en este nav — hoy no está, es la pieza más obvia que falta.

### 6.3 Hero — layout de dos fotos simultáneas, no slideshow
Ya tiene una dirección de arte fuerte, no partas de cero: grid asimétrico, Foto A "El oficio" (pastoreo, más grande) + Foto B "La visita" (familia/granja, más chica, desplazada) con costura de tartán entre ambas. Bloque de texto sólido en verde invade la Foto A desde abajo-izquierda: eyebrow ("Rancho Interactivo · Maullín"), título fuerte, bajada corta, los dos CTA de hero.

Lo que sí podés proponer mejor: la composición exacta del bloque de texto, el tratamiento de los "pills" de etiqueta sobre cada foto ("El oficio" / "La visita"), y cómo se resuelve en mobile sin perder impacto (hoy apila las fotos y el texto pasa a estático debajo — proponé algo mejor si lo tenés).

### 6.4 Banda de stats (fondo claro `--verde-claro`)
4 celdas alineadas, divisores verticales sutiles: especies para conocer, años criando Border Collies, torneos internacionales, ubicación (Maullín, minutos de Puerto Montt). Esta franja ya mezcla los dos pilares del negocio en una sola fila — es la primera señal de que "esto no es solo una granja".

### 6.5 Servicios / "Experiencias" (CMS — 3 a 5 tarjetas dinámicas)
El cliente carga 3-5 experiencias desde el panel (nombre, foto, descripción corta y larga, precio). Hoy el layout es grilla de cards con foto que se expande a un panel de detalle al hacer clic. Diseñá el patrón de tarjeta y el layout de grilla (el brief original pedía evitar "cuadrícula genérica" — proponé asimetría o tamaños variables que sigan funcionando con 3, 4 o 5 ítems, que es el rango real de contenido) y el patrón del panel de detalle expandido. No diseñes contenido final de las tarjetas, son datos del cliente.

### 6.6 "El Rancho" / About (CMS — imagen + texto)
Layout partido: imagen grande (con marcos decorativos en los 3 colores de marca, ya como firma visual) + columna de texto con eyebrow "Sobre nosotros", título, bajada, descripción y CTA a contacto. El cliente edita título/imagen/texto desde el CMS — diseñá el contenedor, no el copy.

### 6.7 Border Collie — reutilizar `why_us.html`, hoy sin usar
**Este es el bloque que resuelve el pilar B del negocio, y ya existe en el código pero no está conectado al Home ni tiene copy propio** (dice literalmente "Pilar 1-4, pendiente de redacción", clonado de otro cliente). Es tu oportunidad real de diseñar la "gran sección Border Collie" que pedía el brief original, sin inventar estructura nueva.

Layout ya construido: fondo `--color-primary` sólido (transición de "familiar" a "profesional" por contraste de color, tal como pedía el brief original), columna izquierda sticky en desktop (eyebrow + título fuerte + bajada + CTA), columna derecha con 4 pilares numerados (01-04) con línea divisoria.

Lo que tenés que diseñar de verdad:
- Redacción y jerarquía de los 4 pilares (candidatos de contenido: crianza, adiestramiento, pastoreo/trabajo, trayectoria/prestigio internacional — ajustables).
- Si el layout de "4 pilares en lista numerada" es la mejor forma de transmitir autoridad y trayectoria, o si proponés una variante (ej. imagen grande de Border Collie trabajando + los pilares como overlay/bloque editorial) — acá sí hay espacio para repensar el layout, es la sección con más peso narrativo del sitio.
- CTA de esta sección: "Conocer el criadero".
- Tipografía de mayor impacto, más espacio negativo, composición más sobria que el resto del sitio — así se diferencia visualmente de la parte "granja familiar".

### 6.8 Galería (condicional — CMS, grid de fotos)
Solo se renderiza si el cliente tiene fotos activas. Grid de fotos reales (hoy con placeholders), usando el componente compartido `media_collection.html` en modo grid de 3 columnas. Diseñá el patrón de grilla/hover, no un carrusel nuevo — el componente base ya es compartido entre temas.

### 6.9 CTA final (fondo `--color-primary`, banda oscura)
"¿Listo para conocer Rancho Cachimba?" + CTA a contacto + teléfono como alternativa. Sección corta, de cierre, antes de contacto.

### 6.10 Contacto (fondo blanco)
Dos columnas: izquierda con datos de contacto (email, teléfono, dirección) como tarjetas; derecha con **CTA de WhatsApp como acción central** (no un formulario — el canal real de este cliente en esta etapa es WhatsApp directo). Diseñá esa tarjeta de WhatsApp como la pieza fuerte de la sección, no como un botón secundario perdido.

### 6.11 Footer (fondo `--color-primary`)
Marca + descripción + redes sociales | Navegación | Ubicación (Maullín · Región de Los Lagos). 3-4 columnas, estándar, sin necesidad de rediseño ambicioso — es la sección de menor peso narrativo del sitio.

---

## 7. Lo que NO pidas a Stitch

- No diseñes una sección "Animales" nueva tipo grid de exploración — no existe como componente; si querés esa idea, sugerí incorporarla como contenido dentro de Servicios/Experiencias (§6.5), no como bloque nuevo.
- No diseñes una sección de "Ubicación" con mapa embebido — la ubicación hoy vive en utility bar + stats + footer, repartida a propósito, no concentrada.
- No diseñes un formulario de contacto multi-paso — el canal real es WhatsApp (§6.10).
- No rediseñes el logo ni cambies los hex de marca.

---

## 8. Responsive

Desktop primero, con adaptación real a mobile — no solo apilar. Casos concretos que ya tienen una resolución en código y que podés mejorar pero no ignorar:
- Hero: las dos fotos pasan de lado-a-lado a apiladas, el bloque de texto pasa de overlay a bloque estático debajo.
- About: la columna de imagen y la de texto invierten orden en mobile (imagen primero visualmente en desktop vía `order-2`/`order-1`, ajustado en mobile).
- Border Collie (§6.7): la columna sticky no aplica en mobile — necesita una resolución propia si cambiás el layout.

---

## 9. Resultado esperado

Prioridades en este orden: identidad de marca → fotografía → jerarquía visual → diferenciación Granja/Border Collie → profesionalismo → UX → responsive → consistencia de color.

El resultado debe sentirse como una sola marca contando dos historias con el mismo lenguaje visual — no dos sitios pegados. El punto de inflexión entre ambas es el bloque 6.7: hoy existe en el código pero está vacío de contenido y de dirección de arte propia. Resolver bien ese bloque es, en la práctica, resolver el pedido central de este brief.

---

## 10. Instrucciones Específicas de Layout y Componentes para Stitch

1. **Patrón del Tartán (`.tartan`):** 
   - Utilízalo como un borde decorativo inferior de 4px en la Utility Bar o como divisor visual de 8px entre el Hero y la Banda de Stats.
   - En el Hero, aplícalo como el conector/costura entre la Foto A (Pastoreo) y la Foto B (Familia).

2. **Resolución Mobile del Hero:**
   - En viewport móvil (< 768px), transforma el layout de 2 fotos a un contenedor único con la Foto A de fondo (overlay oscuro al 40%), la Foto B encajada como una card flotante miniatura en la esquina inferior derecha, y el bloque de texto posicionado sobre la foto principal para reducir el scroll vertical.

3. **Layout para Bloque 6.7 (Border Collie / `why_us.html`):**
   - Usa la columna izquierda (sticky en desktop) con fondo `--color-primary` y texto en `--blanco` con la tipografía `--font-display` (Fraunces) en peso semi-bold para el título.
   - Para los 4 pilares de la columna derecha, diseña tarjetas con fondo `--color-secondary` al 20% de opacidad, bordes finos en `--tierra`, y números "01-04" destacados en `--color-accent` (Amarillo Cachimba) usando la fuente Fraunces.

4. **Tratamiento del CTA de WhatsApp (Sección 6.10):**
   - Destaca la tarjeta de WhatsApp como el elemento principal mediante un contenedor con fondo `--verde-claro`, un borde izquierdo prominente de 6px en `--color-accent`, e iconería clara de canal directo, evitando la apariencia de un simple formulario de correo.