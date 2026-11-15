# Auditoría de plataforma vs. objetivo "plataforma modular" — 2026-11-11

> **Pregunta:** ¿qué tan lejos está el código actual de "una misma plataforma para gestionar todos los sitios, donde cada sitio es distinto y se arma con módulos reutilizables, y un dashboard profesional tipo Instagram/Gmail"? ¿Es factible con el ritmo actual?
> **Alcance:** lectura de código real (modelos, vistas, templates, tests). No se ejecutó la app ni se midió rendimiento. Es insumo para el plan consolidado; las cards resultantes están en [`KANBAN_PROYECTO.md`](KANBAN_PROYECTO.md).
> Métricas citadas = recuento de líneas/archivos al 2026-11-11.

## 1. Veredicto corto

**Factible, pero el kanban anterior asumía una pieza que no existe.** La base multi-tenant (resolución por dominio, aislamiento, branding por tenant, Cloudinary, temas por carpeta) es sólida y está testeada. Lo que falta para el objetivo es **composición**: hoy un sitio *no se arma* con módulos, se *escribe a mano* por tema. El plan "Clase `Module` + registro" (`CONS-08`) cubría solo el menú del dashboard y los flags; no resuelve que cada cliente pueda tener una página distinta. Hay que decidir ese diseño **antes** de construir Media y el dashboard nuevo (`MOD-00`), porque ambos dependen de él.

## 2. Qué hay hoy (hechos verificados)

### 2.1 La página pública no es modular
- `apps/website/views.py::home` (línea 59) entrega un contexto **fijo**: `hero`, `about`, `contact_section`, `services`, `form`. Cualquier bloque extra (stats, CTA, galería) lo resuelve cada template por su cuenta.
- Cada tema escribe su página a mano: `landing/home.html` de `themes/servelec` (133 líneas, 7 includes en orden fijo), `themes/default` (342), `themes/electricidad` (633, HTML casi todo inline), `andesscale` (75).
- `Section` (`apps/website/models.py:41`): 5 tipos fijos (`hero`, `about`, `service`, `contact`, `gallery`) con `unique_together (client, section_type)` → **un solo bloque de cada tipo por cliente; no se puede agregar, repetir ni reordenar bloques**. El docstring lo dice: "No se crean secciones arbitrarias".
- `Section.order` existe pero la página no lo usa para componer.

### 2.2 Componentes: hay duplicación, y un patrón que funciona
- Compartidos hoy en `templates/components/` (8 archivos + `slots/`): `navbar`, `navbar_cta`, `footer`, `hero_gallery`, `hero_ctas_base`, `media_collection`, `media_item`, `contact_multistep`.
- Duplicados por tema (candidatos a generalizar según la regla de `CLAUDE.md`, 2+ temas): `about`, `contact`, `services`, `footer`, `navbar`, `hero` (en `default`, `servelec`, `andesscale`); `cta` (en `servelec` y `andesscale`); `hero_ctas`/`hero_overlay_theme` (en `default` y `servelec`).
- El patrón bueno ya existe y sirve de molde: `components/media_collection.html` con `mode="slideshow"|"grid"` + slots de override por ruta.
- Orden de carpetas inconsistente: `andesscale/` está en la raíz de `templates/`, no en `themes/`; `themes/electricidad` existe pero **no** está en `Client.THEME_CHOICES` (solo `default` y `servelec`); `templates_library/electricidad` y `servicios_profesionales` están vacías; también hay `templates/tenants/` y `templates/landing/` sueltos.

