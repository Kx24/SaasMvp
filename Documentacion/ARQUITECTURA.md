# Arquitectura — AndesScale SaaS

> Actualizado 2026-11-12 leyendo el código de `develop`. Reemplaza a `ARQUITECTURA_SISTEMA.md` (2026-09, en [`historico/auditorias_y_manuales/`](historico/auditorias_y_manuales/ARQUITECTURA_SISTEMA_2026-09.md)).
> Qué es: un solo despliegue Django que sirve los sitios web de varios clientes (*tenants*), cada uno resuelto por dominio, con un dashboard común para que el cliente administre su sitio.
> Complementos: [`SEGURIDAD.md`](SEGURIDAD.md) (controles y hallazgos), [`AUDITORIA_PLATAFORMA_2026-11.md`](AUDITORIA_PLATAFORMA_2026-11.md) (brecha contra el objetivo modular), [`../docs/design-system.md`](../docs/design-system.md) (contrato de temas), [`../CLAUDE.md`](../CLAUDE.md) (cómo trabajar en el repo).

## 1. Ciclo de un request

```
Navegador → Cloudflare (DNS) → Render (gunicorn) → Django
  1. SecurityMiddleware / WhiteNoise (estáticos) / sesión / CSRF / auth
  2. apps/tenants/middleware.py::TenantMiddleware
       Host → Domain (allowlist dinámica) → request.client
       localhost y dominios de sistema → request.client = None
       mode_under_construction → página "en construcción" (salvo dominio is_preview)
  3. Vista (apps/website/views.py, etc.) → SIEMPRE filtra .filter(client=request.client)
  4. apps/core/template_resolver.py::render_tenant_template(request, 'landing/home.html', ctx)
  5. apps/tenants/template_loader.py::TenantTemplateLoader
       templates/{client.template}/landing/home.html   (tema del cliente)
       templates/landing/home.html                     (fallback global)
  6. HTML + CSS compilado (static/css/output.css) + variables CSS de marca del tenant
```

Dos superficies sobre el mismo código: **sitio público** (`/`, distinto por tema) y **dashboard** (`/dashboard/`, igual para todos, requiere login y pertenencia al tenant).

## 2. Stack: cada tecnología y qué hace

| Tecnología | Qué hace en este proyecto | Dónde vive |
|---|---|---|
| **Python + Django 5.2** (Render fija `PYTHON_VERSION=3.11.0`; el entorno local corre 3.13 — desalineado, `SEC-10`) | Framework web: modelos (ORM), vistas, templates, admin, auth, sesiones, migraciones | `config/`, `apps/` |
| **PostgreSQL en Neon** | Base de datos de producción (serverless). Se conecta por `DATABASE_URL` | `config/settings/production.py` vía `dj_database_url` |
| **SQLite** | Base local de desarrollo (`db.sqlite3`) y de pruebas E2E (`db_e2e.sqlite3`) | `config/settings/development.py`, `e2e.py` |
| **Render** | Hosting: un web service `saasmvp`. `render.yaml` declara además 2 crons (`contact-digest`, `send-pending-emails`) que **hoy no existen** en el dashboard real (`OPS-06`) | `render.yaml`, `build.sh`, `Procfile` |
| **gunicorn** | Servidor WSGI que ejecuta Django en Render | `startCommand` en `render.yaml` |
| **WhiteNoise** | Sirve los archivos estáticos (CSS/JS) desde el mismo proceso | `MIDDLEWARE` en `base.py` |
| **Cloudinary** | Almacena y transforma imágenes/video (recortes, formatos, `srcset`). Carpeta por tenant: `tenants/{slug}/…` | `apps/core/cloudinary_utils.py` (único punto de entrada), `apps/website/templatetags/cloudinary_tags.py` |
| **Tailwind CSS 3** | Estilos por utilidades, **compilado** en el build (no CDN). Los colores/fuentes apuntan a variables CSS, no a valores fijos | `tailwind.config.js`, `static/css/input.css` → `output.css`, `npm run build:css` |
| **Variables CSS de marca** | `ClientSettings` (colores, fuente, logo) se inyecta en `:root` de cada `base.html`; así un mismo tema toma la marca de cada cliente | `templates/**/base.html`, `apps/tenants/fonts.py` |
| **Alpine.js 3.16** | Interactividad pequeña en el navegador (menús, drawer móvil, toggles) | `<script>` en los `base.html` |
| **htmx 1.9** | Actualizar partes de la página sin recargar. Cargado en el dashboard pero casi sin uso (`DASH-03`) | `templates/dashboard/base.html`, `templates/partials/` |
| **MercadoPago (SDK 2.3)** | Cobro del plan con Checkout Bricks + webhook firmado. Hoy **apagado a propósito** (sin `MP_*`) | `apps/orders/services/mercadopago_service.py`, `apps/orders/views.py` |
| **Zoho Mail (SMTP)** | Envío de correo transaccional | `EMAIL_*` en `production.py`; `apps/orders/services/email_service.py::EmailService` |
| **`EmailOutbox`** | Cola de correo en base de datos (envío diferido por cron). Hoy `EMAIL_ASYNC=False`: se envía directo | `apps/core/models.py`, comando `send_pending_emails` |
| **Cloudflare** | DNS de `andesscale.com` y subdominios de preview `<slug>.andesscale.com` | Fuera del repo; ver `Procedimiento_Nuevo_Tenant.md` |
| **django-csp / django-permissions-policy** | Cabeceras de seguridad (CSP, Permissions-Policy) solo en producción | `config/settings/security_headers.py` |
| **Playwright + axe-core** | Pruebas E2E de humo por tenant y accesibilidad WCAG AA | `tests/e2e/`, `playwright.config.js` |
| **ruff / bandit / coverage** | Lint, análisis estático de seguridad, cobertura | `ruff.toml`, `requirements-dev.txt` |
| **PyCharm** | IDE principal; desde ahí se hace push y PR | `.idea/runConfigurations/` |

