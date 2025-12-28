# 🚀 SaaS MVP - Multi-Tenant Website Platform

Sistema de gestión de sitios web multi-tenant con Django. Permite crear y gestionar múltiples sitios web de clientes desde una única plataforma.

---

## 📊 Estado del Proyecto

**Progreso:** 15/16 cards completadas (93.75%)

```
✅ Core & Backend          [████████████████] 100%
✅ Frontend & Dashboard    [████████████████] 100%
✅ Gestión Avanzada        [████████████████] 100%
✅ Deploy & Production     [████████████████] 100%
⏳ MultiDomnio             [                ] 000%
```

**Última actualización:** Diciembre 2025

---

## ✅ Funcionalidades Completadas

### 🏗️ Core (Cards #1-6)
- [x] **Card #1:** Ambiente de desarrollo configurado
- [x] **Card #2:** Estructura modular del proyecto
- [x] **Card #3:** Sistema multi-tenant (Client, ClientSettings)
- [x] **Card #4:** TenantMiddleware (detección automática por dominio)
- [x] **Card #5:** Testing de aislamiento de datos
- [x] **Card #6:** Modelos CMS (Section, ContactSubmission)

### 🎨 Frontend (Cards #7-10)
- [x] **Card #7:** Frontend base con Tailwind CSS + HTMX + Alpine.js
- [x] **Card #8:** Sistema de edición inline (modales HTMX, sin reloads)
- [x] **Card #9:** Panel de cliente (/dashboard/)
  - Estadísticas en tiempo real
  - Gestión de secciones y servicios
  - Administración de contactos
- [x] **Card #10:** Formulario de contacto funcional
  - Validación frontend y backend
  - Guardado en BD con IP tracking
  - Notificaciones toast

### 🔧 Gestión Avanzada (Cards #11-15)
- [x] **Card #11:** Django Admin personalizado
  - Admin multi-tenant optimizado
  - Solo lectura para contenido de clientes
  - Gestión centralizada de tenants
- [x] **Card #12:** Autenticación de clientes
  - Login/Logout para clientes
  - Dashboard protegido
  - Roles y permisos
- [x] **Card #13:** Sistema de permisos avanzado
  - Superadmin vs Cliente
  - Acceso diferenciado a funciones
- [x] **Card #14:** Management Commands
  - `create_tenant` - Crear tenant completo en 1 comando
  - `list_tenants` - Listar todos los tenants con estadísticas
- [x] **Card #15:** Dashboard Funcional Completo ⭐ **RECIÉN COMPLETADO**
  - CRUD completo de servicios
  - Edición de secciones (Hero, About, Contact)
  - Formulario de contacto público funcional
  - UI profesional y responsive
  - Gestión unificada de contenido
  - Sidebar sin submenús
  - Servicios como Section tipo 'service'

### ⏳ Pendiente
- [ ] **Card #16:** Deploy a Producción
  - Configuración para Render.com
  - PostgreSQL en producción
  - Variables de entorno
  - ALLOWED_HOSTS dinámico
  - Dominio personalizado
  - HTTPS y SSL

---

## 🏛️ Arquitectura

### Multi-Tenant con Shared Database
```
┌─────────────────────────────────────────┐
│           Base de Datos Única           │
├─────────────────────────────────────────┤
│  Client 1 → Sections (hero, about,      │
│             service×N, contact)          │
│  Client 2 → Sections (hero, about,      │
│             service×N, contact)          │
│  Client 3 → Sections (hero, about,      │
│             service×N, contact)          │
└─────────────────────────────────────────┘
         ↑
         │ TenantMiddleware (detecta por dominio)
         │
┌─────────────────────────────────────────┐
│  cliente1.com → Client 1 data           │
│  cliente2.com → Client 2 data           │
│  127.0.0.1    → Default Client          │
└─────────────────────────────────────────┘
```

### Modelo de Contenido Unificado
```
Section (modelo único)
├── hero          (1 por cliente)
├── about         (1 por cliente)
├── service       (N por cliente) ← Servicios
└── contact       (1 por cliente)

Cada Section tiene:
- title       (se muestra)
- subtitle    (se muestra)
- description (se muestra)
- icon        (solo servicios)
- price_text  (solo servicios)
- image       (opcional)
```

