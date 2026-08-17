# Tablero B — Plataforma, tooling y flujos de trabajo

> **Estado:** PLAN — pendiente de aprobación. Ningún archivo del repo fue tocado.
> **Origen:** auditoría del directorio real (snapshot `estructura_proyecto.md`), README técnico, skill `andesscale-saas` y catálogo de plugins/MCP disponibles en tu cuenta.
> **Regla:** ninguna card de este tablero debe bloquear la publicación de Rancho Cachimba, salvo las marcadas **⚠ adelantable**.
> **Ejecución:** el desarrollo se hace desde **Claude Code sobre el repo**. Eso sube la prioridad de todo lo que da contexto local al agente — `#TOOL-07` pasa a ser la primera card del tablero, porque sin `CLAUDE.md` cada sesión en la terminal arranca a ciegas.
> **Fecha:** 17-08-2026 · v2

---

## Hallazgos de la auditoría del directorio

Esto es lo que salió de comparar lo que dice la documentación contra lo que hay en el árbol de archivos.

### 🔴 Deriva documentación ↔ código
| Hallazgo | Evidencia |
|---|---|
| `check_tenant_setup` está documentado en el README como comando de QA, pero **no existe** en `apps/tenants/management/commands/` | README §9 lo usa en el procedimiento de nuevo tenant |
| `audit_tenant_emails` tiene `.pyc` compilado pero **no tiene `.py`** en el árbol | archivo borrado sin limpiar, o no commiteado |
| `Documentacion/Procedimiento_Nuevo_Tenant.md` está referenciado en el README pero **no aparece** en la carpeta | solo hay `KanBan_NuevoCliente.md`, `README.md`, `estructura_proyecto.txt` |
| El README dice que `template` vive en `ClientSettings`; en otra parte dice que vive en `Client`. La skill repite la versión vieja | fuente de un bug ya conocido (template no carga sin error visible) |

**Esto no es cosmético.** La skill `andesscale-saas` y el README son lo que consume cualquier IA que trabaje en el proyecto. Si están desfasados, todo agente arranca con supuestos falsos y el "diagnóstico antes de ejecución" pierde su valor.

### 🟠 Higiene del repositorio
| Hallazgo | Riesgo |
|---|---|
| `.env` en la raíz del árbol | si no está en `.gitignore`, son credenciales de Cloudinary/Neon/MP expuestas |
| `db.sqlite3`, `db_production_test.sqlite3` y **otro** `config/db.sqlite3` | tres bases de datos sueltas; ambigüedad de cuál usa dev |
| `env/` (virtualenv) dentro del árbol del proyecto | ~14.000 archivos; si entra a git, el repo queda inmanejable |
| `staticfiles/` en la raíz **y** `config/staticfiles/` | doble destino de `collectstatic` |
| 3 CSV de `cloudinary_audit_2026032*` sueltos en la raíz | salida de scripts sin carpeta de destino |
| Un archivo llamado `exit` en la raíz | typo de shell que quedó commiteado |
| `.claude/settings.local.json` vive dentro de `Documentacion/`, no en la raíz | la config de agente no aplica al abrir el proyecto desde la raíz |
| No existe `CLAUDE.md` en la raíz | el proyecto no tiene memoria de proyecto; todo el contexto depende de la skill |

### 🟡 Inconsistencia estructural de templates
Hoy hay **dos convenciones conviviendo**:
- `templates/servelec/`, `templates/andesscale/` → temas fuera de `themes/`
- `templates/themes/default/`, `templates/themes/electricidad/` → temas dentro de `themes/`

Y además `templates/landing/home.html` suelto en la raíz de templates. Cada cliente nuevo que se agregue sin decidir esto suma una variante más.

### 🟢 Lo que está sólido
Vale decirlo, porque no todo es deuda: la separación por dominio en `apps/` es limpia, `orders/services/` con `email_service` / `mercadopago_service` / `order_processor` es la forma correcta de aislar integraciones, el set de management commands de `tenants/` es serio (11 comandos, incluido `test_isolation`), y ya existe `apps/core/rate_limit.py` — o sea seguridad no está en cero.

---