Sin uso real hoy (candidatos a retirar, `DEUDA-06`/`SEC-10`): `djangorestframework`, `django-extensions` e `ipython` en `requirements.txt`, `config/settings/cloudinary_settings.py`.

## 3. Apps Django

| App | Responsabilidad | Piezas clave |
|---|---|---|
| `apps/tenants` | Quién es el cliente: resolución por dominio, marca, configuración, alta de tenants | `middleware.py`, `template_loader.py`, `managers.py`, `fonts.py`, `templatetags/seo_tags.py`, comandos de provisioning |
| `apps/website` | Contenido del sitio y dashboard del cliente | `models.py`, `views.py` (1.099 líneas, a separar en `CONS-07`), `forms.py`, `auth_views.py` |
| `apps/accounts` | Perfil de usuario ↔ tenant, roles, invitación/contraseña | `models.py::UserProfile`, `decorators.py::tenant_member_required`, `mixins.py::TenantAdminMixin` |
| `apps/orders` | Planes, checkout, webhook, onboarding post-pago, correo | `models.py`, `views.py`, `views_onboarding.py`, `services/` |
| `apps/marketing` | SEO por página, `sitemap.xml`, `robots.txt`, verificación de Google | `models.py::SEOConfig`, `views_robots.py` |
| `apps/core` | Utilidades transversales | `cloudinary_utils.py`, `rate_limit.py`, `template_resolver.py`, `models.py::EmailOutbox` |

**Comandos de gestión:** `provision_tenant`, `check_tenant_setup` (gate de QA, `--check-dns`), `list_tenants`, `add_preview_domain`, `update_domain`, `create_tenant`, `setup_production`, `setup_dev_env`, `seed_e2e_tenants`, `setup_cloudinary_folders`, `send_contact_digest` (tenants) · `send_pending_emails`, `cloudinary_usage`, `check_cloudinary`, `audit_cloudinary_assets` (core) · `setup_plans` (orders) · `verify_search_console` (marketing).

## 4. Modelo de datos

