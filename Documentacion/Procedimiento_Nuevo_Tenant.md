# Procedimiento canónico: agregar un nuevo tenant

Este documento reemplaza tener que re-derivar los pasos de onboarding cada vez que entra un cliente nuevo. Es el runbook de referencia (`#FLOW-01`); los kanbans por-cliente deben **seguir este procedimiento**, no reinventarlo.

> Alcance: alta *pre-pago / manual* (equipo interno da de alta al cliente, vía `provision_tenant`). Distinto del onboarding *post-pago* automático de `apps/orders/` (disparado por MercadoPago vía `apps/orders/views_onboarding.py::process_onboarding`) — no mezclar ambos flujos. El flujo automático ya elige un tema real (`Client.THEME_CHOICES`) desde el selector del checkout (`#DEUDA-02`/`#DEUDA-03`); este documento cubre el otro camino, el manual.

---

## 0. Conceptos que hay que tener claros antes de empezar

- **`--industry` ≠ `--theme`.** `--industry` controla solo el *contenido semilla* (colores sugeridos, textos de servicios) que usa `provision_tenant` para poblar `Section`/`Service`. `--theme` controla la *carpeta visual real* que usa el sitio — es el único que se guarda en `Client.template`, y debe ser uno de los valores de `Client.THEME_CHOICES`. Confundirlos hace que el tenant caiga en un tema genérico sin marca, sin ningún error visible — esto pasaba de verdad hasta que se separaron los dos flags (`#FLOW-01`, ver `apps/tenants/tests_provisioning.py`).
- **Temas disponibles hoy** (`Client.THEME_CHOICES`): `themes/default` (genérico) y `themes/servelec` (eléctrico, `#DEUDA-03` lo movió bajo `templates/themes/`). Si el rubro del cliente no encaja en ninguno, se lanza con `themes/default` y se agenda la creación de una carpeta de tema dedicada como tarea aparte — no se inventa un valor nuevo en `--theme` sin antes crear la carpeta `templates/<valor>/` correspondiente (`--theme` está validado por `argparse` contra `Client.THEME_CHOICES` en vivo, así que un valor inexistente falla al invocar el comando, no en silencio después).
- **El dominio vive en el modelo `Domain`, no en `Client`.** Nunca se referencia `client.domain` — no existe. Se usa `client.primary_domain` (puede ser `None`).
- **`provision_tenant` no crea imágenes ni `SEOConfig`.** Ningún `GalleryItem`, ninguna `Section(section_type='gallery')`, ningún `SEOConfig`. Esto es un gap real, documentado en el paso 2 — no un olvido de este runbook.

---

## 1. Desarrollo local

```bash
git checkout develop && git pull origin develop
git checkout -b feature/onboarding-<slug-cliente>
```

```bash
python manage.py provision_tenant <slug-cliente> \
  --industry=<electricidad|construccion|servicios_profesionales|portafolio> \
  --theme=<themes/default|themes/servelec> \
  --under-construction \
  --logo=/ruta/local/logo.png --phone="+56..." --whatsapp=56... \
  --settings=config.settings.development
```

- `--under-construction` si el sitio definitivo aún no está listo: sirve `errors/under_construction.html` (captura de leads) en vez del sitio real, en todas las rutas excepto `/dashboard`, `/auth`, `/superadmin`, `/contact`.
- **`localhost` es el dominio de sistema** (`apps/tenants/middleware.py::SYSTEM_DOMAINS`) — resuelve a `request.client = None`, nunca a un tenant. Sin `--domain`, el tenant recién creado **no es visible** visitando `localhost:8000` directo. Para verlo en dev sin dominio real: pasar `--domain=<slug>.localhost` (resuelve a `127.0.0.1` por RFC 6761, sin tocar `/etc/hosts` — mismo patrón que usa `seed_e2e_tenants.py`) y visitar `http://<slug>.localhost:8000`.
- Branding no pasado por flags se completa después vía `/dashboard/` o `/superadmin/`.

