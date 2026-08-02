# AndesScale — Documentación Técnica
 
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
 
| Dominio | Descripción | Tema |
|---|---|---|
| `andesscale.com` | Landing page del SaaS (el producto mismo) | `marketing/` |
| `servelec-ingenieria.cl` | Cliente 1 — empresa de ingeniería eléctrica | `electricidad/` |
 
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
 
Cada request pasa por `TenantMiddleware`, que detecta el tenant activo según el dominio HTTP (o el parámetro `?tenant=slug` en desarrollo). El objeto `Client` queda disponible como `request.client` en todas las vistas y templates. Todos los modelos de negocio heredan de `TenantAwareManager`, que filtra automáticamente las queries por tenant.
 
```
petición → TenantMiddleware → request.client → View → TenantAwareManager → DB (filtrado)
```
 
### Sistema de temas (templates)
 
Cada tenant tiene asignado un `template` (campo en `ClientSettings`). El `TenantTemplateLoader` resuelve rutas bajo `templates/themes/{template}/`. Si no existe plantilla específica, cae al tema `default/`.
 
```
request.client.settings.template → "electricidad"
TenantTemplateLoader → templates/themes/electricidad/landing/home.html
```
 
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
├── templates/                  # Templates globales del proyecto
│   ├── themes/                 # Temas visuales por rubro
│   │   ├── default/            # Tema genérico
│   │   └── electricidad/       # Tema Servelec
│   ├── dashboard/              # Panel CMS del cliente
│   ├── marketing/              # Landing del SaaS
│   ├── emails/                 # Templates de email transaccional
│   ├── errors/                 # Páginas de error
│   └── partials/               # Fragmentos HTMX
│
├── static/                     # Assets compilados (CSS, JS, img)
├── media/                      # Uploads locales (solo dev)
├── templates_library/          # Seed data por rubro de cliente
│   ├── electricidad/
│   ├── construccion/
│   └── servicios_profesionales/
├── scripts/                    # Scripts de utilidad y mantenimiento
└── docs/                       # Documentación adicional
```
 
### Detalle de carpetas clave
 
| Carpeta | Rol | Tipo |
|---|---|---|
| `config/` | Configuración Django, settings, URLs raíz | Core |
| `apps/tenants/` | Modelo Client, middleware, provisioning | Core |
| `apps/website/` | CMS: Section, Service, ContactSubmission | Core |
| `apps/accounts/` | UserProfile, autenticación, roles | Core |
| `apps/core/` | BaseModel, TenantAwareManager, Cloudinary helpers | Auxiliar |
| `apps/orders/` | Checkout MercadoPago, onboarding post-pago | Auxiliar |
| `apps/marketing/` | SEO, sitemap, robots.txt, Search Console | Auxiliar |
| `templates/themes/` | Temas visuales por rubro | Presentación |
| `templates/dashboard/` | Panel de administración del cliente | Presentación |
| `templates_library/` | Contenido inicial (seed data) por industria | Datos |
| `scripts/` | Automatización, migración, tests manuales | DevOps |
 
---
 
## 4. Módulos del Sistema
 
### 4.1 `apps/tenants/` — Core Multi-Tenancy
 
**Propósito:** Gestionar el ciclo de vida completo de un tenant: creación, detección por dominio, configuración de branding, y aislamiento de datos.
 
**Es el módulo núcleo del sistema.** Todos los demás módulos dependen de él.
 
**Modelos principales:**
 
| Modelo | Descripción |
|---|---|
| `Client` | Representa un tenant. Campos: `name`, `slug`, `plan`, `is_active`, `contact_email` |
| `Domain` | Dominios asociados a un Client (uno-a-muchos) |
| `ClientSettings` | Branding: colores, logo, favicon, fuentes, tagline, descripción, template visual |
| `ClientMailSettings` | Configuración SMTP del tenant |
| `FormConfig` | Configuración del formulario de contacto |
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `middleware.py` | `TenantMiddleware`: detecta tenant por dominio, inyecta `request.client` |
| `template_loader.py` | `TenantTemplateLoader`: resuelve rutas de templates por tema del tenant |
| `context_processors.py` | Inyecta `client` y `settings` en contexto de cada template |
| `signals.py` | Auto-crea `ClientSettings` al crear un `Client` |
| `tenant_tags.py` | Tags `{% tenant_css %}`, `{% client_settings %}` |
 
**Comandos de management:**
 
```bash
python manage.py create_tenant          # Crea tenant interactivo
python manage.py provision_tenant       # Provisionamiento completo con seed data
python manage.py list_tenants           # Lista todos los tenants activos
python manage.py create_localhost_client # Crea tenant para dev local
python manage.py update_domain          # Actualiza dominio de un tenant
python manage.py check_cloudinary       # Verifica configuración Cloudinary
python manage.py cloudinary_usage       # Reporte de uso de Cloudinary
python manage.py test_isolation         # Tests de aislamiento entre tenants
```
 
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
 
Todos usan `TenantAwareManager` para filtrar por tenant automáticamente.
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `views.py` | `HomeView` (landing pública), CRUD de secciones y servicios en dashboard |
| `website_tags.py` | `{% get_section 'hero' %}`, `{% get_services %}` |
| `cloudinary_tags.py` | `{% cloudinary_image %}` con transformaciones |
| `forms.py` | `ContactForm`, `SectionForm`, `ServiceForm` |
| `auth_views.py` | Login/logout del cliente |
 
**Relación con otros módulos:** Consume `request.client` de `tenants`. Usa `core.template_resolver` para renderizar el tema correcto. Alimenta `marketing` con páginas indexables.
 
---
 
### 4.3 `apps/accounts/` — Usuarios y Autenticación
 
**Propósito:** Gestionar usuarios asociados a tenants, con control de roles y permisos.
 
**Modelos:**
 
| Modelo | Descripción |
|---|---|
| `UserProfile` | Extiende `User` de Django con FK a `Client`. Campos: `role`, `invitation_token`, `invitation_expires_at` |
 
**Roles:**
 
| Rol | Acceso |
|---|---|
| `SuperAdmin` | Acceso total a todos los tenants |
| `ClientAdmin` | Acceso solo a su propio tenant |
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `mixins.py` | `TenantRequiredMixin`, `RoleRequiredMixin` para proteger vistas |
| `views.py` | Login, logout, reset de contraseña, invitaciones |
 
**Relación con otros módulos:** Depende de `tenants` para asociar usuarios a clientes. Sus mixins son usados por `website` y `orders`.
 
---
 
### 4.4 `apps/core/` — Utilidades Compartidas
 
**Propósito:** Proveer clases base, managers y helpers reutilizables en todas las apps. No tiene URLs ni vistas propias.
 
**Archivos clave:**
 
| Archivo | Función |
|---|---|
| `models.py` | `BaseModel`: timestamps `created_at`, `updated_at` — heredado por todos los modelos |
| `managers.py` | `TenantAwareManager`: filtra queries por `request.client` automáticamente |
| `cloudinary_utils.py` | `upload_image()`, `delete_asset()`, helpers de transformación |
| `template_resolver.py` | `get_tenant_template()`, `render_tenant_template()` |
 
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
 
### `TenantMiddleware.process_request(request)`
 
**Propósito:** Detectar el tenant activo y adjuntarlo a cada request.
 
**Parámetros:** `request` — objeto `HttpRequest` de Django.
 
**Retorna:** `None` (modifica `request` en lugar) o `HttpResponse` 404 si el dominio no existe.
 
```python
# apps/tenants/middleware.py
 
