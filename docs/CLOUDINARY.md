# ☁️ Cloudinary - Documentación de Integración

> **Última actualización:** Enero 2026  
> **Versión:** 1.0.0  
> **Estado:** Producción

---

## 📋 Información General

| Campo | Valor |
|-------|-------|
| **Cloud Name** | `darwud7cz` |
| **Plan** | Free (25 créditos/mes) |
| **Uso compartido** | Sí - cuenta única para todos los tenants |
| **Aislamiento** | Por carpetas (`/{tenant_slug}/...`) |

---

## 🔐 Credenciales

### Variables de Entorno Requeridas

```bash
# .env (NUNCA commitear este archivo)
CLOUDINARY_CLOUD_NAME=darwud7cz
CLOUDINARY_API_KEY=xxxxxxxxxx
CLOUDINARY_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxx
```

### Ubicación de Secretos

| Entorno | Ubicación |
|---------|-----------|
| **Local** | Archivo `.env` en raíz del proyecto |
| **Producción (Render)** | Environment Variables en Dashboard |
| **CI/CD** | GitHub Secrets (si aplica) |

### ⚠️ Reglas de Seguridad

1. **NUNCA** hardcodear credenciales en código
2. **NUNCA** commitear `.env` al repositorio
3. **NUNCA** loggear `API_SECRET` en ningún nivel
4. Rotar `API_SECRET` anualmente o ante sospecha de exposición
5. Solo el `CLOUD_NAME` puede aparecer en logs o frontend

---

## 📁 Convención de Carpetas

### Estructura de Folders en Cloudinary

```
/{tenant_slug}/
├── sections/          # Imágenes de secciones (hero, about, etc.)
├── services/          # Imágenes de servicios
├── testimonials/      # Avatares de testimonios
├── branding/          # Logos y elementos de marca
└── gallery/           # Galería general (futuro)
```

### Ejemplos Concretos

```
/servelec-ingenieria/
├── sections/
│   ├── hero-main.jpg
│   └── about-team.jpg
├── services/
│   ├── instalaciones-electricas.jpg
│   └── mantenimiento-industrial.jpg
└── branding/
    └── logo.png

/cliente-demo/
├── sections/
│   └── hero-main.jpg
└── branding/
    └── logo.png
```

### Reglas de Naming

| Regla | Ejemplo Correcto | Ejemplo Incorrecto |
|-------|------------------|-------------------|
| Slug en minúsculas | `servelec-ingenieria` | `Servelec_Ingenieria` |
| Guiones, no underscores | `hero-main` | `hero_main` |
| Sin espacios | `mantenimiento-industrial` | `mantenimiento industrial` |
| Sin caracteres especiales | `seccion-nosotros` | `sección-ñoños` |
| Descriptivo y corto | `hero-main` | `imagen-principal-de-la-seccion-hero-del-home` |

---

## 🎨 Presets de Transformación

### Presets Definidos

| Preset | Uso | Transformación |
|--------|-----|----------------|
| `thumbnail` | Miniaturas en admin/listados | `c_fill,w_300,h_200,f_auto,q_auto` |
| `hero` | Imágenes hero full-width | `c_fill,w_1200,h_600,f_auto,q_auto` |
| `service_card` | Cards de servicios | `c_fill,w_400,h_300,f_auto,q_auto` |
| `logo` | Logos de clientes | `c_fit,w_200,h_80,f_auto` |
| `avatar` | Avatares testimonios | `c_fill,w_100,h_100,f_auto,q_auto,r_max` |

### Uso en Templates

```django
{% load website_tags %}

{# Usando preset definido #}
<img src="{% cloudinary_url section.image 'hero' %}" alt="{{ section.title }}">

{# Con fallback a placeholder #}
<img src="{% cloudinary_url service.image 'service_card' %}" alt="{{ service.name }}">
```

### ⚠️ Regla Crítica

**Solo usar presets definidos.** No generar transformaciones dinámicas desde input de usuario.

```python
# ✅ CORRECTO
url = get_cloudinary_url(image, preset='thumbnail')

# ❌ INCORRECTO - Nunca hacer esto
url = get_cloudinary_url(image, width=request.GET['w'], height=request.GET['h'])
```

---

## 🚀 Onboarding de Desarrolladores

### Checklist de Setup

- [ ] Solicitar acceso al vault/gestor de secretos
- [ ] Copiar `.env.example` a `.env`
- [ ] Configurar variables de Cloudinary en `.env`
- [ ] Verificar conexión: `python manage.py shell` → `cloudinary.api.ping()`
- [ ] Leer esta documentación completa
- [ ] Entender convención de carpetas
- [ ] Revisar presets disponibles

