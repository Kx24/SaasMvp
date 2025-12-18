# 🚀 SaaS MVP - Multi-Tenant Website Platform

Sistema de gestión de sitios web multi-tenant con Django. Permite crear y gestionar múltiples sitios web de clientes desde una única plataforma.

---

## 📊 Estado del Proyecto

**Progreso:** 10/12 cards completadas (83%)

```
✅ Core & Backend          [████████████████] 100%
✅ Frontend & Dashboard    [████████████████] 100%
⏳ Deploy & Production     [████████░░░░░░░░]  0%
```

**Última actualización:** Diciembre 2024

---

## ✅ Funcionalidades Completadas

### 🏗️ Core (Cards #1-6)
- [x] **Card #1:** Ambiente de desarrollo configurado
- [x] **Card #2:** Estructura modular del proyecto
- [x] **Card #3:** Sistema multi-tenant (Client, ClientSettings)
- [x] **Card #4:** TenantMiddleware (detección automática por dominio)
- [x] **Card #5:** Testing de aislamiento de datos
- [x] **Card #6:** Modelos CMS (Section, Service, Testimonial, ContactSubmission)

### 🎨 Frontend (Cards #7-8)
- [x] **Card #7:** Frontend base con Tailwind CSS + HTMX + Alpine.js
- [x] **Card #8:** Sistema de edición inline (modales HTMX, sin reloads)

### 📊 Dashboard (Cards #9-10)
- [x] **Card #9:** Panel de cliente (/dashboard/)
  - Estadísticas en tiempo real
  - Gestión de secciones y servicios
  - Administración de contactos
- [x] **Card #10:** Formulario de contacto funcional
  - Validación frontend y backend
  - Guardado en BD con IP tracking
  - Notificaciones toast

### ⏳ Pendiente
- [ ] **Card #11:** Preparar deploy (settings producción, requirements)
- [ ] **Card #12:** Deploy a producción (Render.com + dominio)

---

## 🏛️ Arquitectura

### Multi-Tenant con Shared Database
```
┌─────────────────────────────────────────┐
│           Base de Datos Única           │
├─────────────────────────────────────────┤
│  Client 1 → Sections, Services...       │
│  Client 2 → Sections, Services...       │
│  Client 3 → Sections, Services...       │
└─────────────────────────────────────────┘
         ↑
         │ TenantMiddleware (detecta por dominio)
         │
┌─────────────────────────────────────────┐
│  cliente1.com → Client 1 data           │
│  cliente2.com → Client 2 data           │
│  cliente3.com → Client 3 data           │
└─────────────────────────────────────────┘
```

### Doble Interfaz
```
┌─────────────────────────────────────────┐
│  SUPERADMIN → /admin/ (Django Admin)    │
│  - Crear/gestionar tenants              │
│  - Ver todos los datos                  │
│  - Configuración global                 │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  CLIENTE → /dashboard/                  │
│  - Editar SUS secciones                 │
│  - Gestionar SUS servicios              │
│  - Ver SUS contactos                    │
└─────────────────────────────────────────┘
```

---

## 🛠️ Stack Tecnológico

### Backend
- **Django 5.0+** - Framework web
- **PostgreSQL** - Base de datos
- **Python 3.11+** - Lenguaje

### Frontend
- **Tailwind CSS 3.x** - Framework CSS (CDN)
- **HTMX 1.9+** - Interactividad sin JS complejo
- **Alpine.js 3.x** - Estado reactivo ligero

### Características
- ✅ Sin CKEditor (TextField simple)
- ✅ Sin Cloudinary (ImageField local)
- ✅ Sin npm/webpack (CDN directo)
- ✅ Arquitectura limpia y escalable

---

## 📁 Estructura del Proyecto

```
SaaSMVP/
├── config/                      # Configuración Django
│   ├── settings/
│   │   ├── base.py             # Settings compartidos
│   │   ├── development.py      # Local
│   │   └── production.py       # Producción
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                        # Apps por dominio
│   ├── tenants/                # Multi-tenancy
│   │   ├── models.py           # Client, ClientSettings
│   │   ├── middleware.py       # TenantMiddleware
│   │   ├── admin.py
│   │   └── managers.py
│   │
│   ├── website/                # Sitios públicos
│   │   ├── models.py           # Section, Service, Testimonial, ContactSubmission
│   │   ├── views.py            # Home, Dashboard, Edición
│   │   ├── forms.py            # ContactForm, SectionForm, ServiceForm
│   │   ├── urls.py
│   │   └── templatetags/
│   │       └── website_tags.py # Template tags personalizados
│   │
│   └── core/                   # Utilidades compartidas
│       ├── models.py           # BaseModel
│       └── utils.py
│
├── templates/
│   ├── base.html               # Template base
│   ├── components/             # Navbar, Footer
│   ├── landing/                # Sitio público
│   │   └── home.html
│   ├── dashboard/              # Panel cliente
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── sections.html
│   │   ├── services.html
│   │   └── contacts.html
│   ├── auth/                   # Login modals
│   └── partials/               # Fragmentos HTMX
│
├── static/
│   ├── css/
│   ├── js/
│   └── img/
│
├── media/                      # Uploads (dev only)
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

# 7. Crear cliente default
python manage.py shell
```

