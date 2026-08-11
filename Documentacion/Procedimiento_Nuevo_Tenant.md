# 🧭 Procedimiento canónico: Agregar un nuevo tenant

Este documento reemplaza tener que re-derivar los pasos de onboarding cada vez que entra un cliente nuevo. Es el runbook de referencia; los kanbans por-cliente (ej. `KanBan_RanchoCachimba.md`) deben **seguir este procedimiento**, no reinventarlo.

> Alcance: alta *pre-pago / manual* (equipo interno da de alta al cliente). Distinto del onboarding *post-pago* automático de `apps/orders/` (disparado por MercadoPago) — no mezclar ambos flujos.

---

## 0. Conceptos que hay que tener claros antes de empezar

- **`--industry` ≠ `--theme`.** `--industry` controla solo el *contenido semilla* (colores sugeridos, textos de servicios) que usa `provision_tenant` para poblar `Section`/`Service`. `--theme` controla la *carpeta visual real* que usa el sitio — es el único que se guarda en `Client.template`, y debe ser uno de los valores de `Client.THEME_CHOICES`. Confundirlos hace que el tenant caiga en un tema genérico sin marca, sin ningún error visible.
- **Temas disponibles hoy** (`Client.THEME_CHOICES`): `themes/default` (genérico) y `servelec` (eléctrico). Si el rubro del cliente no encaja en ninguno, se lanza con `themes/default` y se agenda la creación de una carpeta de tema dedicada como tarea aparte — no se inventa un valor nuevo en `--theme` sin antes crear la carpeta `templates/<valor>/` correspondiente.
- **El dominio vive en el modelo `Domain`, no en `Client`.** Nunca se referencia `client.domain` — no existe. Se usa `client.primary_domain` (puede ser `None`).

---

## 1. Desarrollo local

```bash
git checkout develop && git pull origin develop
git checkout -b feature/onboarding-<slug-cliente>
```

```bash
python manage.py provision_tenant <slug-cliente> \
  --industry=<electricidad|construccion|servicios_profesionales|portafolio> \
  --theme=<themes/default|servelec> \
  --under-construction \
  --logo=/ruta/local/logo.png --phone="+56..." --whatsapp=56... \
  --settings=config.settings.development
```

- `--under-construction` si el sitio definitivo aún no está listo: sirve `errors/under_construction.html` (captura de leads) en vez del sitio real, en todas las rutas excepto `/dashboard`, `/auth`, `/superadmin`, `/contact`.
- Sin `--domain`, se accede en dev vía `http://localhost:8000/?tenant=<slug-cliente>`.
- Branding no pasado por flags se completa después vía `/dashboard/` o `/superadmin/`.

**Verificar de inmediato:**
```bash
python manage.py check_tenant_setup <slug-cliente> --settings=config.settings.development
```
Debe salir `[OK]` en tema visual. Si sale `[FAIL]` en tema, el `--theme` usado no tiene carpeta real — no seguir hasta resolverlo (crear la carpeta o usar un valor válido de `THEME_CHOICES`).

---

## 2. Pasos manuales obligatorios (no automatizados a propósito)

`check_tenant_setup` los reporta como `[WARN]` — no son errores del comando, son follow-ups reales pendientes:

1. **Email de contacto**: `ClientEmailSettings` se auto-crea pero con `notify_mode='dashboard'` (los mensajes del formulario de contacto quedan solo visibles en el dashboard, no se envían por correo). Si el cliente espera notificaciones por email, configurar `provider` + `notify_mode` + credenciales SMTP/API en `/superadmin/` → Client → `ClientEmailSettings` inline.
2. **SEO**: no existe `SEOConfig` por defecto. El sitio funciona pero sin meta description/OG image reales hasta crear manualmente `SEOConfig(page_key='home', ...)` (y por cada página adicional que lo amerite) en `/superadmin/`.

---

## 3. QA antes del PR

```bash
python manage.py check_tenant_setup <slug-cliente> --settings=config.settings.development
python manage.py test_isolation --settings=config.settings.development
```

En Windows, si necesitás correr un comando que todavía no pasó por la limpieza de encoding (poco probable — `manage.py` ya fuerza UTF-8 para todos los commands), forzar manualmente por las dudas:
```powershell
$env:PYTHONIOENCODING = "utf-8"
```

PR de `feature/onboarding-<slug-cliente>` → `develop`. No tocar `apps/orders/` en este flujo.

---

## 4. Deploy a producción

```bash
# 1. PR develop -> main (dispara auto-deploy en Render)

# 2. Migraciones (si el PR incluye cambios de modelo)
python manage.py migrate --settings=config.settings.production

# 3. Provisionar el tenant real
python manage.py provision_tenant <slug-cliente> \
  --domain=<dominio-real.cl> \
  --industry=<...> --theme=<...> \
  --under-construction \
  --settings=config.settings.production

# 4. Si el dominio cambia más adelante (o se corrigió mal):
python manage.py update_domain <slug-cliente> --domain=<nuevo-dominio.cl> --settings=config.settings.production

# 5. QA gate en producción
python manage.py check_tenant_setup <slug-cliente> --settings=config.settings.production
```

**Render (dominio custom):**
1. Agregar el dominio del cliente y su variante `www.` a `EXTRA_DOMAINS` en `render.yaml`, commitear.
2. Render → Settings → Custom Domains → agregar el dominio.
3. En el proveedor DNS del cliente: `CNAME @ → <servicio>.onrender.com` (o el registro que indique Render).
4. Verificar `https://<dominio>` sirve la landing correcta (o "En construcción" si sigue activo ese modo).

---

## 5. Cuando el sitio definitivo está listo

1. Cargar contenido real de `Section`/`Service` (reemplaza el seed genérico).
2. Confirmar tema visual final (crear carpeta dedicada si `themes/default` no alcanza).
3. Completar los pasos manuales de la sección 2 si no se hizo antes.
4. Desactivar `mode_under_construction` (admin o shell).
5. Opcional: `python manage.py verify_search_console --domain <dominio>`.

---

## Referencia rápida de comandos

| Comando | Uso |
|---|---|
| `provision_tenant <slug> --industry=... --theme=...` | Alta completa de un tenant nuevo |
| `update_domain <slug> --domain=...` | Cambia/crea el dominio principal de un tenant existente |
| `check_tenant_setup <slug>` / `--all` | Audita tema, dominio, email, SEO — correr después de provisionar y antes de cerrar el onboarding |
| `list_tenants` | Panorama de todos los tenants activos |
| `test_isolation` | Verifica aislamiento de datos entre tenants |

**Eliminados** (código muerto/roto, no usar ni buscar en versiones viejas del repo): `create_localhost_client`, `scriptsAislamiento`.