### Comandos de Verificación

```bash
# Verificar configuración
python manage.py check_cloudinary

# Ver uso actual de créditos
python manage.py cloudinary_usage

# Listar assets de un tenant
python manage.py audit_cloudinary_assets servelec-ingenieria
```

### Permisos por Rol

| Rol | Puede subir | Puede borrar | Ve dashboard |
|-----|-------------|--------------|--------------|
| SuperAdmin | ✅ | ✅ (manual) | ✅ |
| ClientAdmin | ✅ (su tenant) | ❌ | ❌ |
| Developer | ✅ (dev only) | ❌ | ✅ |

---

## 📊 Monitoreo y Alertas

### Dashboard Interno

- **URL:** `/admin/cloudinary/usage/` (solo superadmin)
- **Datos:** Créditos usados, límite, % consumido
- **Refresh:** Manual o diario automático

### Alertas Configuradas

| Trigger | Acción |
|---------|--------|
| 70% créditos | Log warning |
| 85% créditos | Email a admin |
| 95% créditos | Bloquear uploads nuevos |

### Dashboard Oficial

- **URL:** https://console.cloudinary.com/console/darwud7cz/dashboard
- **Acceso:** Solo SuperAdmins con credenciales de Cloudinary

---

## ⚠️ Decisiones de Arquitectura (ADRs)

### ADR-001: No usar Sub-Accounts

**Decisión:** Usar carpetas para aislamiento, no sub-accounts.

**Razón:** 
- Plan Free no soporta sub-accounts
- Complejidad innecesaria para <50 tenants
- Folder-based isolation es suficiente

**Fecha de revisión:** Julio 2026 (o al alcanzar 30 tenants)

### ADR-002: No usar Signed URLs por defecto

**Decisión:** URLs públicas para contenido de landing pages.

**Razón:**
- El contenido es público por naturaleza
- Signed URLs agregan overhead
- Afecta caching de CDN negativamente

**Excepción:** Contenido privado futuro (documentos, facturas)

### ADR-003: No borrado automático

**Decisión:** Solo borrado manual con aprobación.

**Razón:**
- Riesgo de pérdida irreversible
- Soft-delete primero, hard-delete después de 30 días
- Auditoría requerida antes de purgas

---

## 🔄 Procedimientos

### Subir Nueva Imagen (Admin)

1. Ir al admin de Django
2. Seleccionar modelo (Section, Service, etc.)
3. Usar widget de Cloudinary para seleccionar/subir
4. La imagen se guarda automáticamente en la carpeta correcta

### Migrar Contenido Existente

```bash
# Script de migración (ejecutar una vez)
python manage.py migrate_to_cloudinary --tenant=servelec-ingenieria
```

### Backup de Assets

```bash
# Exportar lista de assets (no descarga archivos)
python manage.py audit_cloudinary_assets servelec-ingenieria --output=backup.csv
```

---

## 📈 Plan de Upgrade

### Triggers para Upgrade a Plus

- [ ] Consumo > 80% de créditos por 2 meses consecutivos
- [ ] Más de 10 tenants activos
- [ ] Necesidad de features Plus (ej: named transformations)

### Estimación de Costos

| Tenants | Plan Recomendado | Costo Aprox. |
|---------|------------------|--------------|
| 1-5 | Free | $0/mes |
| 6-15 | Plus | $89/mes |
| 16-50 | Advanced | $249/mes |

### Documentación de Upgrade

Ver: `/docs/CLOUDINARY_UPGRADE.md` (cuando se cree)

---

## 🆘 Troubleshooting

### Error: "Invalid API credentials"

```bash
# Verificar variables
echo $CLOUDINARY_CLOUD_NAME
echo $CLOUDINARY_API_KEY
# NUNCA imprimir API_SECRET

# Verificar en Django
python manage.py shell
>>> import cloudinary
>>> cloudinary.config()
```

### Error: "Resource not found"

- Verificar que el `public_id` incluye la carpeta completa
- Ejemplo: `servelec-ingenieria/sections/hero-main`, no solo `hero-main`

### Imágenes no se muestran

1. Verificar URL en browser directamente
2. Revisar que la transformación es válida
3. Confirmar que el asset existe en dashboard de Cloudinary

---

## 📞 Contactos

| Rol | Responsabilidad |
|-----|-----------------|
| Tech Lead | Decisiones de arquitectura |
| DevOps | Gestión de secretos y producción |
| Soporte Cloudinary | support@cloudinary.com |

---

*Documento mantenido por el equipo de desarrollo. Actualizar ante cualquier cambio en configuración o procedimientos.*