```
Client (tenant) ─┬─ 1:N  Domain
                 ├─ 1:1  ClientSettings        (marca, flags, límites de galería)
                 ├─ 1:1  ClientEmailSettings   (SMTP/API propios del cliente)
                 ├─ 1:1  FormConfig            (campos del formulario de contacto)
                 ├─ 1:N  Section ──┐
                 ├─ 1:N  Service ──┼─ 1:N  GalleryItem (pertenece a una Section O a un Service)
                 ├─ 1:N  ContactSubmission     (leads del sitio)
                 ├─ 1:N  SEOConfig             (uno por página: client + page_key)
                 ├─ 1:N  UserProfile ── 1:1 ── User (auth de Django)
                 └─ 1:N  Order ── N:1 Plan
                              └─ 1:N PaymentLog
EmailOutbox  (cola global, sin FK a Client)
```

| Modelo | Para qué | Campos clave | Datos personales |
|---|---|---|---|
| `tenants.Client` | El cliente/tenant | `slug`, `template` (tema: `themes/default` \| `themes/servelec`), `plan` (**texto, no FK a `Plan`**), `is_active`, `mode_under_construction`, `max_images/pages/services` (sin efecto, `BIZ-01`), `monthly_fee`/`next_payment_due` (modelo de cobro viejo, `BIZ-02`) | Email y teléfono de contacto |
| `tenants.Domain` | Dominios que resuelven a un tenant | `domain`, `is_primary`, `is_active`, `is_preview` (noindex + salta "en construcción"), `domain_type` | — |
| `tenants.ClientSettings` | Marca y configuración del sitio | `logo`, `primary/secondary/accent_color`, `font_family`, `navbar_cta_*`, redes, `enable_blog/testimonials/contact_form/gallery`, `hero_images_limit`, `gallery_images_limit`, `digest_*`, `inbox_retention_days` | — |
| `tenants.ClientEmailSettings` | Envío de correo propio del cliente | `provider`, `smtp_*`, `api_key`, `notify_mode`, `notify_emails` | **Credenciales en texto plano** (`SEC-06`) |
| `tenants.FormConfig` | Qué campos muestra el formulario de contacto | `show_*`/`*_required`/`*_label`, `privacy_text`, `success_message` | — |
| `website.Section` | Bloque de contenido del sitio | `section_type` (`hero`/`about`/`service`/`contact`/`gallery`), `title`, `description`, `image`, `background_image`, `order`, `slot_key`. **Único por `(client, section_type)`** | — |
| `website.Service` | Servicio ofrecido | `name`, `slug` (único por cliente), `description`, `icon`, `image`, `price_text`, `order`, `is_featured` | — |
| `website.GalleryItem` | Imagen de una galería | `section` **o** `service` (exactamente uno), `image`, `title`, `caption`, `cta_*`, `order` | — |
| `website.ContactSubmission` | Mensaje recibido por el formulario | `status`, `is_spam`, `source` | **Nombre, email, teléfono, empresa, mensaje, IP, user-agent** |
| `accounts.UserProfile` | Une un `User` con su tenant | `client`, `role` (`owner`/`admin`/`editor`, hoy sin efecto, `DASH-04`), `invitation_token` | Vía `User`: email, nombre |
| `orders.Plan` | Plan comercial | `price`, `renewal_price`, `features`, `available_themes`, `max_*`, `has_*` | — |
| `orders.Order` | Compra de un plan | `order_number`, `status`, `mp_*`, `onboarding_token`, `client` (se llena al crear el sitio) | **Email, nombre, teléfono, RUT, razón social, dirección, IP** |
| `orders.PaymentLog` | Bitácora de eventos de pago | `action`, `status`, `raw_data` | **IP y payload crudo del pago** |
| `marketing.SEOConfig` | SEO por página | `page_key`, `title`, `meta_description`, `og_image`, `schema_json`, verificación | — |
| `core.EmailOutbox` | Correos pendientes/enviados | `status`, `attempts`, `html_content` | **Destinatario y cuerpo completo**, sin purga (`LEY-03`) |

**Aislamiento:** no hay filtro automático por tenant. `TenantAwareManager` solo ofrece `for_client(client)`; cada vista debe filtrar. Dashboard: `tenant_member_required`. Admin: `TenantAdminMixin` (aplicado solo en `apps/website/admin.py`, ver `SEC-05`).

## 5. Temas, componentes y página pública

