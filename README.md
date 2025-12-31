# 🚀 SaaS MVP - Multi-Tenant Website Platform

Sistema de gestión de sitios web multi-tenant con Django. Permite crear y gestionar múltiples sitios web de clientes desde una única plataforma, con **templates personalizables por tenant**.

---

## 📊 Estado del Proyecto

**Progreso:** Cards A-C completadas + Cards 1-15 originales

```
✅ Core & Backend          [████████████████] 100%
✅ Frontend & Dashboard    [████████████████] 100%
✅ Gestión Avanzada        [████████████████] 100%
✅ Templates por Tenant    [████████████████] 100%
⏳ Deploy & Production     [████░░░░░░░░░░░░] 25%
```

**Última actualización:** Diciembre 2025

---

## ✅ Funcionalidades Completadas

### 🏗️ Core (Cards #1-6)
- [x] Ambiente de desarrollo configurado
- [x] Estructura modular del proyecto
- [x] Sistema multi-tenant (Client, ClientSettings, Domain)
- [x] TenantMiddleware (detección por dominio, subdomain, ?tenant=)
- [x] Testing de aislamiento de datos
- [x] Modelos CMS (Section, Service, Testimonial, ContactSubmission)

### 🎨 Frontend (Cards #7-10)
- [x] Frontend base con Tailwind CSS + HTMX + Alpine.js
- [x] Sistema de edición inline (modales HTMX)
- [x] Panel de cliente (/dashboard/)
- [x] Formulario de contacto funcional

### 🔧 Gestión Avanzada (Cards #11-15 + #27-28)
- [x] Django Admin personalizado multi-tenant
- [x] Autenticación de clientes (Login/Logout)
- [x] Sistema de permisos (Superuser vs Staff)
- [x] Management Commands
- [x] App Accounts (UserProfile vinculado a tenant)
- [x] Roles y permisos por tenant

### 📄 Templates por Tenant (Cards #A-C) ⭐ NUEVO
- [x] **Card #A:** TenantTemplateLoader dinámico
- [x] **Card #B:** Template `_default` completo y modular
- [x] **Card #C:** Comando `create_tenant` mejorado + estructura media

### ⏳ Pendiente
- [ ] **Card #D:** Preparar Deploy
- [ ] **Card #E:** Deploy a Render
- [ ] **Card #F:** Configurar Dominio Producción

---

## 🏛️ Arquitectura

### Multi-Tenant con Templates Personalizables

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA ACTUAL                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   TEMPLATES (Diseño/HTML)          DATOS (Contenido)           │
│   ─────────────────────            ──────────────────           │
│   templates/tenants/               Base de Datos                │
│   ├── _default/  ←──────────┐      └── PostgreSQL               │
│   │   └── landing/          │          ├── Client: Servelec     │
│   │       └── home.html     │          │   ├── Sections         │
│   │                         │          │   ├── Services         │
│   ├── servelec/ (opcional)  │          │   └── Settings         │
│   │   └── landing/          │          │                        │
│   │       └── home.html     │          └── Client: Neblita      │
│   │                         │              ├── Sections         │
│   └── neblita/ (opcional)   │              ├── Services         │
│       └── ...               │              └── Settings         │
│                             │                                   │
│   TenantTemplateLoader:     │                                   │
│   1. Busca en tenants/{slug}/                                  │
│   2. Fallback a tenants/_default/                              │
│   3. Fallback a templates/                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Sistema de Dominios