```python
from apps.tenants.models import Client

client = Client.objects.create(
    name="Cliente Default",
    slug="default",
    domain="127.0.0.1",
    is_active=True
)

client.settings.company_name = "Mi Empresa"
client.settings.primary_color = "#2563eb"
client.settings.secondary_color = "#1e40af"
client.settings.contact_email = "contacto@example.com"
client.settings.save()

print(f"✅ Cliente creado: {client.name}")
exit()
```

```bash
# 8. Iniciar servidor
python manage.py runserver
```

### Acceso

- **Sitio público:** http://127.0.0.1:8000/
- **Django Admin:** http://127.0.0.1:8000/admin/
- **Dashboard cliente:** http://127.0.0.1:8000/dashboard/

---

## 📖 Uso

### Para Superadmin

1. **Crear nuevo cliente:**
   - Ir a `/admin/tenants/client/`
   - Clic en "Agregar Client"
   - Configurar nombre, dominio, slug
   - Configurar ClientSettings (colores, email, etc)

2. **Gestionar contenido:**
   - Ver/editar contenido de todos los clientes
   - Crear secciones, servicios, testimonios
   - Ver mensajes de contacto

### Para Cliente

1. **Login:**
   - Ir al sitio público
   - Clic en "Iniciar Sesión"
   - Usar credenciales proporcionadas

2. **Dashboard:**
   - Ver estadísticas
   - Editar secciones (título, subtítulo)
   - Gestionar servicios (CRUD completo)
   - Ver contactos recibidos

3. **Edición Inline:**
   - Navegar al sitio público (logueado)
   - Clic en "Editar" en cualquier sección/servicio
   - Editar en modal sin reload
   - Cambios se reflejan instantáneamente

---

## 🧪 Testing

### Tests de Aislamiento
```bash
# Verificar que los datos están aislados por tenant
python manage.py test_isolation
```

### Verificar URLs
```bash
# Ver todas las URLs configuradas
python check_urls.py
```

---

## 🗺️ Roadmap

### ✅ Fase 1: MVP Core (Completado)
- Multi-tenancy funcional
- Frontend moderno
- Dashboard cliente
- Formulario de contacto

### ⏳ Fase 2: Deploy (En Progreso)
- [ ] Settings de producción
- [ ] Deploy a Render.com
- [ ] Configuración de dominio
- [ ] Testing en producción

### 🔮 Fase 3: Futuras Mejoras
- [ ] Sistema de plantillas
- [ ] Provisioning automático
- [ ] Email notifications
- [ ] Blog system
- [ ] Analytics dashboard
- [ ] Multi-idioma
- [ ] Pricing & payments
- [ ] API REST

---

## 🤝 Contribuir

Este es un proyecto personal en desarrollo activo. Sugerencias y feedback son bienvenidos.

---

## 📄 Licencia

Proyecto privado - Todos los derechos reservados

---

## 📞 Contacto

**Desarrollador:** [Tu Nombre]  
**Email:** [tu@email.com]  
**GitHub:** [tu-usuario]

---

## 🎯 Cards Completadas

- [x] **Card #1:** Ambiente de Desarrollo (1h)
- [x] **Card #2:** Reestructurar Proyecto (2h)
- [x] **Card #3:** App Tenants - Modelos (2h)
- [x] **Card #4:** TenantMiddleware (2h)
- [x] **Card #5:** Testing Inicial (1h)
- [x] **Card #6:** App Website - Modelos CMS (3h)
- [x] **Card #7:** Frontend Base (Tailwind + HTMX) (3h)
- [x] **Card #8:** Sistema de Edición Inline (4h)
- [x] **Card #9:** Panel Cliente Simple (2h)
- [x] **Card #10:** Formulario de Contacto (2h)
- [ ] **Card #11:** Preparar Deploy (3h)
- [ ] **Card #12:** Deploy a Producción (3h)

**Total invertido:** ~24 horas  
**Restante:** ~6 horas  
**Progreso:** 83%

---

**🚀 MVP listo para deploy en 2 cards más**