## Área DEUDA — Deuda técnica

### `#DEUDA-01` ⚠ adelantable — Auditoría de `CLOUDINARY_PRESETS` — **DONE (2026-08-17, vía `#RC-02`)**
Claves duplicadas causan que "gane" un preset u otro de forma no determinista. Auditar el diccionario completo, deduplicar, documentar cada preset con su uso.
**DoD:** un solo punto de definición, test que falla si se reintroduce una clave duplicada.
**Nota:** era prerequisito de `#RC-02`. `gallery_card`/`gallery_full` deduplicados en `apps/core/cloudinary_utils.py`. Pendiente: el test que falla ante una clave duplicada (no se hizo — no bloqueaba `#RC-06`).

### `#DEUDA-02` ⚠ adelantable — Rediseño de `GalleryItem`
El campo `gallery_type` bloquea cada imagen a un solo rol. Objetivo: **pool único de imágenes por tenant** — subir una vez, reusar en cualquier sección. Requiere FK/M2M entre `Section`/`Service` y `GalleryItem`, que hoy no existen.
**DoD:** una imagen subida una vez puede usarse en hero, servicio y galería sin duplicar el asset en Cloudinary.
**Advertencia:** es la card más grande del tablero. Migración de datos incluida. No empezarla a medias.
**Nota (2026-08-17):** el `AttributeError` en `get_background_image_url()` que esta card iba a arreglar "de paso" ya se resolvió en `#RC-02` (el método era código muerto en `GalleryItem`, se eliminó — no hacía falta esta migración grande para eso). Esta card sigue viva solo por el objetivo de pool único reutilizable, no es bloqueador de Rancho Cachimba.

### `#DEUDA-03` — Unificar convención de temas bajo `templates/themes/`
Mover `servelec/` y `andesscale/` dentro de `themes/`, actualizar `Client.template` de los tenants existentes con migración de datos, ajustar `TenantTemplateLoader`.
**Ojo Windows:** renames que solo cambian mayúsculas necesitan el truco de dos pasos con `git mv`.
**DoD:** una sola convención, los tres tenants renderizan igual que antes.

### `#DEUDA-04` — Limpieza de raíz del repositorio
Verificar `.gitignore` (`.env`, `env/`, `*.sqlite3`, `staticfiles/`), mover CSVs de auditoría a `scripts/output/`, borrar `exit`, resolver el doble `staticfiles/`, mover `.claude/` a la raíz.
**DoD:** `git status` limpio en un clone fresco, `.env` confirmado fuera del historial.
**Si `.env` estuvo alguna vez commiteado:** rotar todas las credenciales. No basta con borrarlo.

### `#DEUDA-05` — Reconciliar README y skill con el código real
Crear `check_tenant_setup` (o borrarlo del README), escribir `Procedimiento_Nuevo_Tenant.md` de verdad, corregir `ClientSettings.template` vs `Client.template` en los 3 lugares donde está mal.
**DoD:** cada comando documentado existe; cada archivo referenciado existe.

---

## Área TOOL — Herramientas y agentes

### `#TOOL-01` — Playwright para QA visual de tenants
**Recomendación tras revisar el trade-off:** **Playwright CLI + tests versionados**, no solo el MCP.
- El **MCP** sirve para exploración conversacional ("abre el sitio y dime qué se ve mal") — bueno para debug puntual.
- El **CLI con specs en el repo** sirve para lo que tú realmente necesitas: un smoke test que corra sobre los 3 tenants antes de cada deploy y falle solo si algo se rompió.

**Propuesta concreta:** `tests/e2e/` con un spec parametrizado por tenant que verifique: home 200, hero visible, formulario envía, navbar y footer presentes, screenshot de referencia. Cada tenant nuevo = una línea en un array.
**DoD:** `npx playwright test` corre sobre servelec, andesscale y rancho-cachimba y falla si un tema se rompe.
**Reemplaza:** el checklist manual de `#RC-13`.

### `#TOOL-02` — Seguridad: Strix vs StackHawk
Investigué las dos opciones que mencionaste y hay una diferencia práctica:

| | **Strix** | **StackHawk HawkScan** |
|---|---|---|
| Qué es | Agente de IA open source para pentesting autónomo | DAST clásico con plugin oficial |
| Disponibilidad | Instalación propia (Docker) | **Ya está en tu catálogo de plugins**, listo para habilitar |
| Fricción | Media-alta: hay que levantarlo y darle un target | Baja: se habilita y corre |
| Cuándo conviene | Auditoría profunda puntual, una vez cada varios meses | Escaneo recurrente antes de deploy |

**Recomendación:** empezar por **StackHawk** (fricción cero, ya lo tienes disponible) para el escaneo recurrente, y reservar **Strix** para una auditoría profunda una vez que MercadoPago esté en producción — que es cuando el riesgo real sube, porque ahí empiezas a mover dinero.
**DoD:** un escaneo corrido contra staging, findings triados en cards.

### `#TOOL-03` — MCPs a conectar
Verifiqué el registro. Están disponibles y aplican directo a tu stack:

| MCP | Para qué te sirve concretamente | Prioridad |
|---|---|---|
| **Neon** | Inspeccionar esquema, comparar migraciones, crear branch de DB por feature | Alta |
| **Cloudinary** | Listar y auditar assets por tenant sin escribir scripts — ataca directo `#DEUDA-01` | Alta |
| **Render** | Ver estado de deploys, logs y métricas sin salir del chat | Media |
| **Sentry** | Errores en producción con contexto; hoy no tienes observabilidad | Media |
| **Figma** | Solo si migras la etapa de diseño desde Stitch | Baja |

**Ya conectado:** Stitch (vía tu escritorio) y Google Drive.
**No existe** MCP de MercadoPago en el registro — esa integración seguirá siendo código propio.
**DoD:** Neon y Cloudinary conectados y probados con una consulta real.

### `#TOOL-04` — Design system / librería de componentes para los themes
El usuario maneja diseño y desarrollo con Tailwind CSS y quiere mejorar cómo construye páginas con un design system, en vez de repetir componentes ad-hoc por tema.
**Evidencia concreta de esta sesión (`#RC-03`/`#RC-06`/`#RC-07` del Tablero A):** el trabajo en `templates/ranchocachimba/` terminó con bastante `style=""` inline y CSS custom properties (`color-mix()`, etc.) en vez de clases Tailwind — se dejó así a propósito por decisión del usuario (no se retocó retroactivamente), pero expuso que cada theme define sus tokens de color por separado en su propio `tailwind.config` (`servelec/base.html`, `ranchocachimba/base.html`, `andesscale/base.html`, cada uno con el mismo bloque duplicado). Esto es la misma raíz que ya había detectado `hero_cachimba.html` (mockup de diseño, Tablero A): `hero.html` hoy tiene **tres versiones divergentes** entre temas, no solo una diferencia de color.
**Qué evaluar cuando se retome:**
- Config de Tailwind compartida (base + extensión por tenant) en vez de bloques duplicados por theme.
- Librería de componentes real en `templates/components/` — ya hay un precedente pedido en `#RC-09` (Tablero A) para generalizar `hero` con variante `layout: single | split`; este card lo extendería al resto.
- Regla explícita de "token de marca" (tenant-configurable, vive en `ClientSettings`) vs. "utilidad de diseño" (Tailwind, no tenant-configurable) — hoy es una decisión ad-hoc repetida card a card (se resolvió así en `#RC-03`), debería quedar como regla del sistema.
**DoD:** por definir con el usuario — placeholder hasta que se retome, no bloquea a Rancho Cachimba.
**Relacionado:** `#RC-09` (Tablero A).

### `#TOOL-04` — Plugins del catálogo
Revisé tu catálogo. Tres tienen encaje real:
- **`engineering`** — trae `code-review`, `tech-debt`, `deploy-checklist`, `testing-strategy`, `architecture`. `deploy-checklist` reemplaza tu checklist manual de deploy; `tech-debt` es literalmente lo que estamos haciendo en este tablero.
- **`design`** — trae `design-critique`, `design-system`, `accessibility-review`, `ux-copy`. `accessibility-review` te tapa un hueco: hoy no auditas accesibilidad y es un argumento de venta con colegios y organismos públicos.
- **`stackhawk-hawkscan`** — ver `#TOOL-02`.