**Verificar de inmediato:**
```bash
python manage.py check_tenant_setup <slug-cliente> --settings=config.settings.development
```
Debe salir `[OK]` en tema visual. **El comando termina con exit code ≠ 0 si hay algún `[FAIL]`** (gate real desde `#FLOW-02`/`BOLT-05`, no solo informativo) — no seguir hasta que el tema y el dominio salgan en verde. Usar `--warn-only` únicamente para inspeccionar sin bloquear un script.

---

## 2. Pasos manuales obligatorios (no automatizados a propósito)

`check_tenant_setup` los reporta como `[FAIL]` o `[WARN]` según el caso — no son errores del comando, son follow-ups reales pendientes que `provision_tenant` no resuelve:

1. **SEO — `[FAIL]`, bloqueante.** No existe `SEOConfig` por defecto; `provision_tenant` no lo crea. El sitio funciona pero sin meta description/OG image reales hasta crear manualmente `SEOConfig(page_key='home', ...)` (y por cada página adicional que lo amerite) en `/superadmin/`.
2. **Galería — no bloqueante, pero falta si el cliente la va a usar.** `provision_tenant` no crea `Section(section_type='gallery')` ni ningún `GalleryItem`. Si el plan del cliente incluye galería de fotos, crear la sección y subir imágenes desde `/dashboard/gallery/` (el dashboard la crea sola al primer uso — ver `dashboard_gallery` en `apps/website/views.py`).
3. **Email de contacto — `[WARN]`.** `ClientEmailSettings` se auto-crea vía signal pero con `notify_mode='dashboard'` (los mensajes del formulario de contacto quedan solo visibles en el dashboard, no se envían por correo). Si el cliente espera notificaciones por email, configurar `provider` + `notify_mode` + credenciales SMTP/API en `/superadmin/` → Client → `ClientEmailSettings` inline.
4. **Contenido placeholder.** El seed de `_create_initial_content` usa textos genéricos ("Bienvenido a...", "Quiénes Somos"). `check_tenant_setup` solo falla si detecta marcadores explícitos (`lorem`/`placeholder`/`xxx`/`TODO`) — el copy genérico pasa el gate pero igual hay que reemplazarlo con contenido real del cliente antes de publicar.

---

## 3. QA antes del PR

```bash
python manage.py check_tenant_setup <slug-cliente> --settings=config.settings.development
python manage.py test apps.tenants.tests_isolation --settings=config.settings.development
```

`manage.py` ya fuerza UTF-8 en stdout/stderr (`#FLOW-01`) — los management commands con emojis/acentos no deberían crashear más en consolas Windows. Si de todas formas aparece un `UnicodeEncodeError` en algún comando que no pasó por esa limpieza, forzar manualmente:
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

1. Cargar contenido real de `Section`/`Service` (reemplaza el seed genérico) y crear `SEOConfig("home")` si no se hizo en el paso 2.
2. Confirmar tema visual final (crear carpeta dedicada si `themes/default` no alcanza).
3. Completar los pasos manuales de la sección 2 si no se hizo antes (galería, email de notificación).
4. Desactivar `mode_under_construction` (`/superadmin/` o shell).
5. Correr `check_tenant_setup <slug> --settings=config.settings.production` una última vez — debe salir 100% `[OK]` antes de anunciar el sitio al cliente.

---

## Referencia rápida de comandos

| Comando | Uso |
|---|---|
| `provision_tenant <slug> --industry=... --theme=...` | Alta completa de un tenant nuevo |
| `update_domain <slug> --domain=...` | Cambia/crea el dominio principal de un tenant existente (no toca otros tenants) |
| `check_tenant_setup <slug>` / `--all` / `--warn-only` | Audita tema, dominio, email, SEO, contenido — gate real (exit ≠ 0 con fallos, salvo `--warn-only`) |
| `list_tenants` | Panorama de todos los tenants activos |
| `python manage.py test apps.tenants.tests_isolation` | Verifica aislamiento de datos entre tenants (suite Django, no management command) |

**Eliminados** (código muerto, ya rotos antes de este runbook — no usar ni buscar en versiones viejas del repo): `create_localhost_client`, `scriptsAislamiento`, el comando `test_isolation` (reemplazado por la suite de arriba, `#MED-02`).
