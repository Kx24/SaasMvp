# KANBAN — AndesScale SaaS

> **Única fuente de verdad del trabajo pendiente.** Lo hecho: [`historico/KANBAN_HISTORICO.md`](historico/KANBAN_HISTORICO.md). Mapa de documentos: [`INDEX.md`](INDEX.md).
> Respaldo de este plan: [`AUDITORIA_PLATAFORMA_2026-11.md`](AUDITORIA_PLATAFORMA_2026-11.md) (plataforma), [`SEGURIDAD.md`](SEGURIDAD.md) (chequeo de seguridad y ley), [`ARQUITECTURA.md`](ARQUITECTURA.md) (cómo funciona).
> **Regla de tamaño:** ~300 líneas máximo. Al cerrar una card: una línea en el histórico y se borra de acá. El detalle largo va a su propio archivo.

---

## 🌙 Retomar aquí (actualizado 2026-11-12)

**Foco del trimestre (nov 2026 – feb 2027), sin captar clientes:** ① consolidar la plataforma (módulos reutilizables + dashboard profesional estilo Instagram/Gmail), ② ciberseguridad, ③ Ley 21.719.

**Decisiones tomadas el 2026-11-12:**
- **Composición de página (`MOD-00`): opción A ahora, B después.** Registro de módulos de funcionalidad + menú del dashboard generado; la home sigue escrita por tema. Orden/visibilidad de bloques por cliente (B) es `MOD-02`. Page-builder completo, descartado.
- **Seguridad y ley primero.** La Ley 21.719 rige el 1-dic-2026; la consolidación arranca en diciembre.

**Estado:** `develop` con commits de documentación pendientes de push (PyCharm). Producción en `main` con PR #2 (`f140bf0`). Último gate: 219 tests OK (1 skip), `makemigrations --check` limpio, 79 errores de `ruff` conocidos.

**Ritmo:** 2 días/semana × 4–5 h. Cada día = Bloque A (~2 h) + Bloque B (~2 h) + cierre (suite, `ruff` en lo tocado, `makemigrations --check`, commit, actualizar esta sección, push). Ningún día cierra en rojo ni sin commit. Card que no entra en 2 h se parte.

**▶️ Próxima sesión: D1** (`CONS-01` + `SEC-10`).

---

## 📖 Diccionario

### Prefijos de cards (activos)
| Prefijo | Significa | Ejemplo |
|---|---|---|
| `CONS` | **Consolidación**: ordenar y endurecer lo que ya existe, sin funcionalidad nueva | separar `views.py`, borrar rutas duplicadas |
| `COMP` | **Componentes**: piezas de template compartidas entre temas (`templates/components/`) | un solo `cta.html` para todos los temas |
| `MOD` | **Módulos**: funcionalidad que se activa por cliente o plan, con modelo + dashboard + componente público | Media, galería, testimonios |
| `DASH` | **Dashboard** del cliente: navegación, flujos, interacción, roles | flujo "Publicar" |
| `SEC` | **Ciberseguridad**: hallazgos y controles técnicos | admin por tenant, cifrado |
| `LEY` | **Ley 21.719** de datos personales: consentimiento, derechos, retención, contratos | página de política |
| `DB` | Base de datos: backups, índices, ramas de Neon | restore probado |
| `OPS` | Operación e infraestructura: Render, DNS, crons, monitoreo | cron de correos |
| `PAY` | Pagos (MercadoPago) | pasar a producción |
| `FLOW` | Flujo comercial y onboarding de clientes | autoservicio |
| `BIZ` | Negocio y contratos (puede no tocar código) | cláusulas |
| `MAIL` | Correo: entregabilidad y plantillas | SPF/DKIM |
| `PREV` | URL temporal `<slug>.andesscale.com` | wildcard |
| `DEUDA` | Deuda técnica sin urgencia | código muerto |
| `DOC` | Documentación | README |
| `TOOL` | Herramientas de desarrollo | escáneres |
| `RC` | Cliente Rancho Cachimba (en pausa) | landing |

**Prefijos históricos** (solo en el histórico, no crear cards nuevas): `AUD` auditoría 2026-08 · `MED` mediano plazo · `DS` design system · `BUG` · `BOLT` / `PILOT` piloto agéntico · `RC-BOLT` hero de Cachimba.

