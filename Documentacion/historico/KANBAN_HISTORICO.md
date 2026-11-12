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

## Tooling, flujo comercial y operaciones

| ID | Qué resolvió | Fecha | Ref |
|---|---|---|---|
| `#TOOL-01` | Playwright smoke multi-tenant | 2026-08-22 | — |
| `#TOOL-07` | `CLAUDE.md` en la raíz | 2026-08-22 | — |
| `#AUD-10` | Higiene de repo (sqlite/staticfiles/CSVs fuera) + test de presets | 2026-08-22 | — |
| `#DEUDA-05` | README/skill reconciliados con el código; skill `andesscale-saas` creado | 2026-08-22 | `d3bb7ba` |
| `#FLOW-01` | Runbook `Procedimiento_Nuevo_Tenant.md`; `provision_tenant` separaba mal industria/tema | 2026-08-24 | `2025343` |
| `#FLOW-02` | `check_tenant_setup` ampliado como gate de QA | 2026-08-23 | `BOLT-05` |
| `#OPS-01` (código) | `check_tenant_setup --check-dns`; `servelec.andesscale.com` como URL temporal | 2026-09-27 | `feature/dns-check` |
| `#PREV-01..04` | Épica URL temporal `<slug>.andesscale.com`: onboarding, SEO noindex, bypass de "en construcción", `add_preview_domain` | 2026-10-05 | `cf9b46c`, `00d2e73`, `3110f4d` |
| `#OPS-02` | `render.yaml` alineado a Neon (no a Postgres de Render) | 2026-11-08 | — |
| `#OPS-03` | `EMAIL_ASYNC=False` por defecto + `BASE_URL`; variables cargadas en Render; **PR #2 `develop`→`main` mergeado** | 2026-11-09 | `f140bf0` |

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