### Tres Interfaces
```
┌─────────────────────────────────────────┐
│  SUPERADMIN → /superadmin/ (Django)     │
│  - Crear/gestionar tenants              │
│  - Ver todos los datos (solo lectura)  │
│  - Configuración global                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  CLIENTE → /dashboard/                  │
│  - Dashboard con estadísticas           │
│  - Secciones (Hero, About, Contact)     │
│  - Servicios (CRUD completo)            │
│  - Contactos recibidos                  │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  PÚBLICO → /                            │
│  - Sitio web del cliente                │
│  - Hero, About, Servicios, Contacto     │
│  - Formulario de contacto funcional     │
└─────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

### Backend
- **Django 5.0+** - Framework web
- **PostgreSQL / SQLite** - Base de datos
- **Python 3.11+** - Lenguaje

### Frontend
- **Tailwind CSS 3.x** - Framework CSS (CDN)
- **HTMX 1.9+** - Interactividad sin JS complejo
- **Alpine.js 3.x** - Estado reactivo ligero

### Características
- ✅ ImageField local (preparado para Cloudinary)
- ✅ Sin npm/webpack (CDN directo)
- ✅ Arquitectura limpia y escalable
- ✅ Management commands para automatización
- ✅ Multi-tenant completo

---

## 📁 Estructura del Proyecto

```
SaaSMVP/
├── config/                      # Configuración Django
│   ├── settings/
│   │   ├── base.py             # Settings compartidos + MEDIA config
│   │   ├── development.py      # Local
│   │   └── production.py       # Producción (Render)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                        # Apps por dominio
│   ├── tenants/                # Multi-tenancy
│   │   ├── models.py           # Client, ClientSettings
│   │   ├── middleware.py       # TenantMiddleware
│   │   ├── admin.py            # Admin con inline, resumen
│   │   ├── managers.py         # TenantAwareManager
│   │   └── management/
│   │       └── commands/
│   │           ├── create_tenant.py
│   │           └── list_tenants.py
│   │
│   ├── website/                # Sitios públicos
│   │   ├── models.py           # Section, ContactSubmission
│   │   ├── views.py            # Home, Dashboard, CRUD
│   │   ├── forms.py            # SectionForm, ContactForm
│   │   ├── admin.py            # Admin solo lectura
│   │   ├── auth_urls.py        # Login/Logout
│   │   ├── auth_views.py       # Autenticación clientes
│   │   ├── urls.py
│   │   └── templatetags/
│   │       └── website_tags.py # get_section, get_services
│   │
│   └── core/                   # Utilidades compartidas
│       ├── models.py           # BaseModel
│       └── utils.py
│
├── templates/
│   ├── base.html               # Template base público
│   ├── components/
│   │   ├── navbar.html         # Con About Us, cierre auto
│   │   └── footer.html
│   ├── landing/
│   │   └── home.html           # Hero, About, Servicios, Contacto
│   ├── dashboard/              # Panel cliente
│   │   ├── base.html           # Sidebar sin submenús
│   │   ├── index.html          # Estadísticas + Acciones rápidas
│   │   ├── sections.html       # Lista TODO (hero, about, servicios)
│   │   ├── service_form.html   # Crear/Editar servicio
│   │   ├── service_confirm_delete.html
│   │   ├── edit_section.html   # Editar sección individual
│   │   └── contacts.html
│   ├── auth/
│   │   └── login.html          # Login clientes
│   └── partials/
│       └── contact_form.html   # Formulario público
│
├── static/
│   ├── css/
│   ├── js/
│   └── img/
│
├── media/                      # Uploads (ImageField)
│   └── sections/               # Imágenes de secciones
│
├── db.sqlite3                  # Base de datos local
├── manage.py
└── requirements.txt
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

# 7. Crear cliente con comando
python manage.py create_tenant "Mi Empresa" "127.0.0.1" --email admin@miempresa.com

# Resultado:
# ✅ TENANT CREADO EXITOSAMENTE
# 🌐 Dominio:   127.0.0.1
# 👤 Usuario:   admin_mi-empresa
# 🔑 Password:  changeme123
# 📊 Contenido: 4 secciones, 3 servicios

# 8. Iniciar servidor
python manage.py runserver
```

### Acceso

- **Sitio público:** http://127.0.0.1:8000/
- **Login cliente:** http://127.0.0.1:8000/auth/login/
- **Dashboard:** http://127.0.0.1:8000/dashboard/
- **Superadmin:** http://127.0.0.1:8000/superadmin/

---

## 📖 Uso

### Management Commands

#### Crear Tenant Completo
```bash
python manage.py create_tenant "Nombre Empresa" "dominio.com" --email admin@empresa.com

# Opciones:
# --username      Usuario admin (default: admin_slug)
# --password      Contraseña (default: changeme123)
# --color         Color primario hex (default: #2563eb)
```

**Crea automáticamente:**
- ✅ Cliente y ClientSettings
- ✅ Usuario admin para el cliente
- ✅ 4 secciones (hero, about, services, contact)
- ✅ 3 servicios de ejemplo

#### Listar Tenants
```bash
python manage.py list_tenants