### Términos
| Término | Definición |
|---|---|
| **Tenant** | Un cliente con su sitio. En código: `Client`; en un request: `request.client` |
| **Tema** | Carpeta de templates que define el aspecto de un sitio (`themes/default`, `themes/servelec`) |
| **Componente** | Trozo de template reutilizable que se incluye con `{% include %}` |
| **Slot** | Hueco de un componente que un tema rellena pasando la ruta de otro template |
| **Módulo de funcionalidad** | Capacidad activable (galería, contacto, medios): datos + pantallas del dashboard + componente público |
| **Bloque de página** | Unidad visual de la home (hero, about, stats…). Hoy fija por tema |
| **Registro de módulos** | Lista central en código que declara cada módulo: nombre, flag, límites, URLs, entrada de menú, componente |
| **Preset** | Transformación de Cloudinary con nombre (`hero`, `thumbnail`…) |
| **Gate** | Verificaciones obligatorias antes de cerrar una card o desplegar |
| **DoD** | *Definition of Done*: condición verificable para dar una card por cerrada |
| **Hallazgo incidental** | Bug real encontrado fuera del alcance de la card; se arregla ahí y se anota |
| **P0–P3** | Prioridad: crítica · alta · media · baja |
| **S / M / L / XL** | Esfuerzo: <2 h · ~medio día · 1–2 días · >2 días (partir antes de empezar) |
| **D1, D2…** | Día de trabajo del plan (4–5 h), no día calendario. **Bloque A / B**: sus dos mitades |

---

## 🗓️ Plan de ejecución

### Fase 0 — Cerrar lo pendiente (D1)
| Día | Bloque A | Bloque B |
|---|---|---|
| D1 | `CONS-01` Push de `develop` + smoke test de producción | `SEC-10` Dependencias al día + `pip-audit` |

### Fase 1 — Seguridad y ley mínima (D2–D5, antes del 1-dic-2026)
| Día | Bloque A | Bloque B |
|---|---|---|
| D2 | `SEC-06` Credenciales SMTP/API cifradas | `SEC-06` (continúa: migración de datos y clave en Render) |
| D3 | `SEC-08` Un solo login (+ open redirect de `next`) | `CONS-04` Borrar rutas legacy |
| D4 | `LEY-01` Consentimiento en contacto y onboarding | `LEY-01` Página de política de privacidad (contenidos del art. 14 ter) |
| D5 | `SEC-14` (parte) JSON-LD escapa `</` | `LEY-05` + `LEY-06` Registro de tratamientos y procedimiento de brechas (documentos) |

### Fase 2 — Consolidación (D6–D11, diciembre)
| Día | Bloque A | Bloque B |
|---|---|---|
| D6 | `DB-02` Backup de Neon con restore probado (+ `DB-03`) | `SEC-12` Integración continua con el gate |
| D7 | `CONS-02` Documentación al día (Neon, `CLAUDE.md`, README) | `CONS-03` `ruff --fix` |
| D8 | `CONS-06` `TenantOwnedMixin` | `DASH-04` Roles con efecto |
| D9 | `DEUDA-08` Portada sin titular por defecto | `CONS-07` Separar `views.py` |
| D10 | `CONS-08` Registro de módulos (opción A) | `CONS-08` (continúa) |
| D11 | `CONS-09` Menú del dashboard desde el registro | `CONS-05` Flags sin módulo |

### Fase 3 — Módulos y dashboard (~20 días, enero–febrero 2027)
Orden: `COMP-02` (1 d) → `COMP-01` (2 d) → `MOD-01` Media (5 d) → `DASH-01` (1 d) → `DASH-02` (4 d) → `DASH-03` (2 d) → `DASH-05` (1 d) → `LEY-02` + resto de `LEY-03` (2 d) → `LEY-04` + `LEY-07` (1 d) → `SEC-13` + `SEC-14` + `SEC-15` (2 d).
Después: `MOD-02` (opción B) y Rancho Cachimba — **no antes de marzo de 2027** (la meta anterior de mediados de febrero no cabe).

Las estimaciones no están medidas; recalibrar al cerrar cada fase.

---

## 🚧 Bloqueado — espera una decisión o insumo tuyo

