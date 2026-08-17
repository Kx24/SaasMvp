# Tablero A — Rancho Interactivo Cachimba · hasta publicación

> **Estado:** PLAN — pendiente de aprobación. Ningún archivo del repo fue modificado.
> **Cliente:** Rancho Interactivo CACHIMBA · Maullín, Región de Los Lagos.
> **Slug propuesto:** `rancho-cachimba` · **Tema propuesto:** `rancho` · **Rubro:** `turismo_rural`
> **Cobro:** fuera de plataforma (transferencia/factura). Observaciones → Tablero B `#PAY-02`.
> **Ejecución:** el desarrollo se hace desde **Claude Code sobre el repo**. Toda ruta de este tablero es relativa a la raíz del proyecto, y todo insumo de diseño vive versionado en el repo — no en historiales de chat.
> **Actualizado:** 17-08-2026 · v2

---

## Qué cambió respecto de la v1

| | v1 | v2 |
|---|---|---|
| Identidad | por definir | **entregada por el cliente**: logo, favicon y guía de color |
| Paleta | propuesta mía (#2F4536 / ocre) | **descartada**. Manda la guía oficial |
| Material | por conseguir | comprimido recibido, suficiente para una v1 operativa |
| Hero | por decidir | **decidido**: dos fotos, granja + pastoreo |
| Enfoque | landing completa | **MVP por etapas**, sobre componentes reutilizables |
| Entorno | Cowork | **Claude Code sobre el repo** |
| Referencias de diseño | sueltas | **`LinkRevisar.md` versionado** |

---

## Convención nueva: `LinkRevisar.md`

**Ruta:** `Documentacion/clientes/rancho-cachimba/LinkRevisar.md`

Archivo de referencias que alimenta toda la etapa de definición de diseño. **Ninguna referencia entra al diseño sin pasar por aquí.** Existe por una razón concreta: si el desarrollo se hace desde Claude Code en la terminal, el agente tiene que poder leer las referencias desde el repo — no sirve que vivan en el historial de un chat que la próxima sesión no ve.

**Formato de cada entrada:**

| Link | Qué se toma | Aplica a | Estado |
|---|---|---|---|
| `url` | la idea específica, no "me gusta" | componente o sección concreta | por revisar / aprobado / descartado |

Dos reglas que hacen que el archivo sirva de verdad:

1. **Cada entrada nombra el componente que afecta.** Así el archivo alimenta directo el trabajo de librería de componentes en vez de quedar como un moodboard decorativo.
2. **Lo descartado se queda, con el motivo.** El valor de "por qué no" es mayor que el de "por qué sí" — evita volver a proponer lo mismo en el cliente siguiente.

**Cards que lo consultan y lo actualizan:** `#RC-04` · `#RC-06` · `#RC-07` · `#RC-09` · `#RC-19`.

---

## Lectura del cliente

Dos productos distintos, públicos y tickets distintos:

| Producto | Público | Qué vende |
|---|---|---|
| Granja interactiva (ciervos, pavos, gallinas, burros, perros) | Familias, colegios, cumpleaños | Contacto con animales |
| Pastoreo con border collies | Turismo de experiencia, criadores, medios | **Autoridad**: un pastor que compite internacionalmente |

**El pastor es el activo diferenciador** y el sitio debe funcionar además como su carta de presentación. El logo ya resuelve la dualidad: ciervo y border collie conviven en la marca.

**Consecuencia técnica:** sitio intensivo en media. Eso lo pone encima de los dos bugs de galería abiertos → `#RC-02` es gate, no trámite.

---

# Etapa 1 · Hero operativo (reemplaza "en construcción")

> Objetivo: que el cliente vea algo real andando esta semana. Nada de esta etapa se rehace después.

### `#RC-01` — Inventario del material del cliente
Descomprimir y catalogar: qué fotos hay, cuáles sirven, qué resolución, qué falta. Cruzar contra las dos fotos que el hero necesita (pastoreo en faena · visitante con animal).
**Lo que igual hay que pedir al cliente:** horarios, precios o política de precios, dirección exacta y coordenadas, teléfono/WhatsApp, correo real de destino, nombre del pastor y sus torneos, nombres de los perros.
**DoD:** inventario en `Documentacion/clientes/rancho-cachimba/brief.md` con lista explícita de qué falta y quién lo consigue (cliente o diseñador gráfico).

### `#RC-02` — Gate de riesgo: galería y Cloudinary — **DONE (2026-08-17)**
Reproducir el `AttributeError` de `GalleryItem.get_background_image_url()` con datos de Servelec y auditar las claves duplicadas de `CLOUDINARY_PRESETS`.
**Por qué ahora:** el hero de dos fotos necesita **dos slots de media** donde el patrón CDCA hoy resuelve uno.
**DoD:** veredicto explícito — "el hero de dos slots se puede construir" o "hay que adelantar `#DEUDA-02`".
**Bloquea:** `#RC-05`.

**Resultado:**
- Reproducido en `manage.py shell` con datos reales de Servelec: `AttributeError: 'GalleryItem' object has no attribute 'background_image'`. Causa: el método era copy-paste del de `Section` (que sí tiene ese campo); `GalleryItem` solo tiene `image`. No lo llamaba nada en producción (solo `Section.get_background_image_url` / `section.get_background_image_url` están en uso, y esos funcionan bien) — era código muerto pero roto. **Eliminado** de `apps/website/models.py`.
- `CLOUDINARY_PRESETS` (`apps/core/cloudinary_utils.py`) tenía `gallery_card`/`gallery_full` definidos dos veces (bloque "GALERÍA" y bloque "HEROGALLERY" debajo); el segundo pisaba al primero en silencio. Consolidado en una sola definición: `gallery_full` con `crop:'limit'` (coincide con lo que ya documentaba `GalleryItem.get_image_url()`: *"gallery_full → 1920×1080, limit... (hero/lightbox)"*) y `fetch_format:'auto'` en vez de `format:'auto'`, siguiendo la convención del resto del archivo (el propio comentario de `get_cloudinary_url()` advierte que `fetch_format` mal puesto genera URLs con `.auto` al final). Esto también resuelve `#DEUDA-01` del Tablero B.
- Verificado sin regresión: `Section.get_background_image_url()` sigue generando URL correcta, `GalleryItem.get_image_url('gallery_full')` genera URL limpia con el preset consolidado, `check_tenant_setup ranchocachimba` sigue en `[OK]` tema/dominio.

**Veredicto del gate:** el hero de dos fotos **se puede construir sin adelantar `#DEUDA-02`**. Hoy no existe un mecanismo de "dos slots simultáneos" (`Section.background_image` es un slot único; el slideshow de `GalleryItem` con `gallery_type='hero'` rota por ese mismo slot, uno a la vez) — pero el layout split de Cachimba no necesita ese mecanismo genérico: alcanza con que el componente `hero.html` de `ranchocachimba` tome directamente los dos primeros `GalleryItem` (`gallery_type='hero'`, ordenados por `order`) y los renderice lado a lado. `#DEUDA-02` (pool único de imágenes reutilizable entre hero/servicio/galería, con migración de datos) queda como mejora futura, no como bloqueador de `#RC-06`.

### `#RC-03` — Tokens de la guía oficial — **DONE parcial (2026-08-17)**
Cargar la paleta entregada en `ClientSettings` como custom properties: `#064B20` Verde Rancho · `#0B642B` Verde Bosque · `#FFD500` Amarillo Cachimba · `#EFB900` Amarillo Dorado · `#FFFFFF` · `#EAF4EC` Verde Muy Claro · `#6B4F32` Tierra · `#172019` Carbón. Proporción 60/30/10.
Subir logo y favicon a `tenants/rancho-cachimba/branding/`.
**Tipografía propuesta:** Fraunces (display) + Inter (cuerpo).
**DoD:** tokens en el tenant de desarrollo, cero hex hardcodeados en el tema.

**Resultado:**
- `ClientSettings` solo tenía `primary_color`/`secondary_color` — `templates/ranchocachimba/base.html` ya referenciaba un `accent_color` que **no existía en el modelo** (lookup silencioso a `''`, siempre caía al fallback hardcodeado). Se agregó el campo `accent_color` (migración `0018_clientsettings_accent_color`, aplicada en dev) y se completó la lectura que el template ya intentaba hacer.
- División de la paleta: **3 colores de identidad** (`primary`/`secondary`/`accent` = Verde Rancho/Verde Bosque/Amarillo Cachimba) quedaron en `ClientSettings` — configurables por tenant, ya seteados en dev (`#064B20`/`#0B642B`/`#FFD500`). Los **5 tonos restantes** (Amarillo Dorado, Blanco, Verde Muy Claro, Tierra, Carbón) quedaron como custom properties fijas en `templates/ranchocachimba/base.html` — no tiene sentido hacerlos configurables por tenant en un theme de un solo cliente, y así el `:root` del theme queda como única fuente de verdad. Se agregaron también 2 tokens neutros de UI (`--gris-texto`, `--gris-borde`) para poder eliminar los grises sueltos que no son parte de la guía de marca.
- **Cero hex hardcodeados**: se auditaron y reemplazaron por `var(--token)` (o `color-mix()` para las variantes con opacidad) todos los hex/rgba sueltos heredados del clonado de Servelec — 12 archivos de `components/`, más los `rgba(15,68,26,...)` del propio `base.html`. Verificado con `grep` (cero coincidencias) y renderizando la home real: los únicos hex que quedan en el HTML servido son exactamente los 8 definidos una vez en `:root`.
- **Tipografía**: se agregó `{% block fonts %}` con Fraunces + Inter (antes el theme heredaba Inter+Outfit del `base.html` global sin nunca cargar Fraunces, pese a que RC-16 ya lo proponía). `font-display` y `.nav-cta` actualizados de `'Outfit'` a `'Fraunces'`.
- Verificado sin regresión: `check_tenant_setup` en `[OK]` para `ranchocachimba` y `servelec`, home de `ranchocachimba` renderiza 200 OK con el theme real (temporalmente fuera de `mode_under_construction` solo para la prueba, revertido al terminar).

**Corrección (2026-08-17):** el logo **ya estaba subido** en `ClientSettings.logo` (`branding/jnqcfp8cm5leo6zet7tf`) — la nota anterior de "sin branding" era incorrecta, no se verificó la BD antes de escribirla. Sigue pendiente: `favicon` y `logo_footer` (ambos `None` hoy) y las fotos/video del hero (`GalleryItem` en `gallery_type='hero'`: 0 registros) — el cliente ya entregó ese material (fotos y videos), falta subirlo. Eso es `#RC-01`/`#RC-06`, no bloquea el resto de `#RC-03`.

### `#RC-04` — Crear y poblar `LinkRevisar.md`
Consolidar todas las referencias visuales con el formato de arriba. Incluye lo ya conversado: toque escocés, *Babe*, afiche de sheepdog trials.
**Decisión ya tomada, registrarla aquí:** lo escocés entra **por textura, no por color** — un tartán tejido con los propios hex de la marca (`#064B20` × `#0B642B` × `#6B4F32` con hilo `#FFD500`). Es CSS puro, sin imágenes, y el diseñador gráfico lo puede exportar como patrón para redes.
**DoD:** archivo creado, commiteado, con al menos 8 entradas clasificadas y cada una apuntando a un componente.

### `#RC-05` — Registrar tema y rubro en el sistema — **DONE (2026-08-17)**
- `Client.THEME_CHOICES` necesita el valor `rancho` → **requiere migración** (precedente `0015`).
- `TEMPLATE_CONFIGS` necesita el rubro `turismo_rural`.
- Decidir si el seed sigue en código o pasa a `seed_data.json` — hoy `templates_library/` solo tiene `.gitkeep`.

**DoD:** `provision_tenant --industry turismo_rural --theme rancho` corre sin error en local.
**Bloqueado por:** `#RC-02`, `#RC-03`.

**Resultado:**
- **El tema ya estaba registrado, con otro nombre.** El trabajo previo a este plan v2 (rama anterior, commit "Crea el theme dedicado `templates/ranchocachimba/`") ya había agregado el tema a `Client.THEME_CHOICES` como `'ranchocachimba'` (no `'rancho'` como asumía esta card) y el `Client` real ya apunta ahí (`client.template == 'ranchocachimba'`). No se renombró — hacerlo ahora sería una migración de datos sin beneficio real, y `'ranchocachimba'` es más específico que `'rancho'`. El DoD se corrió con el valor real: `provision_tenant --theme=ranchocachimba` (no `--theme=rancho`).
- **`TEMPLATE_CONFIGS['turismo_rural']` agregado** en `apps/tenants/management/commands/provision_tenant.py`, con 4 servicios semilla reflejando la lectura del cliente (Granja Interactiva, Pastoreo con Border Collies, Visitas de Colegios, Eventos y Cumpleaños) y los colores oficiales (`primary`/`secondary`/`accent` = Verde Rancho/Verde Bosque/Amarillo Cachimba).
- De paso, `_apply_template_config()` ahora también aplica `accent_color` si el diccionario de colores lo trae (antes del `#RC-03` ese campo no existía en el modelo; `provision_tenant` seguía sin tocarlo aunque ya se había agregado — quedó cerrado el circuito).
- **Decisión sobre el seed:** se queda en código (`TEMPLATE_CONFIGS`), no se migra a `seed_data.json`. Es un solo tenant nuevo, la carpeta `templates_library/` no tiene infraestructura real de carga (`.gitkeep` únicamente), y las otras 4 industrias ya siguen el mismo patrón — introducir un segundo mecanismo de seed ahora sería una migración de arquitectura más grande de lo que este cliente necesita.
- **Verificado sin efectos secundarios:** DoD corrido contra un tenant descartable (`rc-test-turismo`, creado y eliminado en la misma sesión) — `provision_tenant rc-test-turismo --industry=turismo_rural --theme=ranchocachimba` corrió sin error, `check_tenant_setup` salió `[OK]` en tema, colores (`#064B20`/`#0B642B`/`#FFD500`) aplicados correctamente. No se tocó el `Client` real de `ranchocachimba`.

**Corrección de contexto (aviso del usuario):** el material del cliente (fotos y video) ya está disponible, y el logo **ya estaba cargado** en `ClientSettings` antes de esta card (`branding/jnqcfp8cm5leo6zet7tf`) — la nota de "sin branding" en `#RC-03` estaba desactualizada, corregida ahí mismo. Sigue pendiente subir ese material a `GalleryItem` (`gallery_type='hero'`, hoy 0 registros) — eso es `#RC-06`, no esta card.

### `#RC-06` — Hero de dos fotos: construcción — **DONE con material de prueba (2026-08-17)**
Composición aprobada: **asimétrica**, no 50/50 — pastoreo dominante con tratamiento contrastado, granja más chica y desplazada, costura de tartán entre ambas. Bloque de texto sólido que invade la foto izquierda.
**Consulta:** `LinkRevisar.md`.
**DoD:** hero renderizando con `?tenant=rancho-cachimba` en local, con las fotos reales del cliente.
**Bloqueado por:** `#RC-05`.

**Resultado:**
- `templates/ranchocachimba/components/hero.html` reescrito por completo: dejó de usar el slideshow genérico compartido (`components/media_collection.html`) y ahora es un layout **split** propio del theme — grid asimétrico `1.32fr 10px 1fr`, foto B desplazada verticalmente, costura de tartán en CSS puro (4 `repeating-linear-gradient` con los tokens de marca, sin imágenes), bloque de texto sólido invadiendo la foto A. Servelec sigue con el slideshow de siempre, sin tocar — tal como pedía el mockup aprobado ("Cachimba estrena split; Servelec sigue en single").
- Se agregó `get_hero_split_media()` en `website_tags.py` — tag independiente de `get_hero_images()` (que sigue sirviendo el slideshow de los demás temas) para no arriesgar esa lógica compartida. Devuelve exactamente 2 slots (`GalleryItem` o `None`), sin la semántica de "slide default" que no aplica a un layout de dos fotos fijas.
- Se agregó el preset `hero_split` (recorte 3:4, 900×1200) a `CLOUDINARY_PRESETS` — los presets existentes eran todos paisaje/cuadrados, no había ninguno para las fotos verticales que pide la composición aprobada.
- Se creó `Section(client=ranchocachimba, section_type='hero')` — **no existía ningún `Section` para este tenant** (el `provision_tenant` original nunca se corrió con el seed de contenido para este cliente). Título/subtítulo marcados `PLACEHOLDER`, editable después vía dashboard.
- **Bug nuevo encontrado y arreglado:** `upload_to_cloudinary()` en `apps/core/cloudinary_utils.py` pasaba `format='auto'` a la API de upload de Cloudinary — inválido ahí (`'auto'` solo es válido en la URL de entrega vía `fetch_format`, no como extensión de archivo al subir). Función sin ningún llamador en todo el repo hasta ahora — quedó rota sin que nadie la ejerciera. Corregida (se sacó `format`, se dejó `quality:'auto'`).
- Se subieron **2 fotos de prueba** (no del cliente final, ver nota abajo) a `tenants/ranchocachimba/gallery/` como `GalleryItem(gallery_type='hero')`, y se activó `ClientSettings.enable_gallery` (estaba en `False`).
- Verificado con `check_tenant_setup` (`[OK]` tema/dominio, sin regresión en `servelec`) y render real: `200 OK`, ambas fotos de prueba sirviendo con el preset `hero_split`, pills "El oficio"/"La visita" presentes, cero hex hardcodeado fuera de los 10 tokens de `:root`.

**Sobre el material usado — importante antes de dar por bueno el diseño:**
Se usaron como prueba técnica los 2 archivos disponibles en `Documentacion/ClientesRanchoCachimba/` (`zar.jpeg` → slot A "El oficio", `FotoGaleria.jpeg` → slot B "La visita") — **asignación arbitraria**, no se abrieron/miraron los archivos para decidir cuál mostraba pastoreo y cuál granja (instrucción explícita: tratarlos solo como rutas). Esto confirma que el layout funciona con fotos reales, pero **no confirma que sean las fotos ni el recorte correctos** — falta una pasada de diseño real: revisar cuál foto va en cada slot, si el recorte 3:4 automático de Cloudinary funciona bien para cada una (`gravity:'auto'` puede fallar en fotos de acción), y reemplazar por el material definitivo del cliente. También queda sin subir el video (`Animaciondefondo.mp4`, en la misma carpeta) — no hay hoy ningún slot en el hero para video; se deja pendiente de decidir dónde usarlo (posible fondo animado o sección aparte), no se fuerza su uso en esta card.

### `#RC-07` — Navbar, footer y contacto mínimo — **DONE (2026-08-17)**
Reutilizar los componentes compartidos que ya existen. Contacto en esta etapa = botón WhatsApp directo, sin formulario todavía.
**DoD:** navegación y footer coherentes con la marca; el WhatsApp abre con mensaje pre-cargado.

**Resultado:**
- **Navbar:** ya estaba bien — 100% dinámico (`client.name`, `client.settings.tagline`), sin texto de rubro ajeno, ya tokenizado en `#RC-03`. No necesitó cambios de contenido.
- **Footer — 2 leftovers de Servelec encontrados y corregidos:** el copyright decía `{{ client.name }}-Ingeniería` (hardcodeado, tenía sentido para Servelec, no para un rancho turístico) y la ubicación decía `Puerto Montt · Región de Los Lagos` en vez de `Maullín · Región de Los Lagos` (dato real ya está en `ClientSettings.address`). Ambos corregidos.
- **Bug real encontrado y arreglado — botón flotante de WhatsApp:** `whatsapp_number` real del cliente es `'+56 9 2379 8733'` (con espacios y `+`), y el link `wa.me` se armaba con el valor crudo — `wa.me` exige solo dígitos, así que el botón estaba roto en cuanto se cargó el dato real (nadie lo había probado con un número real con espacios hasta ahora). Corregido con `|cut:' '|cut:'+'` en `base.html`. De paso se agregó el mensaje pre-cargado (`?text=...`, `urlencode`) que pedía el DoD — antes no existía.
- **Contacto = WhatsApp, sin formulario:** `contact.html` reemplazó el include de `partials/contact_form.html` (formulario genérico compartido) por una card de WhatsApp con el mismo botón/mensaje pre-cargado que el flotante. Se mantienen las cards de teléfono/dirección (no son un formulario, son datos reales ya cargados). El formulario completo con "tipo de visita"/"fecha tentativa" queda para `#RC-12` (Etapa 2) — no se perdió trabajo real: el formulario genérico que había no era el que Etapa 2 va a usar de todas formas.
- Verificado: render real con ambos links `wa.me` correctos (`https://wa.me/56923798733?text=...`), cero rastro del formulario, `check_tenant_setup` en `[OK]`, sin regresión en `servelec`.

### `#RC-08` — Publicar la Etapa 1 — **Código listo, publicación queda en manos del usuario**
Salir de `mode_under_construction`, deploy, DNS, SSL, `ALLOWED_HOSTS`.
**DoD:** `https://ranchocachimba.cl` en vivo con hero real. El cliente lo ve andando.

**Alcance de esta sesión:** por decisión explícita, no se hizo `git push`, no se creó PR y no se tocó producción/DNS/Render — son acciones de alto impacto (dominio real en vivo) que el usuario prefiere ejecutar él mismo. Lo que sí se verificó/dejó listo:

- **`render.yaml` → `EXTRA_DOMAINS`**: ya incluye `ranchocachimba.cl,www.ranchocachimba.cl` **y ya está commiteado** (no es un cambio pendiente — la nota de la v1 de este Kanban sobre "pendiente de commitear" quedó resuelta en algún commit anterior a esta rama).
- **`ALLOWED_HOSTS`**: arquitectura ya correcta y sin cambios necesarios — se arma dinámicamente desde los `Domain` en la DB + `EXTRA_DOMAINS`, así que no hace falta tocar código para que `ranchocachimba.cl` quede permitido en producción.
- **Migraciones**: `build.sh` corre `migrate --noinput` en cada deploy de Render automáticamente (paso 4/5) — la migración `0018_clientsettings_accent_color` (de `#RC-03`) se aplica sola, no requiere un paso manual aparte.

**Checklist para publicar (a ejecutar por el usuario):**

1. ~~Commitear el trabajo de esta rama.~~ **DONE (2026-08-17)** — `#RC-02` a `#RC-07` commiteados en `feature/RanchocachimbaEtapa1`.
2. **PR `feature/RanchocachimbaEtapa1` → `develop`**, y luego **`develop` → `main`** (dispara auto-deploy en Render) — siguiendo el flujo de `Procedimiento_Nuevo_Tenant.md`.
3. **Confirmar que `ranchocachimba` existe en producción.** No se pudo verificar desde esta sesión (sin credenciales de prod). Si no existe todavía:
   ```bash
   python manage.py provision_tenant ranchocachimba \
     --industry=turismo_rural --theme=ranchocachimba \
     --domain=ranchocachimba.cl --under-construction \
     --settings=config.settings.production
   ```
   Si ya existe (lo más probable, según el estado previo de este Kanban), en vez de reprovisionar hay que replicar a mano en producción lo que esta sesión hizo en dev: colores de marca en `ClientSettings` (`#RC-03`), `enable_gallery=True` + material real subido como `GalleryItem` (`#RC-06`, con fotos reales del cliente — no las de prueba de esta sesión) y el `Section('hero')` con copy definitivo (no el `PLACEHOLDER` actual).
4. **`python manage.py check_tenant_setup ranchocachimba --settings=config.settings.production`** — debe salir `[OK]` en tema y dominio antes de seguir.
5. **Render → Settings → Custom Domains**: agregar `ranchocachimba.cl` y `www.ranchocachimba.cl`.
6. **DNS del cliente**: `CNAME @ → <servicio>.onrender.com` (o el registro que indique Render). SSL lo provisiona Render solo una vez el DNS resuelve — no es un paso aparte.
7. **Decisión del negocio, no técnica: cuándo desactivar `mode_under_construction` en producción.** Recién ahí deja de verse "En construcción" y se ve el hero real — hacerlo solo cuando el material/copy ya no sean los de prueba de esta sesión (ver punto 3).
8. **Verificación en vivo**: `https://ranchocachimba.cl` muestra el hero real (no 404, no "en construcción" si ya se decidió activarlo), `servelec-ingenieria.cl` sigue funcionando sin regresión, y `check_tenant_setup --settings=config.settings.production` como cierre.

**Nota (2026-08-17):** el trabajo de `#RC-03`/`#RC-06`/`#RC-07` se dejó con `style=""` inline y CSS vars en vez de clases Tailwind — decisión explícita de no retocarlo ahora. El usuario quiere retomar esto más adelante como un **design system** propio (librería de componentes + tokens compartidos entre temas), no solo un traspaso de sintaxis. Card abierta en `Kanban_Plataforma_v2.md` → `#TOOL-04`.

---

# Etapa 2 · Landing completa

### `#RC-09` — Diseño y construcción por componente
Aquí se cumple lo que definiste: **la landing se arma sobre los componentes disponibles, mejorando cada uno y su reutilización.** Orden: experiencias → el pastor → galería de animales → cómo visitar → colegios.
**Regla por componente:** antes de escribir código, revisar si ya existe en `servelec`, `andesscale` o `themes/default`. Si existe en más de un lugar con diferencias, **generalizar y subir a `templates/components/`** en vez de crear una cuarta versión.
**Hallazgo que dispara esta regla:** `hero.html` hoy existe en tres versiones divergentes. La propuesta es un solo `hero` con variante `layout: single | split` — Cachimba estrena `split` y Servelec sigue en `single` sin tocarse.
**Consulta y actualiza:** `LinkRevisar.md` por cada componente.
**DoD:** cada componente construido queda en `components/` o documentado por qué tuvo que ser específico del tema.

### `#RC-10` — Sección del pastor
Bloque grande y distinto al resto: retrato, nombre, torneos, perros, video si existe. Es la carta de presentación.
**Consulta:** `LinkRevisar.md` — aquí es donde el registro de "afiche de trials" tiene sentido, aunque el resto del sitio sea más cálido.
**DoD:** la sección funciona sacada de contexto, como pieza compartible por sí sola.

### `#RC-11` — Contenido real y media en Cloudinary
Subidas vía `apps/core/cloudinary_utils.py` en `tenants/rancho-cachimba/{branding,services,sections}`. Incluye redacción final de textos.
**DoD:** cero placeholders, cero lorem ipsum, cero stock genérico.

### `#RC-12` — Formulario de contacto y SMTP
`ClientEmailSettings` y `FormConfig` con **tipo de visita** (familia / colegio / grupo) y **fecha tentativa** — cambia por completo la calidad del lead. Verificar SPF/DKIM.
**DoD:** envío end-to-end recibido en bandeja de entrada, no en spam.

### `#RC-13` — SEO y datos estructurados
`SEOConfig` + JSON-LD `TouristAttraction` × `LocalBusiness` con `openingHoursSpecification` y `geo`. Keywords: granja interactiva Maullín, pastoreo con perros ovejeros, paseo con niños Los Lagos, visitas de colegios.
**DoD:** JSON-LD válido en Rich Results Test.

---

# Etapa 3 · Cierre

### `#RC-14` — QA y aislamiento multi-tenant
`test_isolation` en verde · Servelec y AndesScale sin regresión · `showmigrations` limpio · responsive en móvil real · Lighthouse ≥85 performance y ≥90 accesibilidad · ninguna imagen sobre 300 KB.
**DoD:** checklist completo. Candidato a automatizar con `#TOOL-01`.

### `#RC-15` — Search Console y sitemap
`verify_search_console --domain ranchocachimba.cl`, envío de sitemap, robots.txt del tenant.
**DoD:** propiedad verificada y sitemap aceptado.

### `#RC-16` — Entrega y capacitación
`ClientAdmin`, email de bienvenida, sesión de 30 min sobre el dashboard, mini guía en PDF.
**DoD:** el cliente edita una sección él solo delante tuyo.

### `#RC-17` — Post-lanzamiento (semanas 1–4)
GA4, revisión de los primeros leads, pedirle 3 fotos nuevas para comprobar que la autoadministración se usa.
**DoD:** retrospectiva escrita: qué fue manual y debería ser producto → alimenta el Tablero B.

---

# Transversal

### `#RC-18` — Acuerdo comercial y dominio
Propuesta (fee de diseño + suscripción anual), cobro por transferencia, compra de `ranchocachimba.cl` en NIC Chile.
**Registrar:** que este tenant no pasó por `orders/`, para no ensuciar métricas después.

### `#RC-19` — Mantener `LinkRevisar.md` vivo
No es una card que se cierra: cada vez que aparece una referencia nueva o se descarta una, se actualiza el archivo en el mismo commit del componente.
**DoD:** al cerrar la Etapa 2, el archivo refleja lo que efectivamente se construyó y lo que se descartó con su motivo.

---

## Ruta crítica

```
RC-01 (material) ─┐
RC-02 (gate)      ├─> RC-03 ─> RC-04 ─> RC-05 ─> RC-06 ─> RC-07 ─> RC-08 ▶ ETAPA 1 EN VIVO
RC-18 (dominio) ──┘                                                            │
                                                                               ▼
                          RC-09 ─> RC-10 ─> RC-11 ─> RC-12 ─> RC-13 ─> RC-14 ─> RC-15 ─> RC-16
```

**Riesgo 1 — `#RC-02`.** El hero de dos fotos es lo primero que se construye y es justo lo que necesita dos slots de media. Si el gate sale mal, la Etapa 1 completa se retrasa. Correrlo antes que nada.

**Riesgo 2 — el material.** Ya no es "esperar fotos" en general, sino: ¿están *esas dos fotos específicas* en el comprimido? Si no, es lo primero que le pides al diseñador gráfico, porque bloquea todo lo demás.