class TenantMiddleware:
    def __call__(self, request):
        host = request.get_host().split(':')[0]
        slug = request.GET.get('tenant')  # shortcut en desarrollo
 
        try:
            if slug:
                client = Client.objects.get(slug=slug, is_active=True)
            else:
                domain = Domain.objects.select_related('client').get(domain=host)
                client = domain.client
        except (Client.DoesNotExist, Domain.DoesNotExist):
            return render(request, 'errors/tenant_not_found.html', status=404)
 
        request.client = client
        return self.get_response(request)
```
 
---
 
### `TenantAwareManager.get_queryset()`
 
**Propósito:** Filtrar automáticamente todos los querysets por el tenant activo en el request.
 
**Uso:** Heredado por todos los modelos del sistema.
 
```python
# apps/core/managers.py
 
class TenantAwareManager(models.Manager):
    def get_queryset(self):
        from django.db import connection
        # El tenant se almacena en el thread local durante el request
        return super().get_queryset().filter(client=get_current_client())
 
# Uso en un modelo:
class Section(BaseModel):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    objects = TenantAwareManager()
 
# Uso en una vista:
sections = Section.objects.all()  # Ya filtrado por tenant actual
```
 
---
 
### `render_tenant_template(request, template_name, context)`
 
**Propósito:** Renderizar un template resolviendo la ruta correcta según el tema del tenant.
 
**Parámetros:**
- `request` — `HttpRequest` con `request.client`
- `template_name` — nombre relativo del template (ej. `"landing/home.html"`)
- `context` — diccionario de contexto
**Retorna:** `HttpResponse` con el template renderizado.
 
```python
# apps/core/template_resolver.py
 
def render_tenant_template(request, template_name, context=None):
    theme = request.client.settings.template  # ej. "electricidad"
    full_path = f"themes/{theme}/{template_name}"
    return render(request, full_path, context or {})
 
# Uso en una vista del dashboard:
def dashboard_home(request):
    context = {'sections': Section.objects.all()}
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
 
**Estado actual:** ⚠️ Modo test — activar producción es el principal bloqueador de ingresos.
 
**Flujo:**
 
```
1. CheckoutView → mercadopago_service.crear_preferencia(plan, cliente)
2. Redirigir a URL de MercadoPago
3. Pago completado → webhook POST a /webhook/
4. Validar IPN → order_processor.procesar_pago()
5. Crear Client + enviar email de bienvenida
```
 
**Variables de entorno requeridas:**
 