### 2.3 El dashboard está organizado por modelo, no por tarea
- 6 entradas fijas de menú (Inicio, Branding, Portada, Galería, Secciones, Contactos) = 14 templates, 2.517 líneas. Cada entrada es un CRUD de un modelo.
- Ya tiene **cabecera móvil + drawer** (Alpine, `lg:hidden`): hay punto de partida mobile.
- **Subida de archivos 100 % server-side, de a uno:** formularios `multipart` que pasan por Django/Render (`gallery_item_add` exige `request.FILES['image']`). Sin multi-archivo, sin subida directa a Cloudinary, sin progreso. Es el cuello de botella para "subir contenido como en Instagram".
- **htmx está cargado en `dashboard/base.html` pero ningún template del dashboard lo usa** (`grep hx-` solo encuentra 5 parciales de edición inline pública en `templates/partials/`, legado). Todo es recarga completa de página.
- **Roles sin efecto:** `UserProfile.role` (`owner`/`admin`/`editor`) existe, pero `tenant_member_required` solo valida pertenencia al tenant, y `can_edit: True` está fijo en las vistas. Un `editor` puede lo mismo que un `owner`.
- Dashboard "Inicio" muestra 4 contadores + 5 contactos recientes: no hay actividad, "qué sigue", ni estado del sitio.

### 2.4 Medios: la infraestructura existe, el modelo no
- `apps/core/cloudinary_utils.py` ya tiene `get_video_url`, `get_video_thumbnail_url`, `get_video_sources`, `validate_video_file`, presets y `get_tenant_usage`.
- Pero **ningún modelo guarda video**: solo hay un comentario de diseño en `apps/website/models.py:17`. `Section.image`, `Section.background_image`, `Service.image` y `GalleryItem` (FKs a `section`/`service` desde `#DEUDA-02` Fase 1) siguen siendo imágenes sueltas por dueño.
- Límites: `ClientSettings.hero_images_limit` / `gallery_images_limit` se aplican en la galería; los límites de `Plan` (`max_pages`/`max_services`/`max_images`) **no se aplican en ningún lado** (solo aparecen en `admin.py`).

### 2.5 Flags y módulos a medias
- `enable_gallery`: gobierna vistas del dashboard (real).
- `enable_contact_form`: existe; sin auditar su efecto.
- `enable_testimonials`: solo muestra/oculta un link en el navbar de `themes/default`; **no hay modelo de testimonios**.
- `enable_blog`: sin ningún código detrás.

### 2.6 Deuda estructural que frena el cambio
- `apps/website/views.py`: **1.099 líneas** en un solo archivo (home, contacto, dashboard, secciones, servicios, galería, portada, branding, contactos, auth modal).
- Rutas duplicadas: edición inline pública (`edit_section`, `edit_service`, `add_service`, `delete_service`) y su versión de dashboard (`*_dashboard`, `create_service`); login duplicado inalcanzable en `apps/accounts/views.py`.
- Tests por app: `core` 55, `tenants` 65, `website` 52, `orders` 48, **`accounts` 0, `marketing` 0**. Los 52 de `website` cubren autorización y aislamiento; no hay tests de UX del dashboard (guardar sección, subir imagen, reordenar).
- Aislamiento: depende de `.filter(client=request.client)` en cada vista (no hay mecanismo estructural → `CONS-06`).
- Seguridad abierta que compromete lo que vendés: Django Admin con fuga entre tenants y credenciales SMTP en texto plano (`SEC-05`/`SEC-06`), más el plazo 1-dic-2026 de la Ley 21.719.

## 3. Brecha contra el objetivo

| Objetivo | Hoy | Brecha |
|---|---|---|
| Una plataforma para gestionar todos los sitios | ✅ multi-tenant real, `tenant_member_required`, suite de aislamiento | Roles sin efecto; aislamiento no estructural |
| Cada sitio distinto | 🟡 distinto por **tema** (4 carpetas hechas a mano) | Distinto por **cliente** requiere composición de bloques por cliente |
| Módulos reutilizables | 🟡 8 componentes compartidos + 1 patrón bueno | ~6 componentes duplicados entre temas; sin registro; flags sin módulo |
| Dashboard profesional y útil | 🔴 CRUD por modelo, recarga completa, sin htmx | Rediseño por tareas + interacción parcial |
| Subir contenido tipo Instagram | 🔴 un archivo, vía servidor, solo imagen | Modelo `MediaAsset` + subida directa firmada + multi-archivo + video |
| Cliente autónomo, no técnico | 🟡 puede editar texto/imágenes en formularios largos | Flujo "Publicar", previsualización, límites visibles |

