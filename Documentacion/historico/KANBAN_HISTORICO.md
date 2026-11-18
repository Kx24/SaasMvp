# KANBAN HISTÓRICO — AndesScale SaaS

> **Solo lectura.** Registro de lo que ya está **hecho** (2026-08-20 → 2026-11-11). Lo pendiente vive en [`../KANBAN_PROYECTO.md`](../KANBAN_PROYECTO.md).
> El detalle completo de cada card (DoD, hallazgos, tests, decisiones) está en el snapshot íntegro: [`KANBAN_PROYECTO_snapshot_2026-11-10.md`](KANBAN_PROYECTO_snapshot_2026-11-10.md) — buscá por ID (`#AUD-06`, etc.).
> Cuando una card del kanban activo se cierra, se agrega una línea acá (ID · qué resolvió · fecha · commit) y se borra de allá.

---

## Seguridad y aislamiento multi-tenant

| ID | Qué resolvió | Fecha | Ref |
|---|---|---|---|
| `#AUD-01` | Rutas de checkout reordenadas (`<slug:plan_slug>/` al final) — el pago era inalcanzable | 2026-08-20 | `b5539f9`* |
| `#AUD-02` | Firma de webhook MercadoPago obligatoria, falla cerrado | 2026-08-20 | `b5539f9`* |
| `#AUD-03` | Vínculo usuario↔tenant en login y dashboard (`tenant_member_required`) | 2026-08-20 | `b5539f9`* |
| `#AUD-04` | `render.yaml` reparado (web + cron autocontenidos) | 2026-08-20 | `b5539f9`* |
| `#MED-02` | Suite de aislamiento multi-tenant vía HTTP; eliminado `_current_client` (código muerto peligroso) | 2026-08-22 | — |
| `#MED-05` | IP confiable tras proxy (`TRUSTED_PROXY_COUNT`) + rate limit en login/checkout | 2026-08-23 | `f570cda`, `9e8ab83` |
| `#SEC-02` | Headers de seguridad: CSP + Permissions-Policy (`/checkout/` excluido a propósito) | 2026-08-22 | — |
| `#SEC-03` | `setup_production` ya no crea superusuario con clave hardcodeada; inventario de secretos | 2026-08-24 | `5229215` |
| `#AUD-12` | `DEBUG=False` fijo en producción, sin override por env var | 2026-08-22 | — |
| `SEC-07` | Logs sin emails (`email_ref`, guardia AST) y login sin enumeración. Hallazgos corregidos: `/auth/set-password/` y `/auth/forgot-password/` daban 500 (métodos de `UserProfile` inexistentes) y `'dashboard:home'` inexistente | 2026-11-12 | `BOLT-12` |
| `SEC-11` | Validación de subidas en el servidor: contenido real con Pillow, sin SVG, tope de 10 MB, en las 6 subidas del dashboard y los logos de branding | 2026-11-12 | `BOLT-13` |
| `SEC-05` | Django Admin limitado por tenant en 8 admins (órdenes, pagos, dominios, settings, credenciales SMTP, formularios, SEO, perfiles); `ClientAdmin`, `/superadmin/nuevo/` y `/tenants/` solo superuser | 2026-11-12 | `BOLT-15` |
| `SEC-17` | Comentarios `<!-- DEBUG -->` eliminados del HTML público (`media_collection.html` y `servelec/components/hero.html`); guardia estática + render por tema | 2026-11-14 | `BOLT-17` |
| `SEC-08` | Un solo login: `client_login` respeta `next` solo si es interno (`url_has_allowed_host_and_scheme`); eliminados `login_view`/`logout_view` de `apps/accounts` y sus rutas | 2026-11-14 | `BOLT-20` |
| `SEC-12` | Integración continua: GitHub Actions con el gate estricto, aislamiento, ruff completo y `pip-audit`; permisos mínimos y sin secretos | 2026-11-14 | `BOLT-30` |
| `SEC-14` | Salidas sin escapar: 11 `mark_safe` de `cloudinary_tags.py` reemplazados por `format_html`/`format_html_join` y el JSON-LD de `seo_tags.py` escapa `<`, `>`, `&`; queda 1 `mark_safe` justificado con `# nosec` (HTML ya escapado con `_esc()`); `bandit -ll` en 0 | 2026-11-14 | `BOLT-23` |
| `SEC-05b` (parcial) | Filtro lateral `client` de `UserProfileAdmin`/`SEOConfigAdmin` oculto a staff no superuser (`TenantAdminMixin.get_list_filter`); queda el desplegable de `PaymentLog.order` | 2026-11-14 | `BOLT-24` |
| `SEC-05b` (cierre) | Desplegables FK del admin restringidos al tenant del staff no superuser (`TenantAdminMixin.formfield_for_foreignkey`; cubre `PaymentLog.order`) | 2026-11-14 | `BOLT-32` |
| `SEC-06` | `smtp_password` y `api_key` de `ClientEmailSettings` cifradas en reposo con `MultiFernet` (`EncryptedTextField`, clave `FIELD_ENCRYPTION_KEY`, producción falla al importar sin ella), migración de datos reversible y admin que no devuelve el secreto | 2026-11-14 | `BOLT-22` |
| `SEC-10` | Dependencias al día: Django 5.2.6→5.2.19, gunicorn 21.2.0→27.0.1, pillow 11→13, certifi/idna/requests/sqlparse/urllib3 actualizados; fuera DRF e `ipython`/`django-extensions` (ahora en `requirements-dev.txt` con `pip-audit`); `pip-audit` limpio | 2026-11-15 | `BOLT-27` |
| `SEC-18` | Un solo `TenantAdminMixin` (`apps/accounts/mixins.py`; borrado el fallback de `apps/website/admin.py`): el staff no ve filtros por tenant ni desplegables FK a `User` ajenos (`profile__client`); un test recorre `admin.site._registry` | 2026-11-15 | `BOLT-41` |
| `DASH-04` | Roles con efecto en el dashboard: matriz única `DASHBOARD_PERMISSIONS` (`apps/accounts/permissions.py`) aplicada con `tenant_permission_required` en las vistas del dashboard; `viewer` solo lectura y sin mensajes, `editor` no borra ni cambia la marca; la interfaz oculta lo no permitido (`dash_perms`) | 2026-11-15 | `BOLT-35` |
| `DASH-05` | Tests del dashboard: un archivo por área en `apps/website/tests/` (secciones, servicios, galería, marca, mensajes) con éxito y error de cada flujo, `dashboard.spec.js` con login real y a11y en Inicio y Secciones; `seed_e2e_tenants` crea el owner `owner-e2e` y se niega a correr con `DEBUG=False`. Hallazgos corregidos: los colores de marca aceptaban cualquier texto (ahora hex de 6 dígitos), el spam aparecía en Mensajes e Inicio, y el contador de no leídos del menú nunca se mostraba (`unread_contacts` no existía); contraste y `aria-label` del dashboard | 2026-11-17 | `BOLT-55` |
| `DASH-06` | Avatar e íconos del dashboard usaban el token inexistente `var(--primary)`; ahora `var(--color-primary)` (color de marca del tenant), con test que recorre `templates/dashboard/` | 2026-11-18 | `BOLT-64` |
| `DASH-08` | Ya cubierta por `BOLT-55`: el context processor define `unread_contacts`; la fila quedó obsoleta | 2026-11-18 | `BOLT-64` |
| `SEC-15` | Runbook de incidentes y rotación de secretos (`Documentacion/Runbook_Incidentes.md`): primeros 15 minutos, fuga de secreto, acceso indebido, base dañada (con `DB-02` pendiente), deploy caído, correo/dominio comprometido, datos personales (remite a `LEY-06`), contactos y registro de incidentes | 2026-11-18 | `BOLT-67` |

