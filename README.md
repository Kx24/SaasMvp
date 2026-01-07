# 🚀 SaaS MVP - Multi-Tenant Website Platform

Sistema de gestión de sitios web multi-tenant con Django. Permite crear y gestionar múltiples sitios web de clientes desde una única plataforma, con **templates personalizables por tenant**.

---

## 📊 Estado del Proyecto

**Progreso:** Deploy a producción completado ✅

```
✅ Core & Backend          [████████████████] 100%
✅ Frontend & Dashboard    [████████████████] 100%
✅ Gestión Avanzada        [████████████████] 100%
✅ Templates por Tenant    [████████████████] 100%
✅ Deploy & Production     [████████████████] 100%
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

### 📄 Templates por Tenant (Cards #A-C)
- [x] **Card #A:** TenantTemplateLoader dinámico
- [x] **Card #B:** Template `_default` completo y modular
- [x] **Card #C:** Comando `create_tenant` mejorado + estructura media

### 🚀 Deploy (Card #D) ✅ COMPLETADO
- [x] **Card #D:** Deploy a Render
  - [x] Template loader robusto (maneja SafeString)
  - [x] Middleware con fallback HTML (sin dependencia de templates)
  - [x] Comando `setup_production` idempotente
  - [x] Build.sh limpio (solo preparación)
  - [x] Test local de producción
  - [x] Variables de entorno documentadas

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
│  3. DEFAULT_TENANT_SLUG       Fallback configurado             │
│  4. HTML amigable             Si no encuentra nada             │
│                                                                 │
│  Tabla Domain:                                                  │
│  ├── servelec-ingenieria.cl (primary)                          │
│  ├── saasmvp-kajv.onrender.com (subdomain)                     │
│  ├── localhost (development)                                    │
│  └── 127.0.0.1 (development)                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

### Backend
- **Django 5.2+** - Framework web
- **PostgreSQL** - Base de datos (producción)
- **SQLite** - Base de datos (desarrollo)
- **Python 3.11+** - Lenguaje
- **Gunicorn** - Servidor WSGI (producción)
- **WhiteNoise** - Archivos estáticos

### Frontend
- **Tailwind CSS 3.x** - Framework CSS (CDN)
- **HTMX 1.9+** - Interactividad sin JS complejo
- **Alpine.js 3.x** - Estado reactivo ligero

### Deploy
- **Render.com** - Hosting
- **PostgreSQL (Render)** - Base de datos
- **SSL automático** - Certificados HTTPS

---

## 🚀 Instalación y Setup

### Desarrollo Local

```bash
# 1. Clonar repositorio
git clone <repo-url>
cd SaaSMVP

# 2. Crear virtualenv
python -m venv env
env\Scripts\activate  # Windows
source env/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar .env
copy .env.example .env
# Editar .env con tus configuraciones

# 5. Migraciones
python manage.py migrate

# 6. Crear tenant inicial
python manage.py setup_production --domain=localhost --tenant=servelec

# 7. Iniciar servidor
python manage.py runserver
```

### Test de Producción Local

```bash
# Windows
test_production.bat

# Linux/Mac
chmod +x test_production.sh
./test_production.sh
```

### URLs de Acceso
- **Sitio público:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/superadmin/
- **Dashboard:** http://127.0.0.1:8000/dashboard/

---

## 📖 Management Commands

### setup_production
Configura datos iniciales para producción (idempotente):
```bash
python manage.py setup_production
python manage.py setup_production --domain=miapp.com --tenant=miempresa
```

### create_tenant
Crea un nuevo tenant completo:
```bash
python manage.py create_tenant "Mi Empresa" miempresa.cl
python manage.py create_tenant "Mi Empresa" miempresa.cl \
    --email=admin@miempresa.cl \
    --password=secreto123 \
    --color=#ff6600