# Opciones:
# --active-only   Solo tenants activos
```

**Muestra:**
- Nombre, dominio, estado
- Colores configurados
- Número de secciones, servicios, contactos
- Features habilitadas

---

### Para Superadmin

1. **Gestionar tenants:**
   - Ir a `/superadmin/tenants/client/`
   - Ver lista con resumen de contenido
   - Editar inline ClientSettings
   - Ver estadísticas por tenant

2. **Monitorear contenido:**
   - Ver secciones/servicios (solo lectura)
   - Ver contactos recibidos
   - No puede crear/eliminar contenido (clientes lo hacen)

---

### Para Cliente

1. **Login:**
   - Ir a `/auth/login/`
   - Usuario/contraseña proporcionados
   - Redirige a Dashboard

2. **Dashboard:**
   - **Home:** Estadísticas + Acciones rápidas
   - **Secciones:** Ver/editar TODO (hero, about, servicios, contact)
   - **Contactos:** Ver mensajes recibidos

3. **Gestionar Contenido:**
   
   **Secciones (Hero, About, Contact):**
   - Clic en "Editar"
   - Modificar: título, subtítulo, descripción, imagen
   - Toggle activo/inactivo
   
   **Servicios:**
   - Botón "Nuevo Servicio"
   - Campos: título, subtítulo, descripción, ícono, precio, imagen
   - Editar existentes
   - Eliminar (con confirmación)

4. **Sitio Público:**
   - **Hero:** Título + Subtítulo + Descripción
   - **About:** Título + Subtítulo + Descripción
   - **Servicios:** Cards con todo visible
   - **Contacto:** Formulario funcional

---

## 🧪 Testing

### Verificar Creación de Tenant
```bash
python manage.py create_tenant "Test" "test.local" --email test@test.com
python manage.py list_tenants
```

### Verificar Aislamiento
```bash
# Crear 2 tenants
# Login como cliente1
# Verificar que solo ve SU contenido
```

---

## 🗺️ Roadmap

### ✅ Fase 1: MVP Core (Completado - 15/16 cards)
- Multi-tenancy funcional
- Frontend moderno y responsive
- Dashboard cliente completo
- CRUD de servicios
- Formulario de contacto
- Management commands
- Autenticación completa

### ⏳ Fase 2: Deploy (1 card restante)
- [ ] **Card #16:** Deploy a Producción
  - Settings de producción
  - Deploy a Render.com
  - Configuración de dominio
  - Testing en producción

### 🔮 Fase 3: Futuras Mejoras
- [ ] Sistema de plantillas predefinidas
- [ ] Cloudinary para imágenes
- [ ] Email notifications
- [ ] Blog system
- [ ] Analytics dashboard
- [ ] Multi-idioma
- [ ] Pricing & payments
- [ ] API REST

---

## 🎯 Cards Completadas

### Core & Backend (1-6)
- [x] **Card #1:** Ambiente de Desarrollo (1h)
- [x] **Card #2:** Reestructurar Proyecto (2h)
- [x] **Card #3:** App Tenants - Modelos (2h)
- [x] **Card #4:** TenantMiddleware (2h)
- [x] **Card #5:** Testing Inicial (1h)
- [x] **Card #6:** App Website - Modelos CMS (3h)

### Frontend & UX (7-10)
- [x] **Card #7:** Frontend Base (Tailwind + HTMX) (3h)
- [x] **Card #8:** Sistema de Edición Inline (4h)
- [x] **Card #9:** Panel Cliente Simple (2h)
- [x] **Card #10:** Formulario de Contacto (2h)

### Gestión Avanzada (11-15)
- [x] **Card #11:** Django Admin Multi-Tenant (2h)
- [x] **Card #12:** Autenticación Clientes (3h)
- [x] **Card #13:** Sistema de Permisos (2h)
- [x] **Card #14:** Management Commands (3h)
- [x] **Card #15:** Dashboard Funcional Completo (5h) ⭐ **COMPLETADO**

### Deploy (16)
- [ ] **Card #16:** Deploy a Producción (4h)

**Total invertido:** ~37 horas  
**Restante:** ~4 horas  
**Progreso:** 93.75%

---

## 🤝 Contribuir

Este es un proyecto personal en desarrollo activo. Sugerencias y feedback son bienvenidos.

---

## 📄 Licencia

Proyecto privado - Todos los derechos reservados

---

## 📞 Contacto

**Desarrollador:** Sánchez  
**Proyecto:** SaaS MVP Multi-Tenant  
**Stack:** Django + Tailwind + HTMX

---

**🚀 MVP casi listo - Solo falta deploy (Card #16)**