\* commit del gate de seguridad completo en `feature/RanchocachimbaEtapa1`.

## Flujo transaccional, correo y pagos

| ID | Qué resolvió | Fecha | Ref |
|---|---|---|---|
| `#AUD-05` | `order_number` sin condición de carrera (`ORD-{año}-{uuid6}`) | 2026-08-22 | `10cf3ec` |
| `#AUD-06` | Emails dentro de `transaction.on_commit()`; fix `UserProfile.update_or_create` | 2026-08-22 | `2e8b226` |
| `#AUD-07` | Producción falla al importar sin credenciales SMTP; `_site_url()` en vez de dominio hardcodeado | 2026-08-22 | `fabedf2` |
| `#AUD-08` | Webhook devuelve 500 ante excepción inesperada (MP reintenta) | 2026-08-22 | — |
| `#AUD-09` | Onboarding ya no muta estado en GET | 2026-08-22 | — |
| `#PAY-03` | E2E pago→onboarding→tenant con MP mockeado (parcial: falta pasada manual sandbox). Encontró 2 bugs reales (`NoReverseMatch`, token limpiado antes de tiempo) | 2026-08-22 | `37d09c7` |
| `#MED-01` | Correo asíncrono: `EmailOutbox` + comando `send_pending_emails` | 2026-08-22 | — |
| `#MED-04` (mitad) | Texto plano real por template + link de soporte reparado + dark-mode | 2026-08-23 | `2593784` |
| `LEY-03` (parte) | Purga de contactos independiente del digest e incluye spam antiguo; `--dry-run` sin borrar | 2026-11-12 | `BOLT-14` |
| `LEY-03` (parte) | Tope legal de 365 días (`CONTACT_MAX_RETENTION_DAYS`) para todo `ContactSubmission` de tenants activos, cualquier estado y con o sin `auto_purge_enabled` | 2026-11-14 | `BOLT-26` |
| `LEY-03` (parte) | Plazos de `Order`/`PaymentLog` (6 años, `ORDER_RETENTION_DAYS`) y `EmailOutbox` (90 días): comando `purge_expired_data` (con `--dry-run`), invocado por `send_contact_digest`; plazos publicados en la política | 2026-11-16 | `BOLT-48` |
| `LEY-01` (parte) | Páginas de política de privacidad en `/privacidad/` (cliente y plataforma) con versión vigente; enlaces `href="#"` reemplazados; `check_tenant_setup` avisa si falta `contact_email` | 2026-11-15 | `BOLT-33` |
| `LEY-01` | Captura y prueba del consentimiento: checkbox no pre-marcado en contacto (todas las variantes) y checkout, con `consent_at`, versión de política e IP; user-agent eliminado de `ContactSubmission` y `Order`; aviso con enlace en el onboarding | 2026-11-15 | `BOLT-34` |
| `LEY-02` (parte) | Canal y registro de solicitudes de derechos: formulario público `/privacidad/solicitud/` (CSRF, rate limit y honeypot, éxito idéntico), modelo `DataSubjectRequest` con `due_at` a 30 días, acuse al solicitante y aviso al tenant tras el commit, admin con columna de vencimiento y `response_notes` obligatorio al cerrar, aviso en el dashboard para `view_contacts`; la identidad del solicitante no se verifica | 2026-11-16 | `BOLT-49` |
| `LEY-02` | Herramienta de derechos del titular: comando `data_subject` (`export`/`erase`/`block`/`unblock`) siempre acotado a un tenant; suprimir borra mensajes de contacto y emails en cola y anonimiza `Order`/`PaymentLog` (se conservan por obligación legal); bloqueo temporal con `BlockedSubject` que oculta los mensajes del dashboard, digest y contadores y los exime de la purga; `EmailOutbox.client` (nuevo) acota la cola por tenant; constancia opcional en `DataSubjectRequest.response_notes` | 2026-11-16 | `BOLT-50` |
| `LEY-08` | Aviso previo en el digest (30 días, `CONTACT_PURGE_WARNING_DAYS`) de mensajes `new` por alcanzar el tope de 365 días; el digest sale aunque no haya mensajes nuevos; sin datos personales | 2026-11-15 | `BOLT-45` |