| ID | Qué falta |
|---|---|
| `LEY-00` | Ubicar `Informe_Cumplimiento_Ley21719.md` (lo cita `MASTER_PLAN` §1.4, no está en el repo). Ya no bloquea: el texto de la ley está en `Documentacion/`. Sí conviene que un abogado revise la política (`LEY-01`) y el contrato (`LEY-07`) |
| `SEC-16` | Activar 2FA en Render, Neon, Cloudinary, Cloudflare, Zoho y GitHub; revisar qué cuentas `staff`/superuser existen en producción |
| `OPS-01` | Servelec: `servelec-ingenieria.cl` en NXDOMAIN (web **y correo** caídos), mitigado con `servelec.andesscale.com`. Definitivo: recuperar la clave NIC, o reactivar la zona en Bluehosting, o zona en Cloudflare + cambio de NS (A `@` 216.24.57.1, CNAME `www`, MX Zoho 10/20/50, SPF `v=spf1 include:zoho.com ~all`, DKIM). Confirmar en vivo los pasos de la mitigación |
| `PREV-00` | Decidir: wildcard `*.andesscale.com` (~US$29,78/mes) vs alta manual con `add_preview_domain` |
| `OPS-06` | Crear cron `send-pending-emails` en Render (pagado) para volver a `EMAIL_ASYNC=true`; tampoco existe `contact-digest` |
| `PAY-01` | MercadoPago a producción: `MP_*`, trámite SII, pasada manual en sandbox. Hoy apagado a propósito |
| `MAIL-01` | SPF/DKIM de Zoho; probar plantillas en Gmail/Outlook móvil |
| `SEC-09` | CSP en `/checkout/`; requiere sandbox de MercadoPago (después de `PAY-01`) |

---

## 📋 Cards

### `CONS` — Consolidación
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `CONS-01` | Push + smoke test de producción | P0 | S | Checklist del PR #2: login por tenant, login cruzado rechazado, contacto con correo real, links con `BASE_URL`, galerías, Tailwind, `check_tenant_setup` por tenant; deploy de Render en verde |
| `CONS-02` | Documentación al día | P2 | M | "Supabase" → Neon en `CLAUDE.md`, `Documentacion/README.md` y skill; quitar de `CLAUDE.md` la sección del MCP de GitHub y la frase "corre en cada push"; reescribir `README.md` raíz corto; revisar `docs/CLOUDINARY.md` |
| `CONS-03` | `ruff --fix` | P3 | S | 72 autofixables aplicados, 7 restantes revisados |
| `CONS-04` | Borrar rutas y vistas legacy | P1 | M | Fuera la edición inline pública (`edit_section`, `edit_service`, `add_service`, `delete_service`, `login_modal`, `templates/partials/section_*`/`service_*`); queda solo la versión de dashboard. **Bug a confirmar:** `service_confirm_delete.html` usa `{% url 'dashboard_services' %}` y esa ruta no existe |
| `CONS-05` | Flags sin módulo | P2 | S | `enable_blog` eliminado; `enable_testimonials` pasa a módulo real o se elimina (hoy solo oculta un link) |
| `CONS-06` | `TenantOwnedMixin` | P1 | M | Las vistas del dashboard obtienen sus objetos por un único camino que filtra por `request.client`; suite de aislamiento sigue verde |
| `CONS-07` | Separar `apps/website/views.py` (1.099 líneas) | P2 | M | Un archivo por área (público, secciones, servicios, galería, contactos, branding); URLs sin cambios |
| `CONS-08` | Registro de módulos (opción A) | P1 | L | Clase `Module` + registro: nombre, flag, límites, URLs, entrada de menú, componente público. Galería, contacto y servicios declarados como módulos |
| `CONS-09` | Menú del dashboard generado desde el registro | P1 | M | Un módulo desactivado no aparece en el menú ni responde en su URL |

### `COMP` — Componentes
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `COMP-01` | Generalizar componentes duplicados | P1 | L | `cta`, `about`, `services`, `contact`, `footer`, `navbar`, `hero_ctas`/`hero_overlay_theme` en `templates/components/` con el patrón de `media_collection` (parámetro `mode` + slots). Un componente por commit; a11y y guardia de tokens verdes |
| `COMP-02` | Ordenar el árbol de temas | P2 | M | `andesscale/` dentro de `themes/`; `themes/electricidad` entra a `THEME_CHOICES` o se archiva; fuera `templates_library/` (vacía) y carpetas sueltas sin uso |