**Sobre "plugin claude codex":** no encontré nada con ese nombre en el catálogo ni en el registro. Si te referías a usar Codex/otro agente en paralelo con Claude Code, eso no es un plugin sino una decisión de flujo — dime y lo convierto en card aparte.
**DoD:** plugins habilitados y probados en una tarea real cada uno.

### `#TOOL-05` — Skill `frontend-design` (lo que buscabas como "Skilliu")
No existe ninguna skill llamada "Skilliu". Lo más cercano a lo que describes es **`frontend-design`**, la skill oficial de Anthropic para generar interfaces con criterio visual — es la que circula en los tutoriales en español sobre "crear páginas web increíbles con Claude Code".
Encaja con tu línea de trabajo: es del mismo espíritu que `taste-skill`, que ya usas como marco de calidad anti-genérico.
**DoD:** skill instalada, probada contra el hero de Rancho Cachimba, comparada con el output de Stitch para decidir cuál se queda en el flujo.

### `#TOOL-06` — Mejorar la skill `andesscale-saas`
La skill está bien construida (índice de referencias, carga selectiva). Lo que le falta:
- `references/tenants.md` — ficha por tenant: dominio, tema, rubro, estado de SEO/correo, particularidades. Hoy esa información no está en ningún lado consultable.
- `references/seguridad.md` — rate limit, validación de webhooks, headers, manejo de secretos.
- `references/prompts.md` — la plantilla de prompt de Stitch, versionada, en vez de reescribirla cada vez.
- Corregir `ClientSettings.template` → `Client.template` (arrastra el error del README).
- Actualizar la lista de comandos: quitar los que no existen.

**DoD:** skill actualizada y entregada como archivo para que la guardes en tu cuenta.

### `#TOOL-07` 🔺 **primera card** — `CLAUDE.md` en la raíz del repo
Sube de prioridad porque el desarrollo pasa a hacerse desde Claude Code en la terminal. Hoy todo el contexto vive en la skill, que es de cuenta y no de repo: un agente que abre el proyecto desde la terminal no ve nada.
**Contenido:** comandos frecuentes, las 4 convenciones críticas (`render_tenant_template`, managers, `cloudinary_utils`, `showmigrations`), orden de `config/urls.py`, mapa de dónde vive cada insumo de diseño (incluido `LinkRevisar.md` por cliente), y link a la skill para lo profundo.
**DoD:** `CLAUDE.md` en la raíz y `.claude/` movido desde `Documentacion/`.

### `#TOOL-08` — Kanban con estado real
Hoy el kanban vive en el README y en markdowns sueltos, y se desactualiza. Opciones:
- **A)** Mantenerlo en markdown en el repo, versionado con el código. Cero herramientas nuevas, cero sincronización.
- **B)** Airtable (está en tu catálogo, tiene vista kanban nativa y MCP). Sirve si quieres verlo desde el teléfono.
- **C)** El tablero HTML que te entrego junto a este documento, actualizado sesión a sesión.

**Recomendación:** A como fuente de verdad + C como vista. Trabajas solo; una herramienta más es una cosa más que mantener desincronizada.

---

## Área DS — Sistema de diseño

### `#DS-01` — Formalizar Andes Horizon como tokens
Hoy el sistema vive en tu cabeza y en las decisiones caso a caso. Escribirlo: escala tipográfica, espaciado, radios, sombras, estados. Publicarlo como `docs/design-system.md` + `static/css/tokens.css`.
**Regla que ya rige y hay que dejar explícita:** color de marca siempre como custom property por tenant; neutrales fijos.
**DoD:** un tema nuevo se puede construir leyendo solo ese documento.

### `#DS-02` — Librería de componentes compartidos entre temas
`navbar`, `footer`, `hero`, `contacto`, `galería` se reescriben por tema. Extraer la estructura común a `templates/components/` y dejar en cada tema solo lo que de verdad cambia.
**Impacto:** cada cliente nuevo baja de ~10 componentes escritos a ~3.
**DoD:** Rancho Cachimba usa componentes compartidos para navbar, footer y contacto.