## Base de datos y rendimiento

| ID | Qué resolvió | Fecha |
|---|---|---|
| `#MED-03` | Índices compuestos reales en `Service` y `Domain` (el resto ya estaba bien) | 2026-08-22 |
| `#DEUDA-02` Fase 1 | `GalleryItem.gallery_type` → FKs `section`/`service`; un `Service` puede tener galería | 2026-08-24 (`1a0794d`) |

## Frontend, temas y diseño

| ID | Qué resolvió | Fecha | Ref |
|---|---|---|---|
| `#AUD-11` (+`#TOOL-04`/`#DS-01`/`#DS-02`) | Build de Tailwind (sin CDN), contrato de tema en `docs/design-system.md`, `accent_color`/`font_family` en `BrandingForm`, retirado `tenant_custom_css` | 2026-08-22 | — |
| `#BUG-01` | Comentarios `{# #}` multilínea rotos en 17 templates (ya estaban en producción) + test guardia | 2026-08-22 | — |
| `#DS-03` | Gate de accesibilidad WCAG AA con axe-core/Playwright (0 violaciones en las 3 páginas) | 2026-08-24 | `c875540` |
| `#DEUDA-03` | Vocabulario de temas unificado; arregló checkout del Plan Pro que dejaba sitios rotos | 2026-08-24 | — |
| `#DEUDA-01` | Presets Cloudinary deduplicados + test anti-regresión | 2026-08-22 | — |
| `BOLT-06/07/08` | Guardia de tokens CSS, CTA de navbar por tenant, `hero_ctas` compartido | 2026-08-23 | `bbbd99b`, `0725d09`, `c3e9f3c` |
| `CONS-10` | Tests de render de la home por tema (25 tests, 3 temas); destapó `DEUDA-08` (portada sin titular por defecto) | 2026-11-12 | `BOLT-11` |
| `DEUDA-08` | La portada de un sitio nuevo muestra su titular: `get_hero_images` devuelve el slide default con la galería apagada y todas las altas crean la hero con `slot_key='hero'` | 2026-11-14 | `BOLT-19` |
| `DEUDA-06` | Código muerto retirado: `cloudinary_settings.py`, `OrderProcessor` y la copia suelta de `marketing/0001_initial.py`; test guardia `test_dead_code_removed` | 2026-11-14 | `BOLT-25` |
| `DEUDA-09` | Vista `dashboard_services` huérfana borrada con su re-exportación y `dashboard/services.html`; `{% include %}` multilínea del estado vacío de la galería corregido; test guardia de vistas `dashboard_*` sin ruta | 2026-11-15 | `BOLT-43` |
| `DEUDA-12` | Footer default con año actual (`{% now "Y" %}`), fallback de onboarding `themes/default` (antes el slug inválido `default`), `ARQUITECTURA.md` sin `hero_ctas_base` y `hero_overlay.html` huérfanos de default y servelec borrados | 2026-11-18 | `BOLT-66` |
| `COMP-03` | El botón de enviar de los 4 formularios de contacto activa "Enviando..." solo en el `submit` real (no en el clic) y se recupera de error o de volver a la página | 2026-11-15 | `BOLT-42` |
| `COMP-02` | Árbol de temas ordenado: `themes/electricidad` archivado, `andesscale` movido a `themes/andesscale` (`THEME_CHOICES` + migración de datos 0031, loader sin literal), fuera `templates_library/` y 2 componentes vacíos de `themes/default` | 2026-11-17 | `BOLT-56` |
| `COMP-01` (parte) | Componente `cta` compartido en `templates/components/cta.html` (parámetro `variant` orbs/glow); los `home.html` de andesscale y servelec lo incluyen directo y se borraron los `cta.html` de tema; equivalencia de HTML por fixture | 2026-11-17 | `BOLT-57` |
| `COMP-01` (parte) | Componente `about` compartido en `templates/components/about.html` (parámetro `variant` stripe/blocks); los `home.html` de andesscale y servelec lo incluyen directo y se borraron los `about.html` de tema; `themes/default` no tenía componente (renderiza en línea); equivalencia de HTML por fixture | 2026-11-17 | `BOLT-58` |
| `COMP-01` (parte) | Componente `services` compartido en `templates/components/services.html` (parámetros `variant` stripe/adaptive y `subtitle`); los `home.html` de andesscale y servelec lo incluyen directo y se borraron los `services.html` de tema (también el de `themes/default`, que nadie incluía); equivalencia de HTML por fixture | 2026-11-17 | `BOLT-59` |
| `COMP-01` (parte) | Componente `contact` compartido en `templates/components/contact.html` (parámetro `variant` stripe/servelec); los `home.html` de andesscale y servelec lo incluyen directo y se borraron los `contact.html` de tema; equivalencia de HTML por fixture | 2026-11-17 | `BOLT-60` |
| `COMP-01` (parte) | Componente `footer` compartido en `templates/components/footer.html` (parámetro `variant` default/stripe/servelec, marcado en `components/slots/footer_<variant>.html`); los `base.html` de tema lo incluyen directo y se borraron los `footer.html` de tema (el de `themes/default` estaba vacío: ese tema ahora muestra el footer genérico); equivalencia de HTML por fixture | 2026-11-17 | `BOLT-61` |
| `COMP-01` (parte) | Componente `navbar` compartido en `templates/components/navbar.html` (parámetro `variant` simple/default/stripe/servelec, marcado en `components/slots/navbar_<variant>.html`); los `base.html` de tema lo incluyen directo y se borraron los `navbar.html` de tema; equivalencia de HTML por fixture (16 casos) | 2026-11-17 | `BOLT-62` |
| `COMP-01` | Componentes `hero_ctas` y `hero_overlay_theme` compartidos en `templates/components/` (variantes en `components/slots/hero_ctas_<variante>.html` y `hero_overlay_theme_servelec.html`, solo parámetros); se borraron los cuatro archivos de tema; equivalencia de HTML por fixture. Cierra `COMP-01`: quedan en `themes/` solo `hero.html` (3 envoltorios de `media_collection`, justificados) y `hero_overlay.html` (default y servelec, difieren y no los referencia ninguna vista: candidatos a código muerto) | 2026-11-17 | `BOLT-63` |