```env
MERCADOPAGO_ACCESS_TOKEN=TEST-xxx   # En test
MERCADOPAGO_PUBLIC_KEY=TEST-xxx
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
1. GET /auth/login/
2. Usuario ingresa credenciales
3. auth_views.login_view → authenticate(username, password)
4. Verificar UserProfile.client == request.client (aislamiento)
5. Login exitoso → redirect /dashboard/
6. Middleware verifica sesión en cada request posterior
```
 
**Roles y acceso:**
 
```
SuperAdmin → /superadmin/ (Django Admin nativo)
ClientAdmin → /dashboard/ (CMS custom)
```
 
---
 
### 7.2 Provisioning de Tenant
 
```
1. python manage.py provision_tenant --slug cliente --template electricidad
   ↓
2. Crear Client + Domain en DB
   ↓
3. Crear ClientSettings (colores, logo placeholder, tema)
   ↓
4. Aplicar seed_data.json de templates_library/{template}/
   ↓
5. Crear usuario ClientAdmin
   ↓
6. Enviar email de bienvenida con link de set_password
   ↓
7. Cliente accede a /dashboard/ y personaliza su sitio
```
 
---
 
### 7.3 Formulario de Contacto
 
```
1. Visitante completa form en landing pública
2. POST → ContactView (HTMX para respuesta parcial)
3. ContactForm.is_valid()
4. Guardar ContactSubmission (filtrada por tenant)
5. Enviar email de notificación al cliente (ClientMailSettings)
6. Enviar email de confirmación al visitante
7. Renderizar partials/contact_success.html
```
 
---
 
### 7.4 Checkout y Pago (MercadoPago)
 
```
1. Visitante elige plan en /checkout/
2. CheckoutView → mercadopago_service.crear_preferencia()
3. Redirect a URL de MercadoPago
4. Pago aprobado → MercadoPago POST /webhook/
5. Validar IPN y firma del webhook
6. order_processor.procesar_pago():
   - Crear Order con estado "pagado"
   - Disparar signal post_save
   - Provisionar tenant automáticamente
   - Enviar email de bienvenida + link de onboarding
7. Cliente completa onboarding en /onboarding/{token}/
```
 
---
 
### 7.5 Renderizado de Landing Pública
 
```
1. GET https://servelec-ingenieria.cl/
2. TenantMiddleware → request.client = Client("servelec")
3. HomeView → render_tenant_template(request, "landing/home.html")
4. TenantTemplateLoader → templates/themes/electricidad/landing/home.html
5. Template carga:
   - {% seo_tags "home" %} → título, meta, OG, JSON-LD
   - {% tenant_css %} → variables CSS del branding
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
 
# 6. Crear tenant de desarrollo local
python manage.py create_localhost_client --settings=config.settings.development
 
# 7. Crear superusuario
python manage.py createsuperuser --settings=config.settings.development
 
# 8. Compilar Tailwind CSS
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
MERCADOPAGO_ACCESS_TOKEN=TEST-xxx
MERCADOPAGO_PUBLIC_KEY=TEST-xxx
 
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
python manage.py provision_tenant \
  --slug nuevo-cliente \
  --domain nuevocliente.cl \
  --template servicios_profesionales \
  --settings=config.settings.production
 
# Actualizar dominio si cambia:
python manage.py update_domain \
  --slug nuevo-cliente \
  --domain nuevocliente.cl \
  --settings=config.settings.production
```
 
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
 
### ✅ Completado (Cards #1 – #46b)
 
| Rango | Módulo |
|---|---|
| #1–#6 | Ambiente, estructura, modelos tenant, middleware, testing, CMS |
| #7–#12 | Admin, Cloudinary, template tags, templates, views, contacto |
| #13–#16 | Migración contenido, testing aislamiento, commands, docs |
| #17–#22 | Deploy Render, dominio, testing producción, backup |
| #23–#26 | Template library, provisioning, templates por rubro |
| #27–#30 | Accounts, roles, login/logout |
| #31–#33 | Panel personalización, CSS dinámico, tutorial onboarding |
| #34–#37 | Landing SaaS, case study, email templates, prospectos |
| #38–#42 | Polish, pricing, campaña cold email, demos, onboarding clientes |
| #43–#46b | SEO, sitemap, robots.txt, Google Search Console |
 
### ⏳ Próximos (Cards #47+)
 
| Card | Descripción |
|---|---|
| #47 | Rol MarketingManager |
| #48 | Admin filtrado por rol |
| #49 | CampaignTracker model (Google Ads) |
| #50 | Google Ads API básica |
| #51 | UTM Builder |
| #52 | Google Analytics / GA4 integration |
| #53 | Dashboard de marketing |
| #54 | Exportar reportes PDF/CSV |
 
### 🔴 Bloqueadores activos
 
| Bloqueador | Impacto | Acción requerida |
|---|---|---|
| MercadoPago en modo test | No se pueden cobrar suscripciones reales | Activar cuenta de producción MP |  
 
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
- **Queries:** Siempre usar el manager del modelo (`Section.objects.all()`), nunca filtrar `client` manualmente
- **Cloudinary:** Toda subida pasa por `apps/core/cloudinary_utils.py`
- **Migraciones:** Verificar con `python manage.py showmigrations` antes de cada deploy
---
 
*Documentación generada para AndesScale — Mayo 2026*