```
┌─────────────────────────────────────────────────────────────────┐
│                    DETECCIÓN DE TENANT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Parámetro ?tenant=slug    (desarrollo)                     │
│  2. Dominio exacto            servelec.cl → Client Servelec    │
│  3. Wildcard subdomain        servelec.tuapp.cl → Servelec     │
│  4. Localhost                 → DEFAULT_TENANT_SLUG            │
│                                                                 │
│  Tabla Domain:                                                  │
│  ├── servelec.cl (primary)                                     │
│  ├── www.servelec.cl (alias)                                   │
│  └── servelec.tuapp.cl (subdomain auto)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Tres Interfaces

```
┌─────────────────────────────────────────────────────────────────┐
│  SUPERADMIN → /superadmin/                                      │
│  - Crear/gestionar tenants (CRUD completo)                     │
│  - Ver TODOS los datos                                         │
│  - Gestión de dominios                                         │
│  - Puede acceder a cualquier tenant                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  CLIENTE STAFF → /superadmin/ (filtrado)                       │
│  - Solo ve SU tenant                                           │
│  - NO ve módulo "Tenants"                                      │
│  - CRUD de su contenido                                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PÚBLICO → /                                                    │
│  - Sitio web del cliente                                       │
│  - Template según tenant (o _default)                          │
│  - Datos desde DB filtrados por tenant                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

### Backend
- **Django 5.2+** - Framework web
- **PostgreSQL / SQLite** - Base de datos
- **Python 3.11+** - Lenguaje

### Frontend
- **Tailwind CSS 3.x** - Framework CSS (CDN)
- **HTMX 1.9+** - Interactividad sin JS complejo
- **Alpine.js 3.x** - Estado reactivo ligero

### Características
- ✅ Templates personalizables por tenant
- ✅ Multi-dominio por tenant
- ✅ Sistema de permisos (Superuser vs Staff)
- ✅ WhiteNoise para archivos estáticos/media
- ✅ Preparado para Cloudinary (campos en ClientSettings)
- ✅ Sin npm/webpack (CDN directo)

---

## 📁 Estructura del Proyecto

```
SaaSMVP/
├── config/
│   ├── settings/
│   │   ├── base.py              # TenantTemplateLoader configurado
│   │   ├── development.py
│   │   └── production.py
│   └── urls.py
│
├── apps/
│   ├── tenants/
│   │   ├── models.py            # Client, ClientSettings, Domain
│   │   ├── middleware.py        # TenantMiddleware + thread-local
│   │   ├── template_loader.py   # TenantTemplateLoader ⭐
│   │   ├── context_processors.py
│   │   ├── admin.py
│   │   ├── templatetags/
│   │   │   └── tenant_tags.py   # {% tenant_static %}, {% tenant_media %}
│   │   └── management/commands/
│   │       └── create_tenant.py # Comando mejorado ⭐
│   │
│   ├── website/
│   │   ├── models.py            # Section, Service, Testimonial, Contact
│   │   ├── views.py
│   │   └── templatetags/
│   │       └── website_tags.py  # {% get_section %}, {% get_services %}
│   │
│   └── accounts/
│       ├── models.py            # UserProfile (vincula user ↔ tenant)
│       ├── admin.py             # CustomUserAdmin
│       └── mixins.py            # TenantAdminMixin
│
├── templates/
│   ├── base.html                # Base global
│   ├── tenants/                 # ⭐ NUEVO: Templates por tenant
│   │   ├── _default/            # Template base para todos
│   │   │   └── landing/
│   │   │       └── home.html    # Hero, About, Services, Contact
│   │   ├── servelec/            # (opcional) Personalizado
│   │   └── neblita/             # (opcional) Personalizado
│   │
│   ├── components/
│   ├── dashboard/
│   ├── auth/
│   ├── partials/
│   └── errors/
│
├── media/
│   └── tenants/                 # ⭐ NUEVO: Media por tenant
│       ├── servelec/
│       │   ├── images/
│       │   └── documents/
│       └── neblita/
│
└── static/
```

---

## 🚀 Instalación y Setup

### Requisitos
- Python 3.11+
- PostgreSQL (opcional, usa SQLite en dev)

### Instalación

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd SaaSMVP

# 2. Crear virtualenv
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 5. Migraciones
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Crear carpetas necesarias
mkdir -p templates/tenants/_default/landing
mkdir -p media/tenants