### `#DS-03` — Accesibilidad como estándar
Contraste AA, navegación por teclado, `alt` obligatorio en el dashboard (hoy probablemente opcional), foco visible.
**Argumento comercial:** con colegios y municipalidades esto se pregunta.
**DoD:** los 3 tenants pasan auditoría de accesibilidad automatizada.

---

## Área DB — Base de datos

### `#DB-01` — Branch de Neon por feature
Ya tienes `main` y `dev`. Usar branches efímeros por cambio de esquema evita probar migraciones grandes (como `#DEUDA-02`) contra datos compartidos. El MCP de Neon lo hace en una llamada.
**DoD:** procedimiento documentado y usado una vez de verdad.

### `#DB-02` — Backups verificados
Existe la idea de backup en el kanban viejo. Falta la parte que importa: **probar la restauración**. Un backup sin restore probado no es un backup.
**DoD:** restore completo hecho a un branch de Neon, documentado con tiempos.

### `#DB-03` — Índices y consultas
Revisar `TenantAwareManager`: toda query filtra por `client`, así que cada modelo multi-tenant debería tener índice en `client` y en los campos de orden habituales. Verificar con `EXPLAIN` sobre datos de producción.
**DoD:** informe de queries lentas, índices agregados donde corresponda.

### `#DB-04` — Preparar pgvector (diferido)
Para `apps/assistant/`. Decisión ya tomada (pgvector sobre Neon, no FAISS). **No abrir hasta tener 3+ clientes pagando** — es la card más fácil de empezar y la que menos ingreso genera hoy.

---

## Área FLOW — Flujos comerciales y de trabajo

### `#FLOW-01` — Formalizar el flujo de ingreso de cliente
Convertir el proceso real en un procedimiento repetible, con los artefactos que hoy improvisas:
```
Prospecto → Reunión de diagnóstico → Propuesta (plantilla) → Aceptación
→ Brief + captura de contenido (checklist) → Pago → Provisioning
→ Diseño → Construcción → QA → Publicación → Entrega y capacitación → Seguimiento
```
**Entregables:** plantilla de propuesta, checklist de brief (ya redactado en `#RC-01` — generalizarlo), contrato/términos, checklist de publicación.
**DoD:** el siguiente cliente después de Rancho Cachimba se hace siguiendo el documento, sin inventar nada.

### `#FLOW-02` — Automatizar el checklist de publicación
Convertir `#RC-13` en `python manage.py check_tenant_setup <slug>`: valida tema existente, dominio en `ALLOWED_HOSTS`, `ClientEmailSettings` completo, `SEOConfig` completo, al menos N secciones con contenido, sin placeholders.
**Bonus:** es el comando que el README ya dice que existe (`#DEUDA-05`).
**DoD:** el comando falla con mensaje claro sobre un tenant incompleto.

### `#FLOW-03` — Onboarding autoservicio del cliente
`orders/views_onboarding.py` y los templates ya existen. Falta cerrar el círculo: que un cliente pague, complete el onboarding y tenga sitio sin intervención tuya.
**Bloqueado por:** `#PAY-01`.
**Observación de Rancho Cachimba:** todo lo que hagas a mano en el Tablero A es evidencia de qué falta aquí. Anotarlo mientras pasa, no después.

### `#FLOW-04` — Insumos de diseño versionados en el repo
Hoy los prompts buenos (Stitch, generación de contenido, redacción de textos) y las referencias visuales viven en historiales de chat. Con la ejecución movida a Claude Code eso deja de funcionar: el agente en la terminal no ve el chat.

**Dos piezas:**
1. `Documentacion/prompts/` — `prompt_stitch.md`, `prompt_contenido_cliente.md`, `prompt_seo.md`, con versión y nota de qué funcionó.
2. **`LinkRevisar.md` como convención por cliente** — `Documentacion/clientes/<slug>/LinkRevisar.md`. Referencias de diseño con formato fijo: link · qué se toma · a qué componente aplica · estado (por revisar / aprobado / descartado con motivo). Estrena en Rancho Cachimba (`#RC-04`) y pasa a ser parte del checklist de brief de `#FLOW-01`.