## Tooling, flujo comercial y operaciones

| ID | Qué resolvió | Fecha | Ref |
|---|---|---|---|
| `#TOOL-01` | Playwright smoke multi-tenant | 2026-08-22 | — |
| `#TOOL-07` | `CLAUDE.md` en la raíz | 2026-08-22 | — |
| `#AUD-10` | Higiene de repo (sqlite/staticfiles/CSVs fuera) + test de presets | 2026-08-22 | — |
| `#DEUDA-05` | README/skill reconciliados con el código; skill `andesscale-saas` creado | 2026-08-22 | `d3bb7ba` |
| `#FLOW-01` | Runbook `Procedimiento_Nuevo_Tenant.md`; `provision_tenant` separaba mal industria/tema | 2026-08-24 | `2025343` |
| `#FLOW-02` | `check_tenant_setup` ampliado como gate de QA | 2026-08-23 | `BOLT-05` |
| `FLOW-04` | `provision_tenant` siempre deja un `Domain` primario (`--domain`, o `<slug>.localhost` en DEBUG, o `<slug>.PREVIEW_DOMAIN`; sin fuente falla antes de crear nada) y se eliminó el paso muerto `--copy-templates`/`--source-template` (`_default`) | 2026-11-15 | `BOLT-44` |
| `TOOL-04` | CI sin doble ejecución (`push` acotado a `develop`/`main`/`agent/**`), `pip-audit==2.10.1` fijado, nota Python 3.11 vs Render 3.11.0 y test de que producción/`build.sh`/`Procfile` no dependen de `django_extensions` | 2026-11-16 | `BOLT-46` |
| `#OPS-01` (código) | `check_tenant_setup --check-dns`; `servelec.andesscale.com` como URL temporal | 2026-09-27 | `feature/dns-check` |
| `#PREV-01..04` | Épica URL temporal `<slug>.andesscale.com`: onboarding, SEO noindex, bypass de "en construcción", `add_preview_domain` | 2026-10-05 | `cf9b46c`, `00d2e73`, `3110f4d` |
| `#OPS-02` | `render.yaml` alineado a Neon (no a Postgres de Render) | 2026-11-08 | — |
| `#OPS-03` | `EMAIL_ASYNC=False` por defecto + `BASE_URL`; variables cargadas en Render; **PR #2 `develop`→`main` mergeado** | 2026-11-09 | `f140bf0` |
| `CONS-03` | Lint preexistente en 0 (`ruff` 60 → 0: autofix seguro + 1 `except` + `per-file-ignores` de settings) | 2026-11-12 | `BOLT-16` |
| `CONS-05` | Flags `enable_blog` y `enable_testimonials` eliminados (modelo, migración `0027`, admin, `list_tenants`, navbar default); `MOD-03` Testimonios descartada | 2026-11-14 | `BOLT-18` |
| `CONS-06` | Helper `tenant_object_or_404` (`apps/core/tenant_objects.py`): único camino para objetos del tenant en `apps/website/views.py`, con guardia estática en tests | 2026-11-14 | `BOLT-28` |
| `CONS-07` | `apps/website/views.py` separado en el paquete `apps/website/views/` (public, sections, services, gallery, contacts, branding, `_shared`; ninguno >400 líneas), con re-exports en `__init__` y nombres de URL congelados en test | 2026-11-14 | `BOLT-29` |
| `CONS-02` | Documentación al día: `CLAUDE.md` con Neon, sin MCP de GitHub y con la ejecución agéntica enlazada; `README.md` raíz reescrito corto; `docs/CLOUDINARY.md` corregido; `.coverage`/`htmlcov/` ignorados; guardia `test_docs_drift` | 2026-11-14 | `BOLT-31` |
| `CONS-11` (parte) | Cobertura de `tenants` núcleo (middleware + managers) de 83,9 % a 100 %: `apps/tenants/tests_managers.py` (16 tests: `for_client`/`active`/`featured`/`ordered` con y sin atributo; atajo `?tenant=` con DEBUG y ignorado sin DEBUG; headers SEO de preview; dominios de sistema) | 2026-11-15 | `BOLT-36` |
| `CONS-11` (parte) | Cobertura de `apps/orders/` de 70,4 % a 92,5 %: tests sin red de `MercadoPagoService` (SDK mockeado), ramas de checkout/webhook, onboarding y modelos; destapó y corrigió 2 bugs reales (`except mercadopago.exceptions…` inexistente → `AttributeError` en vez de `MercadoPagoError`; templates `checkout_success.html`/`checkout_error.html` fuera de `orders/` → 500 tras cada pago aprobado) | 2026-11-15 | `BOLT-37` |
| `CONS-11` (parte) | Cobertura de `core` y servicios de `tenants` (total 69,2 % → 74,8 %): tests sin red de `cloudinary_utils`, `EmailDispatcher` (locmem + mock SMTP) y los template tags de `tenant_tags`, `website_tags` y `cloudinary_tags`; destapó y corrigió 3 bugs (`cloudinary.api` sin importar → `get_tenant_usage` fallaba con `AttributeError`; tags `get_testimonials`/`get_featured_testimonials` huérfanos que lanzaban `ImportError`; el comentario de `tenant_include` salía escapado y visible) | 2026-11-15 | `BOLT-38` |
| `CONS-11` | Cobertura al contrato cerrada: total 74,8 %, `orders` 92,5 %, `tenants` núcleo 100 % (baseline actualizado). Quedan sin tests los comandos de gestión con 0 % (`audit_cloudinary_assets`, `check_cloudinary`, `create_tenant`, `cloudinary_usage`, `verify_search_console`, `setup_cloudinary_folders`, `setup_dev_env`, `seed_e2e_tenants`), fuera del contrato | 2026-11-15 | `BOLT-39` |
| `CONS-04` | Edición inline pública eliminada (7 rutas, vistas, 6 templates legacy); `delete_service_dashboard` renderizaba un template inexistente (`dashboard/delete_service.html`) y ahora usa `service_confirm_delete.html` con el `{% url %}` corregido | 2026-11-14 | `BOLT-21` |
| `CONS-12` | Guardia estática de objetos de tenant extendida a `orders` y `accounts` con lista explícita de excepciones justificadas; corregida fuga: recuperar contraseña desde el dominio de A ya no dispara el reset de un usuario de B (respuesta idéntica, sin enumeración) | 2026-11-15 | `BOLT-40` |
| `CONS-08` | Registro de módulos (`apps/tenants/modules.py`): `core`, `services`, `gallery` y `contact` con flag, límite, rutas del dashboard y entradas de menú; test de cobertura de rutas (`apps.tenants.tests_modules`). Solo declara, sin cambio de comportamiento; `dashboard_portada` queda en `gallery` porque su vista exige `enable_gallery` | 2026-11-17 | `BOLT-52` |
| `CONS-09` | Menú y acceso del dashboard desde el registro de módulos: decorador `module_required` (404 con el módulo apagado, bajo `tenant_permission_required`), context processor `dashboard_menu` y `base.html` que recorre la lista; con la galería apagada Portada/Galería desaparecen (antes atenuadas; Portada vive en `gallery`); con el contacto apagado `contact_submit` da 404 y el formulario público no se renderiza, pero Mensajes sigue accesible (`apps.tenants.tests_module_access`) | 2026-11-17 | `BOLT-53` |
| `BIZ-01` | Límites del plan con efecto real: `limit_for`/`usage_for`/`check_limit` y `ModuleLimitReached` en `apps/tenants/modules.py`; `create_service` y `gallery_item_add` se niegan al tope con "Tu plan permite N …", la galería usa el menor entre `gallery_images_limit` y `max_images`, la UI muestra "N de M" y deshabilita el botón de servicios; editar/borrar nunca se bloquean y el admin no se limita (`apps.tenants.tests_module_limits`). `max_pages` queda sin aplicar (`DEUDA-11`) | 2026-11-17 | `BOLT-54` |
| `DOC-01` | Documentación al día tras las rondas 4 a 8: ARQUITECTURA (paquete `views/`, Build Command `./build.sh`, variables obligatorias, Render no sincroniza `render.yaml`), SEGURIDAD (hallazgos cerrados pasan a controles; bandit en 0), INDEX, MASTER_PLAN y `Documentacion/README.md` sin código borrado ni auto-filtro de manager; guardia `test_docs_vigentes` | 2026-11-16 | `BOLT-47` |
| `OPS-04` | Alerta de créditos de Cloudinary: `CLOUDINARY_ALERT_THRESHOLDS` (70/90) y `PLATFORM_ALERT_EMAIL` en settings; `cloudinary_usage --alert` envía un correo de aviso/alerta y `send_contact_digest` lo ejecuta una vez por corrida (no en `--dry-run`, sin bloquear el digest) | 2026-11-16 | `BOLT-51` |
| `TOOL-08` | `test_gatekeeper` sin falsos rojos: tope de 900 s (sobrescribible con `GATEKEEPER_TEST_TIMEOUT_S`), una sola corrida del gate para la clase sana (cacheada en `setUpClass`) y `TimeoutExpired` convertido en fallo que sugiere subir el tope (`apps.core.tests.test_gatekeeper_runtime`) | 2026-11-18 | `BOLT-65` |