### `MOD` — Módulos
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `MOD-01` | Módulo **Media** | P1 | XL (~5 d) | `MediaAsset` (imagen / video Cloudinary / embed YouTube-Vimeo), subida directa navegador→Cloudinary firmada, multi-archivo, límites por plan (`BIZ-01`). Unifica las 6 subidas del dashboard, que hoy llaman `cloudinary.uploader.upload` a mano con carpeta `{slug}/…` en vez de `upload_to_cloudinary` y `tenants/{slug}/…` (hallado por `BOLT-13`). Migra `Section.image`/`background_image`/`Service.image` al pool (~16 templates). DoD: subir 10 fotos y un video desde el celular; los 3 tenants renderizan igual |
| `MOD-02` | Orden y visibilidad de bloques (opción B) | P2 | L | El cliente reordena y oculta los bloques que su tema trae; cada `home.html` itera una lista en vez de includes fijos |
| `MOD-03` | Módulo Testimonios | P3 | M | Solo si `CONS-05` decide conservarlo: modelo + pantalla + componente |

### `DASH` — Dashboard
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `DASH-01` | Navegación por tareas | P1 | M | Inicio (estado del sitio + qué sigue) · Publicar · Mensajes · Mi sitio · Ajustes, generado desde el registro |
| `DASH-02` | Flujo "Publicar" mobile-first | P1 | XL (~4 d) | Grilla de medios tipo Instagram sobre `MOD-01`. Una persona no técnica publica sin ayuda; probado con Servelec |
| `DASH-03` | Interacción con htmx | P2 | L | Guardar, ocultar y reordenar sin recargar; estados vacíos y de error. Servicios como patrón |
| `DASH-04` | Roles con efecto | P2 | M | Matriz `owner`/`admin`/`editor` × acción, testeada (hoy `can_edit: True` fijo) |
| `DASH-05` | Tests del dashboard | P2 | M | Guardar sección, subir, reordenar; a11y de Playwright extendida al dashboard; `apps/accounts` deja de tener 0 tests |

### `SEC` — Ciberseguridad (detalle y evidencia en `SEGURIDAD.md`)
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `SEC-05b` | Restos de alcance en el admin | P3 | S | `list_filter` por `client` en `SEOConfigAdmin`/`UserProfileAdmin` lista los nombres de todos los clientes a un staff; el desplegable de `PaymentLog.order` no se restringe. Hallado por `BOLT-15` |
| `SEC-06` | Credenciales cifradas en reposo | P0 | M | `smtp_password`/`api_key` cifrados (Fernet) con clave en variable de entorno + migración de datos; test: el valor en base no es el texto ingresado |
| `SEC-08` | Un solo login | P1 | M | Resuelta la colisión `/auth/`; validar `next` con `url_has_allowed_host_and_scheme` (hoy `login_view` redirige a cualquier URL); `apps/accounts` ≥ 70 % de cobertura. Los métodos de invitación ya existen (`BOLT-12`) |
| `SEC-10` | Dependencias | P0 | M | `pip-audit` en `requirements-dev.txt` y sin vulnerabilidades conocidas; Django en el último 5.2.x; `gunicorn` actualizado; fuera `djangorestframework` y herramientas de desarrollo de `requirements.txt`; misma versión de Python en Render y local |
| `SEC-12` | Integración continua | P1 | M | GitHub Actions en cada push/PR: suite, aislamiento, `makemigrations --check`, `bandit -ll`, `pip-audit` |
| `SEC-13` | Endurecer `/superadmin/` | P1 | M | Segundo factor (TOTP) y rate limit en su login |
| `SEC-14` | Salidas sin escapar | P2 | M | Revisados los 21 avisos de `mark_safe`; JSON-LD escapa `</`; `bandit` en 0 Medium o justificados |
| `SEC-15` | Runbook de incidentes y rotación de secretos | P2 | S | Documento: qué hacer ante una fuga, cómo rotar cada secreto de `Inventario_Secretos.md`, a quién avisar (enlaza `LEY-06`) |
| `SEC-17` | Comentarios `<!-- DEBUG -->` en el HTML público | P3 | S | `templates/components/media_collection.html` (3) y `templates/themes/servelec/components/hero.html` (3) exponen nombre del cliente y datos internos; quitarlos o envolverlos en `{% if debug %}`. Hallado por `BOLT-11` |