**Por qué importa más de lo que parece:** cada entrada apunta a un componente, así que el archivo alimenta directo el trabajo de librería (`#DS-02`) en vez de quedar como moodboard decorativo. Y lo descartado se queda con su motivo, que es lo que evita volver a proponer lo mismo en el cliente siguiente.
**DoD:** ambas carpetas en el repo y `LinkRevisar.md` de Rancho Cachimba poblado y en uso.

---

## Área PAY — Pagos

### `#PAY-01` — MercadoPago a producción
Bloqueador de ingresos declarado hace meses. Depende del registro SII para facturación electrónica.
**Acción concreta:** separar en dos: (a) lo que depende del SII y es trámite, (b) lo que es técnico y se puede dejar listo ahora (validación de firma del webhook, idempotencia, manejo de pagos duplicados, estados de `Order`).
**DoD:** cobro real recibido de punta a punta.

### `#PAY-02` — Registrar las observaciones del cobro manual de Rancho Cachimba
Mientras cobras fuera de plataforma, ir anotando cada fricción: qué datos pediste a mano, qué correo escribiste tú, qué paso del onboarding hiciste por el cliente. Esa lista **es** la especificación de `#FLOW-03`.
**DoD:** documento de observaciones cerrado al terminar `#RC-17`.

### `#PAY-03` — Prueba end-to-end en sandbox
Antes de producción, pasar un tenant ficticio por checkout completo en modo test. Hoy el flujo nunca se probó de punta a punta con provisioning automático.
**DoD:** tenant creado automáticamente por un pago de prueba, sin tocar el shell.

---

## Área SEC — Seguridad

### `#SEC-01` — Validación de firma de webhooks de MercadoPago
El README dice "validar IPN y firma". Verificar que esté implementado de verdad en `mercadopago_service.py`. Un webhook sin validación de firma es un endpoint que cualquiera puede llamar para provisionar tenants gratis.
**DoD:** firma verificada, test que prueba que un webhook falsificado se rechaza.

### `#SEC-02` — Headers de seguridad
CSP, HSTS, `X-Frame-Options`, `SECURE_SSL_REDIRECT`, cookies `Secure`/`HttpOnly`/`SameSite` en `production.py`.
**DoD:** nota A en securityheaders.com para los 3 dominios.

### `#SEC-03` — Manejo de secretos
Confirmar que `.env` nunca entró a git. Rotar credenciales si entró. Documentar dónde vive cada secreto (Render env vars) y quién tiene acceso.
**DoD:** inventario de secretos, rotación hecha si corresponde.

### `#SEC-04` — Aislamiento entre tenants como test permanente
`test_isolation` existe. Falta que corra automáticamente, no cuando alguien se acuerda.
**DoD:** el test corre en cada push (ver `#TOOL-01`, misma infraestructura).

---

## Priorización sugerida

**Ahora (paralelo a Rancho Cachimba, sin bloquearlo)**
`#TOOL-07` 🔺 primero · `#DEUDA-01` · `#DEUDA-04` · `#SEC-03` · `#TOOL-03` (Neon + Cloudinary) · `#FLOW-04` (la parte de `LinkRevisar.md`, que arranca con `#RC-04`)

**Inmediatamente después de publicar**
`#DEUDA-05` · `#TOOL-01` · `#TOOL-06` · `#FLOW-01` · `#FLOW-02` · `#PAY-02`

**Siguiente ciclo (habilita al cliente #3 y #4)**
`#DEUDA-02` · `#DEUDA-03` · `#DS-01` · `#DS-02` · `#PAY-01` · `#PAY-03` · `#SEC-01`

**Diferido hasta tener tracción**
`#DB-04` (pgvector/asistente) · `#TOOL-02` con Strix · cards #47–#54 del kanban viejo (Google Ads / GA4 / dashboard de marketing)

> Sobre las cards #47–#54 del kanban original: son un módulo de marketing completo para una plataforma que todavía tiene **un** cliente pagando. Sugiero congelarlas explícitamente en vez de dejarlas como "próximas" — mientras figuren ahí compiten por atención con cosas que sí mueven ingreso.