- **Tema** = carpeta bajo `templates/` con `base.html`, `landing/home.html` y `components/`. Existen `themes/default`, `themes/servelec`, `themes/electricidad` (no elegible en `THEME_CHOICES`) y `andesscale/` (fuera de `themes/`; es el sitio propio). `ranchocachimba` vive solo en su rama.
- **Componentes compartidos** (`templates/components/`): `navbar`, `navbar_cta`, `footer`, `hero_gallery`, `hero_ctas_base`, `media_collection`, `media_item`, `contact_multistep`, `slots/`. Patrón de referencia: `media_collection.html` (parámetro `mode` + slots de override).
- **Hoy la home no es modular:** `apps/website/views.py::home` entrega `hero`, `about`, `contact_section`, `services` y cada tema arma su página a mano. Objetivo y camino: registro de módulos (opción A, `CONS-08`) y después orden/visibilidad de bloques (opción B, `MOD-02`).
- Emails: plantillas HTML + texto en `templates/emails/`.

## 6. Flujos principales

| Flujo | Recorrido |
|---|---|
| **Login del cliente** | `/auth/login/` → `apps/website/auth_views.py::client_login` (rate limit por IP+usuario+tenant; exige `UserProfile.client == request.client`) → `/dashboard/` |
| **Dashboard** | `apps/website/urls.py`: Inicio, Branding, Portada, Galería, Secciones (incluye servicios) y Contactos. Formularios `multipart` con recarga completa; subida de imagen pasa por Django → `upload_to_cloudinary` |
| **Formulario de contacto** | `contact_submit`: rate limit 3/10 min + honeypot → `ContactSubmission` → notificación según `ClientEmailSettings.notify_mode` → digest semanal opcional |
| **Compra y onboarding** | `/checkout/<plan>/` → `process/` (MercadoPago) → webhook firmado `/webhook/mercadopago/` → email con token → `/onboarding/<token>/` crea `Client` + `Domain` de preview + `UserProfile(owner)` + secciones semilla. Correos siempre dentro de `transaction.on_commit` |
| **Alta manual** | `provision_tenant <slug> --industry --theme` → `check_tenant_setup <slug>` (runbook: `Procedimiento_Nuevo_Tenant.md`) |
| **SEO** | `seo_tags` (meta + JSON-LD desde `SEOConfig`), `sitemap.xml` y `robots.txt` por tenant; dominios `is_preview` salen con `noindex` |
| **Admin interno** | `/superadmin/` (Django Admin) + `/superadmin/nuevo/` y `/tenants/` (`apps/tenants/views.py`, solo `is_staff`) |

## 7. Entornos, despliegue y calidad

- **Settings:** `base.py` (común) → `development.py` (SQLite, `DEBUG`) · `production.py` (falla al importar sin `SECRET_KEY`/`EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`; `DEBUG=False` fijo; `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` derivados de la misma lista de dominios) · `e2e.py` (Playwright). Selección por `DJANGO_ENVIRONMENT`.
- **Build en Render** (`build.sh`): `pip install` → `npm ci && npm run build:css` → `collectstatic` → `migrate` → `setup_production`.
- **Ramas:** `main` = producción (deploy automático en Render), `develop` = integración.
- **Variables y secretos:** inventario en [`Inventario_Secretos.md`](Inventario_Secretos.md).
- **Calidad:** 219 tests (`python manage.py test apps`), suite de aislamiento (`apps.tenants.tests_isolation`), Playwright (humo + a11y). El gate se corre **a mano**; no hay CI todavía (`SEC-12`). Reglas: sección "Arnés de TDD" del kanban.

## 8. Limitaciones conocidas (enlazadas al kanban)

Composición de página fija por tema (`CONS-08`, `MOD-02`) · sin modelo de medios ni video (`MOD-01`) · subida de archivos de a uno y por el servidor (`MOD-01`) · roles sin efecto (`DASH-04`) · cache y rate limiter en memoria del proceso (`OPS-05`) · sin crons en Render (`OPS-06`) · sin backups con restore probado (`DB-02`) · hallazgos de seguridad en [`SEGURIDAD.md`](SEGURIDAD.md).