### `LEY` — Ley 21.719 (artículos y estado en `SEGURIDAD.md` §3; texto en `Ley-21719_13-DIC-2024.pdf`)
| ID | Card | P | Esf. | Definición de hecho |
|---|---|---|---|---|
| `LEY-01` | Consentimiento y política de privacidad (art. 12 y 14 ter) | P0 | L | Checkbox no pre-marcado con fecha, versión de política e IP guardados en `ContactSubmission` y en el onboarding (prueba del consentimiento). Página de política por tenant y de AndesScale con los contenidos del art. 14 ter, fecha y versión; el enlace del formulario deja de ser `href="#"` |
| `LEY-02` | Derechos del titular (art. 4–11) | P1 | M | Canal de solicitudes (correo o formulario) + registro de cada solicitud con fecha y respuesta; comando que exporta en JSON y suprime los datos de una persona; bloqueo temporal. Plazos: 30 días corridos, bloqueo en 2 días hábiles |
| `LEY-03` | Retención y purga (art. 14 d y principio de proporcionalidad) | P1 | M | Purga de contactos ya independiente del digest e incluye spam (`BOLT-14`). Falta: **decidir si se purgan los mensajes `new` antiguos** (hoy se conservan); plazos para `Order`, `PaymentLog`, `EmailOutbox`; plazo publicado en la política; cron en Render (`OPS-06`) para que corra en producción |
| `LEY-04` | Proveedores y transferencia internacional (art. 15 bis, 27–28) | P2 | S | DPA o cláusulas contractuales de Neon, Render, Cloudinary y Zoho archivados; listados en la política |
| `LEY-05` | Registro de tratamientos y bases de licitud (art. 13, 14, 14 quáter) | P1 | S | Documento por tratamiento: datos, finalidad, base de licitud, quién accede, conservación, proveedores. Incluye decidir si se sigue guardando IP y user-agent |
| `LEY-06` | Procedimiento de brechas (art. 14 sexies) | P1 | S | Documento + plantilla de registro: detección, evaluación de riesgo, reporte a la Agencia, aviso al cliente responsable cuando AndesScale es encargado, aviso a titulares cuando corresponde |
| `LEY-07` | Contrato de encargo con clientes (art. 15 bis) | P1 | M | Cláusula con objeto, duración, finalidad, tipo de datos, categorías de titulares y obligaciones; autorización escrita de sub-encargados (Neon, Render, Cloudinary, Zoho); devolución o supresión al terminar (une con `BIZ-03`). Sin código; revisar con abogado |

### Negocio, datos y operación
| ID | Card | P | Esf. | Nota |
|---|---|---|---|---|
| `DB-02` | Backup de Neon con restore probado | P1 | M | Restore a una rama, documentado con tiempos |
| `DB-03` | `EXPLAIN ANALYZE` de consultas calientes en Neon | P3 | S | Junto a `DB-02` |
| `BIZ-01` | Límites de plan con efecto real | P2 | M | `max_images/pages/services` verificados al crear contenido. Se resuelve en el registro de módulos |
| `BIZ-02` | `Plan.renewal_price` y `Client.monthly_fee` alineados al modelo real | P2 | S | Pago único + mantención 12 meses + renovación anual (`MASTER_PLAN` §4.4). `Client.plan` es texto, no FK a `Plan`: decidir |
| `BIZ-03` | Cláusulas de mantención y fin de servicio | P2 | M | Sin código. `MASTER_PLAN` §4.5 |
| `FLOW-03` | Onboarding 100 % autoservicio | P2 | L | Depende de `PAY-01`; spec en `PAY-02` |
| `PAY-02` | Registro de fricciones del cobro manual | P3 | S | — |
| `OPS-04` | Alerta de créditos Cloudinary | P3 | S | Existe el comando `cloudinary_usage`; conectar umbrales y aviso |
| `OPS-05` | Cache compartida, `/health/` real, Sentry | P3 | M | Antes de más de un proceso |
| `DEUDA-06` | Código muerto | P3 | S | `cloudinary_settings.py`, `OrderProcessor` |
| `DEUDA-08` | Portada sin titular con la configuración por defecto | P1 | S | En `themes/default` y `themes/servelec` el titular del hero solo se ve con `enable_gallery=True` **y** `Section.slot_key='hero'`; ningún alta los fija. Decidir: mostrar el diseño base aunque la galería esté apagada y/o crear la Section hero con `slot_key='hero'`. Invertir `HeroDefaultsFindingTest` (`apps/website/tests/test_home_render.py`). Hallado por `BOLT-11` |

