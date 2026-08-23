corre# AndesScale — Documentación Técnica
 
> Plataforma SaaS multi-tenant para gestión de presencia web de pymes en Chile y Latinoamérica.
 
---
 
## Tabla de Contenidos
 
1. [Descripción del Proyecto](#1-descripción-del-proyecto)
2. [Arquitectura General](#2-arquitectura-general)
3. [Estructura de Carpetas](#3-estructura-de-carpetas)
4. [Módulos del Sistema](#4-módulos-del-sistema)
5. [Funciones y Métodos Clave](#5-funciones-y-métodos-clave)
6. [Integraciones Externas](#6-integraciones-externas)
7. [Flujos Principales](#7-flujos-principales)
8. [Instalación Local](#8-instalación-local)
9. [Despliegue en Producción](#9-despliegue-en-producción)
10. [Estado del Kanban](#10-estado-del-kanban)
---
 
## 1. Descripción del Proyecto
 
AndesScale es una plataforma SaaS (Software as a Service) construida sobre Django que permite a pequeñas y medianas empresas (pymes) obtener y administrar su presencia web de forma sencilla, rápida y autoadministrable.
 
### Modelo de negocio
 
- **Fee inicial:** Diseño y configuración del sitio.
- **Suscripción anual:** Hosting, soporte y renovación.
- **Módulos diferenciales:** Catálogo, reservas, chatbot, pagos (según plan).
### Tenants activos en producción
 
| Dominio | Descripción | `Client.template` |
|---|---|---|
| `andesscale.com` | Landing page del SaaS (el producto mismo) | `andesscale` (marca propia, resuelto aparte por el loader) |
| `servelec-ingenieria.cl` | Cliente 1 — empresa de ingeniería eléctrica | `servelec` |
| Rancho Cachimba (`ranchocachimba.cl`, aún no publicado) | Turismo rural — lanzamiento en pausa (`feature/RanchocachimbaEtapa1`) | `ranchocachimba` |
 
### Stack tecnológico
 
| Capa | Tecnología |
|---|---|
| Backend | Django 5.2, Python 3.11 |
| Frontend | Tailwind CSS, Alpine.js, HTMX |
| Base de datos | Neon (PostgreSQL serverless) |
| Media | Cloudinary (imágenes + video) |
| Pagos | MercadoPago |
| Hosting | Render (auto-deploy desde GitHub) |
| DNS / SSL | Render + proveedor de dominio externo |
 
---
 
## 2. Arquitectura General
 
```
┌─────────────────────────────────────────────────────────┐
│                    REQUEST HTTP                          │
└────────────────────────┬────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │ TenantMiddleware│  ← detecta tenant por dominio
                │  (apps/tenants) │    inyecta request.client
                └────────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
   ┌──────▼──────┐ ┌─────▼──────┐ ┌───▼──────────┐
   │  apps/      │ │  apps/     │ │  apps/        │
   │  website/   │ │  orders/   │ │  marketing/   │
   │  (CMS)      │ │  (pagos)   │ │  (SEO)        │
   └──────┬──────┘ └─────┬──────┘ └───┬──────────┘
          │              │            │
          └──────────────┼────────────┘
                         │
              ┌──────────▼──────────┐
              │     apps/core/      │  ← BaseModel, TenantAwareManager,
              │  (utilidades base)  │     cloudinary_utils, template_resolver
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
   ┌─────▼─────┐  ┌──────▼──────┐ ┌─────▼──────┐
   │ Cloudinary│  │  Neon DB    │ │MercadoPago │
   │  (media)  │  │ (PostgreSQL)│ │  (pagos)   │
   └───────────┘  └─────────────┘ └────────────┘
```
 
### Patrón multi-tenant
 
Cada request pasa por `TenantMiddleware` (`apps/tenants/middleware.py`), que detecta el tenant activo según el dominio HTTP (o el parámetro `?tenant=slug`, solo con `DEBUG=True`) y lo deja en `request.client` — además lo guarda en un thread-local (`set_current_tenant`/`get_current_tenant`) que usa el `TenantTemplateLoader` para resolver temas. Un dominio de sistema (`localhost`, `BASE_DOMAIN`, `*.onrender.com`) pasa con `request.client = None`; un dominio desconocido devuelve 404 antes de llegar a ninguna vista.

> ⚠️ **`TenantAwareManager` NO filtra automáticamente por tenant** (se eliminó ese comportamiento en `#MED-02`, 2026-08-22 — el auto-filtro dependía de un atributo de clase `_current_client` que nunca se seteaba en código de request real y era un riesgo real de fuga entre tenants concurrentes). **Toda vista debe filtrar explícitamente** con `.filter(client=request.client)` o `Model.objects.for_client(client)`. No asumir que `Model.objects.all()` está scoped por tenant.

```
petición → TenantMiddleware → request.client → View (filtra .filter(client=request.client) a mano) → DB
```
 
### Sistema de temas (templates)
 
Cada tenant tiene asignado un `template` (campo en `Client`, no en `ClientSettings`; valores válidos: `Client.THEME_CHOICES` — hoy `'themes/default'`, `'servelec'`, `'ranchocachimba'`). `TenantTemplateLoader` (`apps/tenants/template_loader.py`) resuelve cada `template_name` en este orden:

1. Si el tenant es `andesscale` (marca propia): `templates/andesscale/{template_name}` → `templates/{template_name}` (sin tier `default/` intermedio).
2. Para cualquier otro tenant: `templates/{client.template}/{template_name}` → `templates/default/{template_name}` (fallback genérico) → `templates/{template_name}` (fallback global — así resuelven `base.html`, `templates/components/*.html`, `templates/emails/*.html`).
3. Sin tenant (`request.client is None`): solo `templates/{template_name}`.

```
request.client.template → "servelec"
TenantTemplateLoader → templates/servelec/landing/home.html

request.client.template → "themes/default"
TenantTemplateLoader → templates/themes/default/landing/home.html
```

Las vistas llaman `apps.core.template_resolver.render_tenant_template(request, template_path, context)` — esta función **ya no arma rutas a mano**, solo delega en `render()` de Django y deja que el loader haga la resolución.

> No confundir con `--industry` de `provision_tenant` (rubro/contenido semilla: colores y textos). El campo `template`/`--theme` es exclusivamente la carpeta visual.
 
---
 
## 3. Estructura de Carpetas
 
```
project_root/
├── manage.py
├── requirements.txt
├── .env                        # Variables de entorno (nunca commitear)
├── .gitignore
├── README.md
├── Procfile                    # Comando de inicio para Render
│
├── config/                     # ⚙️ Configuración Django
│   ├── urls.py                 # Router principal (orden de prioridad crítico)
│   └── settings/
│       ├── base.py             # Settings compartidos
│       ├── development.py      # DEBUG=True, DB local/SQLite
│       ├── production.py       # DEBUG=False, vars de entorno
│       └── cloudinary_setting.py
│
├── apps/                       # 🎯 Módulos por dominio de negocio
│   ├── tenants/                # Core multi-tenancy
│   ├── website/                # CMS y landing pages públicas
│   ├── accounts/               # Usuarios y autenticación
│   ├── core/                   # Utilidades compartidas
│   ├── orders/                 # Pagos y onboarding
│   └── marketing/              # SEO, sitemap, robots.txt
│
├── templates/                   # Templates globales, resueltos por TenantTemplateLoader
│   ├── themes/default/          # Tema base genérico
│   ├── servelec/                # Tema del cliente Servelec (rubro electricidad)
│   ├── ranchocachimba/          # Tema Rancho Cachimba (turismo rural, en pausa)
│   ├── andesscale/              # Marca propia del SaaS (landing de producto)
│   ├── components/              # Componentes compartidos entre 2+ temas (docs/design-system.md)
│   ├── dashboard/                # Panel CMS del cliente
│   ├── emails/                  # Templates de email transaccional
│   ├── errors/                  # Páginas de error (incl. under_construction.html)
│   └── partials/                # Fragmentos reutilizados entre temas (ej. contact_form.html)
│
├── static/                     # Assets compilados (CSS, JS, img) — pipeline Tailwind (#AUD-11)
├── media/                      # Uploads locales (solo dev)
├── scripts/                    # Scripts de utilidad y mantenimiento
├── tests/e2e/                  # Smoke Playwright multi-tenant (#TOOL-01)
└── docs/                       # design-system.md: contrato de tema y librería de componentes
```
 
### Detalle de carpetas clave
 
| Carpeta | Rol | Tipo |
|---|---|---|
| `config/` | Configuración Django, settings, URLs raíz | Core |
| `apps/tenants/` | Modelo Client, middleware, provisioning | Core |
| `apps/website/` | CMS: Section, Service, ContactSubmission | Core |
| `apps/accounts/` | UserProfile, autenticación, roles | Core |
| `apps/core/` | `BaseModel`, `EmailOutbox`, Cloudinary helpers, `template_resolver` | Auxiliar |
| `apps/orders/` | Checkout MercadoPago, onboarding post-pago | Auxiliar |
| `apps/marketing/` | SEO, sitemap, robots.txt, Search Console | Auxiliar |
| `templates/{tema}/` | Un directorio por tema visual (`servelec`, `ranchocachimba`, `andesscale`, `themes/default`) | Presentación |
| `templates/dashboard/` | Panel de administración del cliente | Presentación |
| `templates_library/` | Scaffolding de seed data por industria — hoy solo carpetas vacías (`.gitkeep`), sin contenido real | Datos |
| `scripts/` | Automatización, migración, tests manuales | DevOps |
 
---
 
## 4. Módulos del Sistema
 
### 4.1 `apps/tenants/` — Core Multi-Tenancy
 
**Propósito:** Gestionar el ciclo de vida completo de un tenant: creación, detección por dominio, configuración de branding, y aislamiento de datos.
 
**Es el módulo núcleo del sistema.** Todos los demás módulos dependen de él.
 
**Modelos principales:**
 
| Modelo | Descripción |
|---|---|
| `Client` | Representa un tenant. Campos: `name`, `slug`, `plan`, `template` (tema visual, `THEME_CHOICES`), `is_active`, `contact_email` |
| `Domain` | Dominios asociados a un Client (uno-a-muchos, uno marcado `is_primary`) |
| `ClientSettings` | Branding: colores (`primary`/`secondary`/`accent`), logo/favicon/logo_footer, `font_family` (lista curada, `#AUD-11`), tagline, descripción, SEO básico. **No** tiene el campo `template` — el tema visual vive en `Client.template`, no acá. |
| `ClientEmailSettings` | Configuración de envío por tenant (SMTP propio, SendGrid/Resend/Mailgun/SES, o solo dashboard) |
| `FormConfig` | Qué campos muestra el formulario de contacto del tenant y sus opciones |
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `middleware.py` | `TenantMiddleware`: detecta tenant por dominio, inyecta `request.client` y el thread-local que usa el loader |
| `template_loader.py` | `TenantTemplateLoader`: resuelve rutas de templates por tema del tenant (ver §2) |
| `context_processors.py` | Inyecta `client` y `current_year` en el contexto de cada template |
| `signals.py` | Al crear un `Client`, auto-crea `ClientSettings` + `ClientEmailSettings` + `FormConfig` (`get_or_create`, idempotente) |
| `tenant_tags.py` | Tags de media/template por tenant: `{% tenant_static %}`, `{% tenant_media %}`, `{% get_tenant_media_url %}`, `{% tenant_include %}`, `{% get_tenant_slug %}`. Los tokens de marca (colores/fuente) se inyectan como CSS custom properties directamente en cada `base.html` de tema, no vía un tag — el tag `{% tenant_custom_css %}` que existía antes se retiró por completo (`#AUD-11` Paso 4, código muerto). |
 
**Comandos de management:**
 
```bash
python manage.py create_tenant             # Crea tenant interactivo
python manage.py provision_tenant          # Provisionamiento completo con seed data (--industry / --theme)
python manage.py list_tenants              # Lista todos los tenants con su estado
python manage.py update_domain             # Actualiza el dominio principal de un tenant
python manage.py check_tenant_setup        # Audita theme/dominio/email/SEO de un tenant (gate de QA)
python manage.py check_cloudinary          # Verifica configuración Cloudinary (apps/core)
python manage.py cloudinary_usage          # Reporte de uso de Cloudinary (apps/core)
python manage.py setup_cloudinary_folders  # Crea la estructura de carpetas en Cloudinary para un tenant
python manage.py send_contact_digest       # Cron: resumen periódico de mensajes de contacto por tenant
```

> No existe un comando `test_isolation` — se eliminó (`#MED-02`, 2026-08-22) junto con el auto-filtro que probaba; el aislamiento real se verifica con `python manage.py test apps.tenants.tests_isolation` (suite automática, corre en cada push).
 
**Relación con otros módulos:** Provee `request.client` a `website`, `accounts`, `orders` y `marketing`. Es la dependencia base de todo el sistema.
 
---
 
### 4.2 `apps/website/` — CMS y Landing Pages
 
**Propósito:** Gestionar el contenido público de cada tenant (secciones, servicios, contacto) y renderizar las landing pages según el tema configurado.
 
**Modelos principales:**
 
| Modelo | Descripción |
|---|---|
| `Section` | Bloque de contenido: hero, about, galería, etc. Campos: `section_type`, `title`, `description`, `full_description`, imagen Cloudinary |
| `Service` | Servicio ofrecido por el tenant. Campos: `name`, `description`, imagen |
| `ContactSubmission` | Formulario de contacto recibido. Campos: `name`, `email`, `phone`, `message`, `created_at` |
 
Todos tienen FK a `Client`, pero **ningún manager filtra por tenant automáticamente** — cada vista de `views.py` filtra a mano (`.filter(client=request.client)`). Ver advertencia de `TenantAwareManager` en §2.
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `views.py` | `home` (landing pública), dashboard y CRUD de secciones/servicios/galería, todo detrás de `tenant_member_required` |
| `website_tags.py` | `{% get_section 'hero' %}`, `{% get_services %}`, entre otros tags de contenido |
| `cloudinary_tags.py` | Tags de imagen con transformaciones Cloudinary |
| `forms.py` | `ContactForm`, `SectionForm`, `ServiceForm` |
| `auth_views.py` | `client_login`/`client_logout` — **el login real del dashboard**, montado en `auth/login/` vía `apps/website/auth_urls.py` (ver gotcha más abajo) |
 
**Relación con otros módulos:** Consume `request.client` de `tenants`. Usa `core.template_resolver` para renderizar el tema correcto. Alimenta `marketing` con páginas indexables.
 
---
 
### 4.3 `apps/accounts/` — Usuarios y Autenticación
 
**Propósito:** Gestionar usuarios asociados a tenants, con control de roles y permisos.
 
**Modelos:**
 
| Modelo | Descripción |
|---|---|
| `UserProfile` | Extiende `User` de Django con FK a `Client` (`null=True` solo para superusers). Campos: `role`, `invitation_token`, `invitation_expires_at` |
 
**Roles (`UserProfile.ROLE_CHOICES`):**
 
| Rol | Acceso |
|---|---|
| `owner` | Dueño del tenant, acceso total (`is_owner`) |
| `admin` | Gestiona contenido (`is_admin`, incluye `owner`) |
| `editor` | Solo edita contenido (`can_edit`, incluye `owner`/`admin`) — default del campo |
| `viewer` | Solo lectura |
 
Por fuera de estos 4 roles, un `User.is_superuser` de Django tiene acceso total a todos los tenants (exento de `tenant_member_required` y del check de `client_login`).
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `decorators.py` | `tenant_member_required` — exige `profile.client == request.client` (o superuser) en toda vista de dashboard de `apps/website/views.py`; ver `#AUD-03` |
| `mixins.py` | `TenantAdminMixin`/`TenantAdminReadOnlyMixin` — filtran por tenant en **Django Admin** (`ModelAdmin`), no en vistas de dashboard |
| `views.py` | `set_password_view`, `request_password_reset_view`, `change_password_view` (sí en uso); `login_view`/`logout_view` están registrados en `apps/accounts/urls.py` bajo `auth/`, pero `apps/website/auth_urls.py` monta **el mismo prefijo `auth/`** con sus propios `login/`/`logout/` primero en `config/urls.py` — Django resuelve ahí y esos dos de `accounts` nunca se alcanzan por URL directa (código muerto en la práctica, solo viven por `{% url 'accounts:login' %}` si algo los referencia así). No confundir con el login real (`apps/website/auth_views.py::client_login`). |
 
**Relación con otros módulos:** Depende de `tenants` para asociar usuarios a clientes. `decorators.py` protege las vistas de `website`.
 
---
 
### 4.4 `apps/core/` — Utilidades Compartidas
 
**Propósito:** Proveer clases base y helpers reutilizables en todas las apps. No tiene URLs ni vistas propias.
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `models.py` | `BaseModel` (timestamps, heredado por todos los modelos) y `EmailOutbox` (cola de emails, `#MED-01`) |
| `cloudinary_utils.py` | `upload_to_cloudinary()`, `delete_from_cloudinary()`, `get_cloudinary_url()`, `get_srcset_urls()`, `CLOUDINARY_PRESETS` — toda subida/URL de Cloudinary pasa por acá, no armar rutas a mano |
| `template_resolver.py` | `render_tenant_template()` — ya no arma rutas, delega en el `TenantTemplateLoader` de `apps/tenants/template_loader.py` |
 
> `TenantAwareManager` **no** vive en `apps/core/` — está en `apps/tenants/managers.py` y no filtra por tenant automáticamente (ver §2 y `#MED-02`).
 
**Relación con otros módulos:** Es la base técnica de todo el sistema. Todas las apps dependen de `core`.
 
---
 
### 4.5 `apps/orders/` — Pagos y Onboarding
 
**Propósito:** Gestionar el flujo completo desde el pago hasta el aprovisionamiento del tenant.
 
**Modelos:**
 
| Modelo | Descripción |
|---|---|
| `Plan` | Plan de suscripción: nombre, precio, features |
| `Order` | Orden de pago: plan, monto, estado, tenant asociado |
| `Subscription` | Suscripción activa de un tenant |
 
**Flujo de pago:**
 
```
Usuario → /checkout/ → MercadoPago (preferencia) → Pago externo
→ Webhook /webhook/ → order_processor.py → Provisionar tenant → Email bienvenida
```
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `services/mercadopago_service.py` | Crear preferencia de pago, validar webhook IPN |
| `services/order_processor.py` | Lógica post-pago: crear tenant, enviar emails |
| `services/email_service.py` | Emails de confirmación de pago |
| `views_onboarding.py` | Flujo de configuración inicial post-pago |
| `signals.py` | Dispara provisioning automático tras pago exitoso |
 
> ⚠️ MercadoPago actualmente en **modo test**. Activar producción es bloqueador de ingresos.
 
**Relación con otros módulos:** Depende de `tenants` para crear el Client. Usa `core` para emails. Dispara `provision_tenant` de `tenants`.
 
---
 
### 4.6 `apps/marketing/` — SEO y Visibilidad
 
**Propósito:** Gestionar SEO, indexación y visibilidad de cada tenant de forma independiente.
 
**Modelos:**
 
| Modelo | Descripción |
|---|---|
| `SEOConfig` | Por tenant: título, meta description, Open Graph, Schema.org JSON-LD, verificación Google/Bing |
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `seo_tags.py` | `{% seo_tags "home" %}` — inyecta en `<head>`: title, meta, OG, JSON-LD, canonical |
| `sitemaps.py` | `TenantStaticSitemap`, `TenantSectionsSitemap` — filtrado por tenant |
| `views_robots.py` | `/robots.txt` dinámico por tenant |
| `views_verification.py` | Sirve `/google<code>.html` para verificar Search Console |
| `views_sitemap.py` | Sirve `/sitemap.xml` y `/sitemap-<section>.xml` |
 
**Comandos:**
 
```bash
python manage.py verify_search_console --domain andesscale.com
python manage.py verify_search_console --all
```
 
**Relación con otros módulos:** Consume `request.client` de `tenants`. Indexa contenido de `website`. Usado en todos los `base.html` de temas.
 
---
 
## 5. Funciones y Métodos Clave
 
### `TenantMiddleware.__call__(request)`
 
**Propósito:** Detectar el tenant activo, adjuntarlo a `request.client` y a un thread-local que usa el loader de templates.
 
**Parámetros:** `request` — objeto `HttpRequest` de Django.
 
**Retorna:** la respuesta de la vista (`request.client = client` o `None` si es dominio de sistema), o un `HttpResponse` 404 si el dominio es desconocido.
 
```python
# apps/tenants/middleware.py (simplificado)

class TenantMiddleware(MiddlewareMixin):
    def __call__(self, request):
        clear_current_tenant()
        host = request.get_host().split(':')[0].lower()
        client = self._detect_tenant(request, host)  # ?tenant=slug solo si DEBUG, si no busca Domain

        if client:
            request.client = client
            set_current_tenant(client)  # thread-local, lo usa TenantTemplateLoader
            if client.mode_under_construction and not request.path.startswith(self.CONSTRUCTION_BYPASS_PREFIXES):
                return render(request, 'errors/under_construction.html', {'client': client})
            return self.get_response(request)

        if self._is_system_domain(host):  # localhost, BASE_DOMAIN, *.onrender.com
            request.client = None
            return self.get_response(request)

        return self._handle_no_tenant(request, host)  # 404
```
 
---
 
### `TenantAwareManager` (`apps/tenants/managers.py`)
 
**No filtra por tenant.** Es un `models.Manager` con helpers de conveniencia (`for_client()`, `active()`, `ordered()`) — el auto-filtro basado en un atributo de clase `_current_client` existió antes pero se eliminó en `#MED-02` (2026-08-22) por ser código muerto en producción y un riesgo real (atributo de clase compartido entre requests concurrentes de distintos tenants).
 
**Uso correcto:** filtrar siempre a mano.
 
```python
# apps/tenants/managers.py
 
class TenantAwareManager(models.Manager):
    def for_client(self, client):
        return super().get_queryset().filter(client=client)
    # + active(), ordered(), featured() — helpers, no auto-filtro
 
# Uso en una vista (obligatorio filtrar explícito):
sections = Section.objects.filter(client=request.client)
# o, equivalente:
sections = Section.objects.for_client(request.client)
```
 
---
 
### `render_tenant_template(request, template_path, context)`
 
**Propósito:** Renderizar un template dejando que `TenantTemplateLoader` resuelva la ruta correcta según el tema del tenant — ya no arma rutas a mano.
 
**Parámetros:**
- `request` — `HttpRequest` con `request.client` (usado por el loader vía thread-local)
- `template_path` — ruta relativa genérica (ej. `"landing/home.html"`)
- `context` — diccionario de contexto
**Retorna:** `HttpResponse` con el template renderizado.
 
```python
# apps/core/template_resolver.py

def render_tenant_template(request, template_path, context=None):
    return render(request, template_path, context or {})

# Uso en una vista del dashboard (filtrado explícito, sin auto-filtro de manager):
def dashboard_home(request):
    context = {'sections': Section.objects.filter(client=request.client)}
    return render_tenant_template(request, 'dashboard/index.html', context)
```
 
---
 
### `{% get_section 'hero' %}`
 
**Propósito:** Template tag para obtener una sección del CMS por tipo.
 
**Parámetros:** `section_type` — tipo de sección (`'hero'`, `'about'`, `'gallery'`, etc.)
 
**Retorna:** Objeto `Section` o `None`.
 
```django
{# En un template de tema: #}
{% load website_tags %}
 
{% get_section 'hero' as hero %}
{% if hero %}
  <h1>{{ hero.title }}</h1>
  <p>{{ hero.description }}</p>
{% endif %}
```
 
---
 
### `{% seo_tags page_key %}`
 
**Propósito:** Inyectar todas las etiquetas SEO en el `<head>` del documento.
 
**Parámetros:** `page_key` — identificador de la página (`"home"`, `"servicios"`, etc.)
 
**Genera:** `<title>`, `<meta>`, Open Graph, Schema.org JSON-LD, canonical, verificaciones.
 
```django
{# En base.html de cualquier tema: #}
{% load seo_tags %}
<head>
  {% seo_tags page_key|default:"home" %}
</head>
```
 
---
 
### `upload_image(file, folder, public_id)`
 
**Propósito:** Subir una imagen a Cloudinary en la carpeta correcta del tenant.
 
**Ubicación:** `apps/core/cloudinary_utils.py`
 
**Parámetros:**
- `file` — archivo a subir
- `folder` — carpeta en Cloudinary (ej. `"tenants/servelec/services"`)
- `public_id` — ID público del asset (opcional)
**Retorna:** `dict` con `url`, `public_id`, `secure_url`.
 
```python
from apps.core.cloudinary_utils import upload_image
 
result = upload_image(
    file=request.FILES['image'],
    folder=f"tenants/{request.client.slug}/services"
)
image_url = result['secure_url']
```
 
---
 
## 6. Integraciones Externas
 
### Cloudinary — Media Storage
 
**Rol:** Almacenamiento y transformación de imágenes y videos. Reemplaza el sistema de archivos local en producción.
 
**Configuración:** `config/settings/cloudinary_setting.py`
 
**Estructura de carpetas en Cloudinary:**
 
```
tenants/
  {client_slug}/
    branding/      ← logo, favicon
    services/      ← imágenes de servicios
    sections/      ← imágenes de secciones (hero, galería, etc.)
```
 
**Uso en templates:**
 
```django
{% load cloudinary_tags %}
{% cloudinary_image section.image width=800 height=600 crop="fill" %}
```
 
---
 
### MercadoPago — Pagos
 
**Rol:** Procesamiento de pagos de suscripción para nuevos clientes.
 
**Estado actual:** ⚠️ Modo test. La parte técnica (checkout, firma de webhook, idempotencia, generación de `order_number` sin condición de carrera, E2E automatizado con mocks) ya está cerrada — ver `#AUD-01/02/05/08` y `#PAY-03` en el kanban. Lo que falta es el trámite de facturación (SII) y una pasada manual real contra el sandbox de MP con credenciales de test (`#PAY-01`).
 
**Flujo:** ver §7.4 arriba (checkout → webhook firmado → onboarding provisiona el tenant).
 
**Variables de entorno requeridas:**
 
```env
MP_ACCESS_TOKEN=TEST-xxx      # En test
MP_PUBLIC_KEY=TEST-xxx
MP_WEBHOOK_SECRET=xxx          # Obligatorio fuera de DEBUG — falla cerrado si falta (#AUD-02)
```
 
---
 
### Neon — Base de Datos PostgreSQL
 
**Rol:** Base de datos principal del proyecto (serverless PostgreSQL).
 
**Branches:**
- `main` — producción
- `dev` — desarrollo (mismos datos, rama separada)
**Uso local:** SQLite para desarrollo rápido sin conexión a Neon.
 
**Variables de entorno:**
 
```env
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```
 
---
 
### Render — Hosting y Deploy
 
**Rol:** Plataforma de hosting con auto-deploy desde GitHub.
 
**Archivos de configuración:**
 
```
Procfile        → web: gunicorn config.wsgi
render.yaml     → servicios, variables de entorno, build command
```
 
**Build command:**
 
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```
 
---
 
### Google Search Console
 
**Rol:** Verificación de propiedad y monitoreo de indexación por tenant.
 
**Métodos de verificación implementados:**
1. Meta tag en `<head>` via `{% seo_tags %}`
2. Archivo HTML servido por `views_verification.py`
**Tenants verificados:** `andesscale.com`, `servelec-ingenieria.cl`
 
---
 
## 7. Flujos Principales
 
### 7.1 Autenticación de Cliente
 
```
1. GET /auth/login/ → resuelve a apps/website/auth_views.py::client_login
   (montado por apps/website/auth_urls.py, que Django resuelve ANTES que
   apps/accounts/urls.py — también registrado en 'auth/' pero shadowed;
   ver nota en §4.3)
2. Usuario ingresa credenciales
3. client_login → authenticate(username, password)
4. _user_belongs_to_tenant(): profile.client_id == request.client.id (o superuser/staff) — #AUD-03
5. Login exitoso → redirect a 'home' (rota sesión + token CSRF)
6. Middleware detecta el tenant en cada request posterior; tenant_member_required protege cada vista del dashboard
```
 
**Roles y acceso:**
 
```
superuser (Django) → /superadmin/ + acceso a todos los tenants
owner/admin/editor/viewer (UserProfile.role) → /dashboard/, acotado a profile.client
```
 
---
 
### 7.2 Provisioning de Tenant
 
```
1. python manage.py provision_tenant cliente --industry servicios_profesionales --theme servelec
   ↓
2. Crear Client + Domain en DB
   ↓
3. Signal post_save de Client crea ClientSettings + ClientEmailSettings + FormConfig (get_or_create)
   ↓
4. Aplicar seed data según --industry
   ↓
5. Crear usuario owner (UserProfile.role='owner') ligado al Client
   ↓
6. Enviar email de bienvenida con link de set_password (EmailService.send_welcome)
   ↓
7. python manage.py check_tenant_setup <slug> — gate de QA antes de dar por lista la publicación
   ↓
8. Cliente accede a /dashboard/ y personaliza su sitio
```
 
---
 
### 7.3 Formulario de Contacto
 
```
1. Visitante completa el form en la landing pública (varía por tema — algunos usan
   partials/contact_form.html, otros components/contact_multistep.html)
2. POST → website/views.py::contact_submit (rate limit 3/10min por IP+tenant, honeypot)
3. ContactForm.is_valid()
4. Guardar ContactSubmission (client=request.client explícito)
5. Notificar según ClientEmailSettings.notify_mode ('dashboard' | 'email' | 'both')
6. Responder JSON (fetch) o partial HTMX según el tema — sin página de éxito separada
```
 
---
 
### 7.4 Checkout y Pago (MercadoPago)
 
```
1. Visitante elige plan en /checkout/<plan_slug>/ → checkout_view (apps/orders/views.py)
2. POST /checkout/process/ → process_payment_view → MercadoPagoService crea la preferencia
3. Redirect a Checkout Bricks de MercadoPago (excluido de la CSP, ver kanban #SEC-02)
4. Pago aprobado → MercadoPago POST /webhook/ → mercadopago_webhook_view
5. Validar firma HMAC del webhook (401 si falta/es inválida; #AUD-02) y re-consultar el pago contra la API de MP
6. Order pasa a estado 'paid'; el email con el link de onboarding se encola vía
   transaction.on_commit() (#AUD-06) — nunca dentro de la misma transacción del webhook
7. Cliente completa /onboarding/<token>/ (views_onboarding.py): ahí recién se
   crea Client + Domain + UserProfile(owner) + Section(hero, contact) — el
   tenant NO se provisiona en el webhook, se provisiona en el onboarding
8. Order pasa a 'completed'; redirect a la página de éxito (namespace de urls_onboarding.py: sin 'orders:', ver gotcha en CLAUDE.md)
```
 
---
 
### 7.5 Renderizado de Landing Pública
 
```
1. GET https://servelec-ingenieria.cl/
2. TenantMiddleware → request.client = Client("servelec-ingenieria"), template='servelec'
3. website.views.home → render_tenant_template(request, "landing/home.html")
4. TenantTemplateLoader → templates/servelec/landing/home.html
5. Template carga:
   - {% seo_tags "home" %} → título, meta, OG, JSON-LD
   - Variables CSS de branding embebidas inline en base.html (colores/fuente de ClientSettings)
   - {% get_section 'hero' %} → sección hero del tenant
   - {% get_services %} → servicios del tenant
6. Respuesta HTML con contenido del tenant
```
 
---
 
## 8. Instalación Local
 
### Requisitos previos
 
- Python 3.11+
- Git
- Node.js (para compilar Tailwind CSS)
- PostgreSQL local **o** acceso a Neon (branch dev)
### Paso a paso
 
```bash
# 1. Clonar el repositorio
git clone https://github.com/Kx24/SaasMvp.git
cd SaasMvp
 
# 2. Crear y activar virtualenv
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
 
# 3. Instalar dependencias
pip install -r requirements.txt
 
# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales (ver sección siguiente)
 
# 5. Aplicar migraciones
python manage.py migrate --settings=config.settings.development
 
# 6. Crear tenant de desarrollo local (sin --domain: se accede vía ?tenant=mi-empresa-dev)
python manage.py provision_tenant mi-empresa-dev --industry=servicios_profesionales --settings=config.settings.development
 
# 7. Crear superusuario
python manage.py createsuperuser --settings=config.settings.development
 
# 8. Instalar dependencias de Node y compilar Tailwind CSS (pipeline propio, #AUD-11 — ya no CDN)
npm ci
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch
 
# 9. Iniciar servidor
python manage.py runserver --settings=config.settings.development
```
 
### Variables de entorno requeridas (`.env`)
 
```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
 
# Base de datos (SQLite para dev rápido, o Neon)
DATABASE_URL=sqlite:///db.sqlite3
# DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
 
# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
 
# MercadoPago (modo test)
MP_ACCESS_TOKEN=TEST-xxx
MP_PUBLIC_KEY=TEST-xxx
MP_WEBHOOK_SECRET=xxx
 
# Email (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=AndesScale <your@email.com>
```
 
### Acceder a los tenants en desarrollo
 
```
# Con parámetro ?tenant=slug (sin necesidad de configurar DNS):
http://localhost:8000/?tenant=servelec
http://localhost:8000/?tenant=andesscale
 
# Dashboard del cliente:
http://localhost:8000/dashboard/?tenant=servelec
 
# Superadmin Django:
http://localhost:8000/superadmin/
```
 
---
 
## 9. Despliegue en Producción
 
### Plataforma: Render + Neon
 
**Render** sirve la aplicación Django. **Neon** provee PostgreSQL serverless.
 
### Paso a paso — primera vez
 
```bash
# 1. Push a GitHub (rama main)
git push origin main
 
# 2. En Render:
#    - New Web Service → conectar repo GitHub
#    - Runtime: Python 3.11
#    - Build Command:
pip install -r requirements.txt && python manage.py collectstatic --noinput
 
#    - Start Command (Procfile):
web: gunicorn config.wsgi --log-file -
 
# 3. Agregar variables de entorno en Render:
#    (todas las del .env, con valores de producción)
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
ALLOWED_HOSTS=andesscale.com,servelec-ingenieria.cl,...
 
# 4. Primera migración en producción:
python manage.py migrate --settings=config.settings.production
 
# 5. Configurar planes de suscripción:
python manage.py setup_plans --settings=config.settings.production
```
 
### Agregar un nuevo tenant en producción
 
```bash
# Provisionar tenant completo con seed data:
python manage.py provision_tenant nuevo-cliente \
  --domain nuevocliente.cl \
  --industry servicios_profesionales \
  --theme themes/default \
  --settings=config.settings.production

# Actualizar el dominio principal de un tenant existente:
python manage.py update_domain nuevo-cliente \
  --domain nuevocliente.cl \
  --settings=config.settings.production

# Verificar que el tenant quedó bien provisionado (theme, dominio, email, SEO):
python manage.py check_tenant_setup nuevo-cliente \
  --settings=config.settings.production
```

> Procedimiento completo, incluyendo pasos manuales (email de contacto, SEO): ver `Documentacion/Procedimiento_Nuevo_Tenant.md`.
 
### Configurar dominio personalizado
 
```
1. En Render: Settings → Custom Domains → Add domain
2. En proveedor DNS del cliente:
   CNAME  @  →  your-app.onrender.com
3. Render provisiona SSL automáticamente (Let's Encrypt)
4. Verificar: https://nuevocliente.cl
```
 
### Verificar Google Search Console
 
```bash
python manage.py verify_search_console --domain nuevocliente.cl
```
 
---
 
## 10. Estado del Kanban
 
Esta sección numeraba cards `#1`–`#54` con un esquema que ya no se usa — el kanban vigente vive en **`Documentacion/KANBAN_PROYECTO.md`** y usa IDs por categoría (`#AUD-xx` seguridad/robustez, `#MED-xx` mediano plazo, `#DEUDA-xx` deuda técnica, `#RC-xx` Rancho Cachimba, `#TOOL-xx` herramientas). Mantener un resumen duplicado acá garantiza que se desactualice de nuevo — no se reproduce.
 
**Para saber qué está hecho y qué falta:** abrir `Documentacion/KANBAN_PROYECTO.md`, sección **"🌙 Retomar aquí"** al inicio, que se actualiza en cada sesión con el estado más reciente.
 
**Resumen de alto nivel al 2026-08-22:** el gate de seguridad P0 (checkout, firma de webhook, aislamiento cross-tenant, `render.yaml`) está cerrado, igual que la robustez transaccional (emails fuera de la transacción, `order_number` sin condición de carrera, E2E de pago con mocks) y el aislamiento multi-tenant real (`#MED-02`, suite `apps.tenants.tests_isolation`). El pipeline de Tailwind (`#AUD-11`) y headers de seguridad (`#SEC-02`) también están cerrados. Lo que sigue son cabos sueltos que requieren acción del usuario fuera del repo (SPF/DKIM de Zoho, sandbox real de MercadoPago, dashboard de Render) y el lanzamiento de Rancho Cachimba, en pausa.

 
---
 
## Contribución y Desarrollo
 
### Patrón de trabajo
 
1. Revisar el Kanban antes de empezar
2. Aprobar el plan de la card antes de escribir código
3. Implementar card por card con verificación en cada paso
4. Validar en entorno local antes de push a producción
5. Auto-deploy activado: cada push a `main` despliega en Render
### Convenciones
 
- **Templates:** Nunca usar `render()` en vistas del dashboard; siempre `render_tenant_template()`
- **Queries:** ⚠️ Al revés de lo que decía esta línea antes — `TenantAwareManager` **no** filtra por tenant (`#MED-02`). Siempre `.filter(client=request.client)` explícito, nunca asumir que `Model.objects.all()` ya viene scoped.
- **Autorización:** vistas de dashboard van detrás de `tenant_member_required` (`apps/accounts/decorators.py`), no alcanza con `@login_required` solo (`#AUD-03`).
- **Cloudinary:** Toda subida pasa por `apps/core/cloudinary_utils.py` (`upload_to_cloudinary`, `get_cloudinary_url`, presets en `CLOUDINARY_PRESETS`)
- **Emails:** todo `send_*` disparado dentro de un `transaction.atomic()` va envuelto en `transaction.on_commit(...)` (`#AUD-06`)
- **Migraciones:** Verificar con `python manage.py makemigrations --check --dry-run` antes de cada deploy
- **Arnés de TDD:** toda card de Backend/Database entrega un test que falla sin el cambio — contrato completo en `Documentacion/KANBAN_PROYECTO.md` §2 y en `CLAUDE.md`.
---
 
*Documentación generada para AndesScale — Mayo 2026. Reconciliada con el código real en `#DEUDA-05`, 2026-08-22.*