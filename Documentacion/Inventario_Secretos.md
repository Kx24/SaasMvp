# Inventario de secretos (`#SEC-03`)

Fuente de verdad de **qué** secretos usa el sistema, **para qué**, y **dónde viven**. Construido rastreando cada lectura real de variable de entorno en el código (`config()`/`os.environ.get`), no de memoria — ver método al final.

> **Lo que este documento NO puede confirmar:** qué valores están efectivamente configurados hoy en el dashboard de Render — eso solo lo ve quien tiene acceso a esa cuenta. La columna "¿Configurado en Render?" queda para completar a mano.

---

## ⚠️ Hallazgo urgente — verificar antes de lo demás

**`DJANGO_SUPERUSER_PASSWORD` no estaba declarada en `render.yaml`, ni siquiera como recordatorio.** `apps/tenants/management/commands/setup_production.py` (corre en cada build vía `build.sh`) creaba el primer superusuario de `/superadmin/` con usuario `admin` / email `admin@example.com`, y **si esa env var nunca se seteó, con la contraseña hardcodeada `admin123456`** — visible en el propio código fuente. El comando es idempotente (si ya existe un superuser, no hace nada más), así que esto solo importa para el **primer** deploy de la base de datos actual.

**Acción pedida:** entrar a `/superadmin/` en producción y confirmar que el usuario `admin` (o el que sea el superuser actual) tiene una contraseña real, no `admin123456`. Si no estás seguro de cuál se usó en el primer deploy, cambiala ahora por las dudas — es gratis y toma un minuto. El código ya se corrigió (`apps/tenants/management/commands/setup_production.py`): de acá en más, si falta `DJANGO_SUPERUSER_PASSWORD` el build falla en vez de crear una cuenta con clave débil.

---

## Inventario completo

| Variable | Para qué | Sensibilidad | Dónde se lee | Servicios que la necesitan | Declarada en `render.yaml` | ¿Configurada en Render? |
|---|---|---|---|---|---|---|
| `SECRET_KEY` | Firma de sesiones/cookies/tokens de Django | 🔴 Secreto crítico | `config/settings/production.py` | web, ambos crons | ✅ `generateValue: true` (Render la genera sola) | — |
| `DATABASE_URL` | Conexión a Postgres (incluye password) | 🔴 Secreto crítico | `config/settings/production.py` | web, ambos crons | ✅ `fromDatabase` (automático) | — |
| `DJANGO_SUPERUSER_PASSWORD` | Password del primer superusuario `/superadmin/` | 🔴 Secreto crítico | `apps/tenants/management/commands/setup_production.py` | web (solo en build) | ✅ `sync: false` *(agregado en esta card — antes no estaba)* | **☐ Verificar — ver hallazgo urgente arriba** |
| `EMAIL_HOST_PASSWORD` | Password SMTP (Zoho) | 🔴 Secreto crítico | `config/settings/production.py` | web, ambos crons (envían correo) | ✅ `sync: false` | ☐ |
| `MP_ACCESS_TOKEN` | Token privado de MercadoPago (crea/consulta pagos) | 🔴 Secreto crítico | `apps/orders/services/mercadopago_service.py` | web (checkout) | ✅ `sync: false` *(agregado en esta card)* | ☐ |
| `MP_WEBHOOK_SECRET` | Valida la firma HMAC de los webhooks de MP (`#AUD-02`) | 🔴 Secreto crítico | `apps/orders/services/mercadopago_service.py` | web (webhook) | ✅ `sync: false` *(agregado en esta card)* | ☐ |
| `CLOUDINARY_API_SECRET` | Firma las subidas a Cloudinary | 🔴 Secreto crítico | `apps/core/cloudinary_utils.py` | web (todo lo que sube media) | ✅ `sync: false` *(agregado en esta card)* | ☐ |
| `EMAIL_HOST_USER` | Cuenta SMTP (identificador, no solo secreto) | 🟡 Semi-sensible | `config/settings/production.py` | web, ambos crons | ✅ `sync: false` | ☐ |
| `CLOUDINARY_API_KEY` | Identificador de API de Cloudinary (va emparejado con el secret) | 🟡 Semi-sensible | `apps/core/cloudinary_utils.py` | web | ✅ `sync: false` *(agregado en esta card)* | ☐ |
| `MP_PUBLIC_KEY` | Clave pública de MP (se expone en el JS del checkout a propósito) | 🟢 No secreta | `apps/orders/services/mercadopago_service.py` + templates de checkout | web | ✅ `sync: false` *(agregado en esta card — no es secreta, pero conviene tenerla junto al resto del set de MP)* | ☐ |
| `CLOUDINARY_CLOUD_NAME` | Nombre de la cuenta Cloudinary (no secreto) | 🟢 No secreta | `apps/core/cloudinary_utils.py` | web | ✅ `sync: false` *(agregado en esta card)* | ☐ |
| `MP_SANDBOX` | `True`=modo sandbox (default seguro), `False`=cobros reales | 🟢 Config, no secreto — **decisión de negocio** | `config/settings/base.py` (`default=True`) | web | ✅ `sync: false` *(deliberadamente sin `value:` — pasar a `False` habilita cobros reales, no es un valor que este documento deba fijar)* | ☐ **Confirmar que está en `False` antes de vender de verdad** |
| `BASE_DOMAIN` | Dominio raíz para armar subdominios de tenants | 🟢 Config | `config/settings/production.py` | web, ambos crons | ✅ `value: "onrender.com"` | ✅ (ya en el blueprint) |
| `DEFAULT_TENANT_SLUG` | Tenant que se sirve si no matchea ningún dominio | 🟢 Config | `config/settings/production.py` | web, ambos crons | ✅ `value: "servelec"` | ✅ |
| `EXTRA_DOMAINS` | Dominios custom de clientes, separados por coma | 🟢 Config (lista pública igual) | `config/settings/production.py` | web, ambos crons | ✅ | ✅ |
| `EMAIL_HOST` | Servidor SMTP | 🟢 Config | `config/settings/production.py` | web, ambos crons | ✅ `value: "smtp.zoho.com"` | ✅ |
| `EMAIL_PORT` / `EMAIL_USE_TLS` / `EMAIL_USE_SSL` | Config de conexión SMTP | 🟢 Config | `config/settings/production.py` | web, ambos crons | ✅ (`EMAIL_USE_SSL` no declarada, tiene default seguro) | ✅ |
| `EMAIL_ASYNC` | Encolar emails vs. enviar sync (`#MED-01`) | 🟢 Config | `config/settings/production.py` (`default=True`) | web | No declarada (usa el default) | — |
| `DEFAULT_FROM_EMAIL` / `SUPPORT_EMAIL` | Remitente / casilla de soporte mostrada al usuario | 🟢 Config | `config/settings/base.py` | web | No declaradas (usan default) | — |
| `BASE_URL` | URL base para links absolutos en emails | 🟢 Config | `config/settings/base.py` | web | No declarada (usa default `localhost`, **revisar si hace falta en prod**) | ☐ |
| `DEBUG` | Nunca debe ser `True` en producción | 🟢 Config | `config/settings/production.py` | web, ambos crons | ✅ `value: "False"` | ✅ |
| `RENDER_EXTERNAL_HOSTNAME` | La provee Render automáticamente, no se configura a mano | 🟢 Auto | `config/settings/base.py`, `setup_production.py` | web | Automática de Render | — |
| `TENANT_DOMAINS` | Mapeo tenant→dominios para `setup_production` (formato `slug:dom1,dom2\|slug2:...`) | 🟢 Config | `apps/tenants/management/commands/setup_production.py` | web (build) | No declarada — **solo se usa si hay más de 1 tenant en el mismo deploy** | ☐ Confirmar si aplica |