```

### Opciones de create_tenant:
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

---

## 🚀 Deploy a Render

### Variables de Entorno Requeridas

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `SECRET_KEY` | (generada) | Clave secreta Django |
| `DEBUG` | `False` | Siempre False en producción |
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` | Settings de producción |
| `DATABASE_URL` | (automática) | Conexión a PostgreSQL |
| `DEFAULT_TENANT_SLUG` | `servelec` | Tenant por defecto |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts permitidos |

### Proceso de Deploy

1. **Push a GitHub:**
```bash
git add .
git commit -m "deploy: production ready"
git push origin main
```

2. **En Render Dashboard:**
   - Manual Deploy → Clear build cache & deploy

3. **Verificar logs:**
```
✅ BUILD COMPLETADO
✅ SETUP COMPLETADO
```

4. **Agregar dominios personalizados:**
   - Settings → Custom Domains
   - Agregar: `servelec-ingenieria.cl`
   - Configurar DNS (CNAME)

---

## 📁 Estructura del Proyecto

```
SaaSMVP/
├── apps/
│   ├── tenants/
│   │   ├── template_loader.py   # Robusto, maneja SafeString
│   │   ├── middleware.py        # HTML fallback si no hay tenant
│   │   ├── models.py            # Client, ClientSettings, Domain
│   │   └── management/commands/
│   │       ├── create_tenant.py
│   │       └── setup_production.py
│   ├── website/
│   │   ├── models.py            # Section, Service, Testimonial
│   │   └── views.py
│   └── accounts/
│       └── models.py            # UserProfile
│
├── config/settings/
│   ├── base.py                  # Settings base con loaders
│   ├── development.py           # Desarrollo
│   └── production.py            # Producción
│
├── templates/
│   ├── tenants/
│   │   └── _default/            # Template base
│   │       └── landing/
│   │           └── home.html
│   ├── base.html
│   ├── dashboard/
│   └── auth/
│
├── build.sh                     # Script de build para Render
├── test_production.bat          # Test local (Windows)
├── test_production.sh           # Test local (Linux/Mac)
├── requirements.txt
└── render.yaml
```

---

## 🔐 Sistema de Permisos

| Rol | Acceso Admin | Ve Tenants | Ve Todo | CRUD |
|-----|--------------|------------|---------|------|
| **Superuser** | ✅ | ✅ | ✅ | ✅ Todo |
| **Staff Tenant** | ✅ (filtrado) | ❌ | Solo su tenant | ✅ Su contenido |
| **Usuario Normal** | ❌ | ❌ | Solo público | ❌ |

---

## 🗺️ Roadmap Completado

### ✅ Fase 1: MVP Core
- Multi-tenancy funcional
- Frontend moderno y responsive
- Dashboard cliente completo
- Management commands
- Autenticación y permisos

### ✅ Fase 2: Templates por Tenant
- TenantTemplateLoader
- Template _default modular
- Estructura media por tenant
- Comando create_tenant mejorado

### ✅ Fase 3: Deploy
- Build.sh robusto
- Setup de producción idempotente
- Test local de producción
- Deploy a Render funcional

### 🔮 Fase 4: Futuras Mejoras
- [ ] Cloudinary para imágenes
- [ ] Email notifications (SMTP por tenant)
- [ ] Panel de personalización visual
- [ ] Sistema de plantillas predefinidas
- [ ] Blog system
- [ ] Multi-idioma
- [ ] API REST
- [ ] Pagos y suscripciones

---

## 📞 Contacto

**Desarrollador:** Sánchez  
**Proyecto:** SaaS MVP Multi-Tenant  
**Stack:** Django 5.2 + Tailwind CSS + HTMX + Alpine.js

---

## 🎉 Estado Actual

**MVP COMPLETADO Y DEPLOYADO** 

- ✅ Sistema multi-tenant funcionando
- ✅ Templates personalizables por tenant
- ✅ Deploy a Render operativo
- ✅ Admin y Dashboard funcionales
- ✅ Gestión de dominios múltiples

**URL Producción:** https://saasmvp-kajv.onrender.com