# 8. Iniciar servidor
python manage.py runserver
```

---

## 📖 Uso

### Crear Tenant Completo (Nuevo Comando)

```bash
# Básico
python manage.py create_tenant "Mi Empresa" miempresa.cl

# Con opciones
python manage.py create_tenant "Mi Empresa" miempresa.cl \
    --email=admin@miempresa.cl \
    --password=secreto123 \
    --phone="+56912345678" \
    --color=#ff6600 \
    --extra-domain=www.miempresa.cl \
    --copy-templates
```

**Opciones disponibles:**

| Opción | Descripción | Default |
|--------|-------------|---------|
| `--email` | Email del admin | admin@example.com |
| `--password` | Contraseña | changeme123 |
| `--username` | Username | admin_{slug} |
| `--color` | Color primario (hex) | #2563eb |
| `--phone` | Teléfono contacto | (vacío) |
| `--extra-domain` | Dominios adicionales | (ninguno) |
| `--copy-templates` | Copiar _default a tenant | False |
| `--no-content` | No crear contenido inicial | False |

**Crea automáticamente:**
- ✅ Client + ClientSettings
- ✅ Dominios (principal + extras + subdominio)
- ✅ Usuario admin vinculado al tenant
- ✅ Carpeta media/tenants/{slug}/
- ✅ 3 secciones (hero, about, contact)
- ✅ 3 servicios de ejemplo

### Probar en Desarrollo

```bash
# Visitar con parámetro tenant
http://127.0.0.1:8000/?tenant=mi-empresa

# O configurar DEFAULT_TENANT_SLUG en settings
http://127.0.0.1:8000/
```

### Personalizar Templates

```bash
# 1. Copiar _default a tu tenant
xcopy /E /I templates\tenants\_default templates\tenants\mi-empresa

# 2. Editar templates en templates/tenants/mi-empresa/
# 3. El TenantTemplateLoader usará automáticamente los personalizados
```

---

## 🔐 Sistema de Permisos

```
┌─────────────────────────────────────────────────────────────────┐
│                    MATRIZ DE PERMISOS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SUPERUSER (is_superuser=True)                                 │
│  ├── Ve módulo "Tenants" ✅                                    │
│  ├── Ve TODOS los usuarios ✅                                  │
│  ├── Ve TODO el contenido ✅                                   │
│  ├── Puede acceder a cualquier ?tenant= ✅                     │
│  └── CRUD completo en todo ✅                                  │
│                                                                 │
│  STAFF DE TENANT (is_staff=True + profile.client)              │
│  ├── NO ve módulo "Tenants" ❌                                 │
│  ├── Solo ve usuarios de SU tenant ✅                          │
│  ├── Solo ve contenido de SU tenant ✅                         │
│  ├── NO puede acceder a otros tenants ❌                       │
│  └── CRUD solo de su contenido ✅                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗺️ Roadmap

### ✅ Fase 1: MVP Core (Completado)
- Multi-tenancy funcional
- Frontend moderno y responsive
- Dashboard cliente completo
- Management commands
- Autenticación y permisos

### ✅ Fase 2: Templates por Tenant (Completado)
- TenantTemplateLoader
- Template _default modular
- Estructura media por tenant
- Comando create_tenant mejorado

### ⏳ Fase 3: Deploy (En progreso)
- [ ] **Card #D:** Preparar Deploy
- [ ] **Card #E:** Deploy a Render
- [ ] **Card #F:** Configurar Dominio

### 🔮 Fase 4: Futuras Mejoras
- [ ] Cloudinary para imágenes
- [ ] Email notifications (SMTP por tenant)
- [ ] Panel de personalización visual
- [ ] Sistema de plantillas predefinidas
- [ ] Blog system
- [ ] Multi-idioma
- [ ] API REST

---

## 📞 Contacto

**Desarrollador:** Sánchez  
**Proyecto:** SaaS MVP Multi-Tenant  
**Stack:** Django 5.2 + Tailwind CSS + HTMX + Alpine.js

---

**🚀 Templates por Tenant completados - Siguiente: Deploy a Producción**