---

## Política de rotación

No hay rotación automatizada — es manual, y por eso queda documentada acá qué exige cada tipo:

| Variable | Cuándo rotar | Cómo, sin causar downtime |
|---|---|---|
| `SECRET_KEY` | Solo ante sospecha de compromiso — rotarla sin necesidad invalida **todas** las sesiones activas y las firmas de `cookies`/tokens en tránsito. | Generar una nueva (`django.core.management.utils.get_random_secret_key()`), setear en Render, redeploy. Todos los usuarios logueados pierden sesión. |
| `DATABASE_URL` | Si Render la rota (cambio de plan, etc.) o ante sospecha de compromiso. | La gestiona Render vía `fromDatabase` — no se edita a mano salvo migrar de proveedor. |
| `MP_ACCESS_TOKEN` / `MP_WEBHOOK_SECRET` / `MP_PUBLIC_KEY` | Cada 6-12 meses como buena práctica, o inmediato ante sospecha. `MP_WEBHOOK_SECRET` **tiene que rotarse coordinado**: cambiarla en el panel de MP primero, verificar que el webhook nuevo firma con la clave nueva, recién ahí actualizar Render (si se invierte el orden, los webhooks entrantes fallan validación durante la ventana — `#AUD-02` los devuelve `401`, no se pierden pero sí se acumulan hasta que MP reintente). |
| `CLOUDINARY_API_SECRET` / `CLOUDINARY_API_KEY` | Ante sospecha de compromiso, o si se detecta uso anómalo en el dashboard de Cloudinary. | Regenerar en el panel de Cloudinary, actualizar Render, redeploy — no requiere coordinar nada externo (a diferencia del webhook de MP). |
| `EMAIL_HOST_PASSWORD` | Según la política de Zoho / cuando cambie quien administra la casilla. | Cambiar en Zoho, actualizar Render. Sin downtime — solo afecta el próximo envío. |
| `DJANGO_SUPERUSER_PASSWORD` | Solo importa para el *primer* deploy (el comando es idempotente después). Si se sospecha que se usó el default viejo, rotar la contraseña real del usuario `admin` directo en `/superadmin/`, no vía esta env var (ya no tiene efecto una vez que el superuser existe). | Cambiar el password del usuario en el admin, no en Render. |
| `EXTRA_DOMAINS` / `TENANT_DOMAINS` | No son secretos — no requieren rotación, solo actualización cuando cambian los dominios de los clientes. | — |

**Regla general:** ningún secreto de esta lista se commitea nunca a git (`.env` está en `.gitignore` desde antes de esta card, y `git log --all -- .env` confirma que nunca entró al historial). `.env.example` (nuevo, esta card) es la plantilla sin valores reales para desarrollo local.

---

## Método

Inventario construido rastreando en el código, no de memoria:

```bash
# Lecturas vía decouple (config())
grep -rn "config(" config/settings/*.py apps/ --include="*.py"

# Lecturas vía os.environ directo
grep -rn "os\.environ\.get\|os\.getenv" config/ apps/ --include="*.py"
```

Cruzado contra `render.yaml` (qué está declarado, aunque sea como `sync: false`) y contra el código real que consume cada variable (para clasificar sensibilidad y servicios que la necesitan, no asumir por el nombre).

**Fuera de alcance de esta card:** confirmar el estado real en el dashboard de Render (columna "¿Configurado en Render?" arriba) — requiere acceso que este documento no tiene. `#AUD-04` tiene el mismo cabo suelto pendiente para el resto de la config de Render.