## 4. Decisión de diseño pendiente (bloquea Media y Dashboard) — `MOD-00`

Dos conceptos distintos que el plan viejo mezclaba bajo "módulo":

1. **Módulo de funcionalidad** (galería, formulario de contacto, servicios, medios, blog, testimonios): se *activa* por cliente/plan, tiene modelo(s), vistas de dashboard y componente público. → registro con nombre, flag, límites, URLs, entrada de menú, componente.
2. **Bloque de página** (hero, about, stats, CTA, galería, servicios, contacto…): unidad visual que se *ordena* en la home de cada cliente.

Opciones, de menor a mayor costo:

| Opción | Qué es | Costo estimado | Riesgo |
|---|---|---|---|
| **A. Registro de módulos + home por tema (recomendada como primer paso)** | Solo el concepto 1. La home sigue escrita por tema, pero cada bloque opcional se muestra solo si el módulo está activo; el menú del dashboard sale del registro | ~2–3 días (es `CONS-08/09` ya planeado) | Bajo. No cambia la página pública |
| **B. A + orden/visibilidad de bloques existentes** | Reusar `Section.order` + un campo de visibilidad para que el cliente (o vos) reordene/oculte los bloques que el tema ya trae; el tema itera una lista ordenada en vez de includes fijos | +3–4 días | Medio. Hay que migrar 4 `home.html` a iterar la lista |
| **C. Modelo `PageBlock` completo** | Bloques repetibles, de tipos arbitrarios, con configuración por bloque (JSON), editables por el cliente | +10–15 días | Alto: es un mini page-builder; riesgo de sobreconstruir antes de tener clientes |

**✅ Decidido por el usuario el 2026-11-12: A ahora, B después (`MOD-02`), C descartado.** Recomendación original: A ahora (encaja en el mes de consolidación), B como segunda etapa si el dashboard nuevo lo necesita, C descartado hasta tener clientes que lo pidan. La decisión final es del plan consolidado.

## 5. Factibilidad (capacidad vs. alcance)

- **Capacidad:** 2 días/semana × 4–5 h ≈ 9 h/semana. Lo que queda de noviembre ≈ 3 semanas ≈ **6 días de trabajo**; diciembre ≈ 8 días.
- **Alcance ya planeado:** consolidación = 5 días; `MOD-01` Media ≈ 5; dashboard mobile-first ≈ 4. Total 14 días ≈ 7 semanas → termina hacia **mediados de enero**, sin colchón y sin Rancho Cachimba.
- **Lo que el plan viejo dejó fuera:** `SEC-05/06/07` (~2 días, P0 y atados a la Ley 21.719 del 1-dic), `MOD-00` (~1 día), generalización de componentes (`COMP-01`, ~2 días), roles efectivos y nav por tareas del dashboard.
- **Conclusión:** "este mes" cabe como **consolidar + dejar decidido y empezado el módulo**, no como dashboard terminado. Dashboard profesional completo ≈ enero. Rancho Cachimba a mediados de febrero queda **muy ajustado**; conviene tratarlo como "mejor caso", no como compromiso.
- Las estimaciones son del autor del plan, no medidas; el primer día real de `MOD-01` sirve para recalibrarlas.

## 6. Riesgos

1. **Sobreconstruir el builder** (opción C) sin clientes que lo pidan — mitigación: decidir A/B en `MOD-00`.
2. **Refactor de `views.py` + `Module` + dashboard a la vez** — mitigación: orden estricto (borrar legacy → mixin → separar vistas → registro → dashboard), una card por commit.
3. **Migración de imágenes a `MediaAsset` (`DEUDA-02` Fase 2)** toca ~16 templates sin tests: escribir tests de renderizado de home por tema **antes** de migrar.
4. **P0 de seguridad/compliance quedan fuera del mes** si no se agendan — mitigación: reservar 2 días explícitos.
5. **Sin clientes captando:** el valor de lo construido se valida recién con el primer cliente real; conviene que el dashboard nuevo se pruebe con Servelec (cliente existente) antes de Cachimba.