### `RC` — Rancho Cachimba ⏸️ (rama `feature/RanchocachimbaEtapa1`; no tocar sin pedido explícito)
| ID | Card | Depende de |
|---|---|---|
| `RC-01` | Inventario del material del cliente | Tú, en paralelo |
| `RC-18` | Acuerdo comercial y dominio `ranchocachimba.cl` | Tú |
| `RC-06b` | Pasada de diseño real del hero | `RC-01` |
| `RC-09` / `RC-10` | Landing por componente; sección del pastor | `COMP-01`, `MOD-01` |
| `RC-11` | Contenido real y media; favicon y `logo_footer` | `RC-01` |
| `RC-12` | Formulario de contacto + SMTP del tenant | `MAIL-01` |
| `RC-13` | SEO local + JSON-LD | `SEC-14` |
| `RC-21` | Pill "El oficio" oculto bajo el header fijo | — |
| `RC-22` | Integrar la rama a `develop` | Fase 3 terminada |
| `RC-08` | Publicar Etapa 1 | todo lo anterior |
| `RC-14`–`17` | QA + Lighthouse · Search Console · entrega · retrospectiva | `RC-08` |

### Congelado
`DB-01` rama de base por feature · `DB-04` pgvector · `TOOL-02` StackHawk/Strix · `TOOL-03` MCPs · marketing/GA4/Ads · sprints de venta (`MASTER_PLAN` §3.5).

---

## 🧪 Arnés de TDD (contrato, no sugerencia)

1. Toda card Backend/Database entrega un test que **falla sin el cambio** (rojo confirmado; si es de infra, reproducir con `git stash`).
2. Cobertura mínima, que nunca baja: `apps/orders/` ≥ 80 %, `apps/tenants/middleware.py` + `managers.py` ≥ 90 %, resto ≥ 70 %.
3. Antes de cerrar: `ruff check` en lo tocado, suite completa verde, `makemigrations --check --dry-run` limpio.
4. Un commit por card, con el ID en el mensaje. Nada se commitea en rojo.
5. Hallazgo incidental que bloquea el DoD: se arregla ahí y se anota en el commit y en el histórico.
6. Bucle: SPEC (rojo) → CODE (verde) → VERIFY → REPAIR (máx. 3 vueltas; a la 4ª, parar y reportar) → CLOSE.

| Verificación | Comando |
|---|---|
| Suite | `python manage.py test apps -v 1` |
| Aislamiento | `python manage.py test apps.tenants.tests_isolation` |
| Lint | `python -m ruff check apps/ config/` |
| Migraciones | `python manage.py makemigrations --check --dry-run` |
| Seguridad estática | `python -m bandit -r apps config -x "*/tests/*,*/migrations/*" -ll -q` |
| Producción | `python manage.py check --deploy --settings=config.settings.production` |
| E2E + a11y | `npx playwright test` |
| Tenant listo | `python manage.py check_tenant_setup <slug> [--check-dns]` |

## 🔗 Satélites
- **Piloto agéntico:** `docs/kanban_agente.md`, `docs/infoagente.md`, `docs/tratamiento_git.md` (los referencian `orchestrate.py` y `scripts/gatekeeper.py`). Las cards nuevas se crean acá.
  **Ronda 3 (preparada 2026-11-12, sin ejecutar):** `BOLT-11` `CONS-10` · `BOLT-12` `SEC-07` · `BOLT-13` `SEC-11` · `BOLT-14` `LEY-03` parcial · `BOLT-15` `SEC-05` · `BOLT-16` `CONS-03`, en la rama `agent/fase1-seguridad`. `orchestrate.py` no tiene agente conectado: se ejecuta con una sesión de Claude Code siguiendo `.claude/workflows/`.
- **Estrategia y negocio:** `MASTER_PLAN_Y_ARQUITECTURA.md`.