## Rancho Cachimba (en pausa — rama `feature/RanchocachimbaEtapa1`)

| ID | Qué resolvió | Fecha |
|---|---|---|
| `#RC-02`..`#RC-07` | Gate galería, tokens de marca, tema + rubro `turismo_rural`, hero split, navbar/footer/contacto | 2026-08 |
| `#RC-20` / `RC-BOLT-01..06` | Hero según mockup: tokens CSS corregidos (143 usos), tartán, navbar oscuro + CTA, barra de utilidad, stats, CTAs (`6a43eaf`..`5af0a6c`) | 2026-08-23 |

## Piloto agéntico (`docs/kanban_agente.md`, §4 = registro de ejecución)

`PILOT-01..03` (gatekeeper, prompts por rol, orquestador) y `BOLT-01..10` DONE; mergeado a `develop` en `45eca7b` (2026-08-24; `BOLT-10` el 2026-09-01).

## Negocio y organización

- **Modelo comercial consolidado** (2026-09/11): pago único + mantención 12 meses + renovación anual negociada (no suscripción) — `MASTER_PLAN_Y_ARQUITECTURA.md` §3–4.
- **Unificación de repo + PyCharm** (2026-11-08): un solo checkout en `develop`.
- **Refocus de plataforma** (2026-11-09): módulos + dashboard de medios amigable; sin biblioteca de UI (Tailwind + htmx).
- **Reorganización de documentación** (2026-11-11): kanban unificado, snapshot y archivos obsoletos a `Documentacion/historico/`.
- **`MOD-00` decidido** (2026-11-12): composición de página = opción A ahora (registro de módulos, home por tema), B después (`MOD-02`), page-builder descartado. Detalle en `AUDITORIA_PLATAFORMA_2026-11.md` §4.
- **Chequeo de ciberseguridad y plan trimestral** (2026-11-12): `SEGURIDAD.md`, `ARQUITECTURA.md`, diccionario de nomenclaturas y plan de ejecución por fases en el kanban; orden "seguridad y ley primero".
