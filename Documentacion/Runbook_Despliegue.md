# Runbook de despliegue — rondas 3 a 16 a producción

> Creado 2026-11-22. Lleva producción (Render `saasmvp`, hoy en el commit de agosto `1a5d3e2`) a
> `main` con las rondas 3 a 16. Unas 2 h. Cierra `OPS-07`, `CONS-01` y `OPS-06`.
> Si algo falla en un paso marcado "detente", no sigas: guarda el error y revísalo antes.

**Antes de empezar, tres hechos:**

- `build.sh` corre `migrate` **durante el build**, contra el `DATABASE_URL` de Render: el Manual
  Deploy aplica las migraciones a producción solo. Por eso el ensayo en Neon va primero.
- `config/settings/development.py` fuerza SQLite e ignora `DATABASE_URL`. Para ensayar contra Neon
  desde el PC se usa `config.settings.production` con las variables que exige.
- La CI y el agente probaron las migraciones solo en SQLite. El ensayo de este runbook es la
  primera prueba en Postgres.

Migraciones nuevas desde agosto que importan: `tenants 0031` (árbol de temas, datos), `orders 0004`
y `tenants 0032` (borran `max_pages`, se pierden sus valores), `tenants 0033`–`0035` (`Client.plan`
pasa a FK de `Plan`; si falta el `Plan`, el cliente queda con `plan` en `null`).

## 0. Preparación (~15 min)

- [ ] PR de `agent/ronda16` mergeado a `develop` con CI verde, y `develop` → `main`.
- [ ] 2FA activo (`SEC-16`) en Neon, Cloudinary, Cloudflare, Zoho y GitHub.
- [ ] Render → `saasmvp`: **Auto-Deploy en Off**.
- [ ] En el PC: `git checkout main` y `git pull`.

## 1. Ramas de Neon (~5 min)

- [ ] Neon → proyecto → Branches → **Create branch** desde producción: `pre-deploy-2026-11`. Es el
      respaldo: no se toca.
- [ ] Otra rama desde producción: `ensayo-deploy`, para el ensayo.
- [ ] Copiar el connection string de `ensayo-deploy` (endpoint `-pooler`).

## 2. Ensayo de migraciones en `ensayo-deploy` (~20 min)

PowerShell, en el PC, sobre `main`. `SECRET_KEY` y `FIELD_ENCRYPTION_KEY` son los **reales** de
Render (hay datos cifrados); las de correo pueden ser de relleno.

```powershell
$env:DJANGO_SETTINGS_MODULE="config.settings.production"
$env:DATABASE_URL="<connection string de ensayo-deploy>"
$env:SECRET_KEY="<el de Render>"
$env:FIELD_ENCRYPTION_KEY="<el de Render>"
$env:EMAIL_HOST_USER="ensayo"; $env:EMAIL_HOST_PASSWORD="ensayo"
env\Scripts\python.exe manage.py showmigrations tenants orders
```

- [ ] Anotar en qué migración está cada app (se espera antes de `tenants 0031`).
- [ ] Comprobar los 3 `Plan`:
      ```powershell
      env\Scripts\python.exe manage.py shell -c "from apps.orders.models import Plan; print(list(Plan.objects.values_list('slug', flat=True)))"
      ```
      Si no salen `essential`, `pro` y `enterprise`: `env\Scripts\python.exe manage.py setup_plans`
      sobre `ensayo-deploy`. **Habrá que hacerlo también en producción** (paso 4).
- [ ] `env\Scripts\python.exe manage.py migrate` — sin error. **Si falla, detente.**
- [ ] Ningún cliente sin plan:
      ```powershell
      env\Scripts\python.exe manage.py shell -c "from apps.tenants.models import Client; print(list(Client.objects.values_list('slug', 'plan__slug')))"
      ```
      Ningún `None`. **Si hay alguno, detente.**
- [ ] `env\Scripts\python.exe manage.py check_tenant_setup <slug>` por cada tenant real. Que falle por
      SEO es esperable (`DEUDA-10` descartada: es el gate de QA); por base de datos, **detente**.
- [ ] `env\Scripts\python.exe manage.py check --deploy`.
- [ ] **Cerrar la terminal** para no dejar `DATABASE_URL` apuntando a Neon.

## 3. Ensayo visual (opcional, recomendado, ~20 min)

Si `saasmvp-staging` (del ensayo `OPS-07`) sigue existiendo:

- [ ] Su `DATABASE_URL` → `ensayo-deploy`; Build Command `./build.sh`; Manual Deploy de `main`.
- [ ] En el navegador: homes de andesscale, servelec y default; navbar a 375 px; footer, contacto y
      hero de Servelec; login; `/privacidad/`; subir una imagen.

## 4. Despliegue real (~15 min)

- [ ] Si en el paso 2 faltaban los `Plan`: nueva terminal con las variables del paso 2 pero el
      `DATABASE_URL` de **producción**, y `env\Scripts\python.exe manage.py setup_plans`. Funciona
      sobre el esquema actual (`Plan` ya existe en producción). Cerrar la terminal.
- [ ] Render → `saasmvp` → Settings → **Build Command**: `./build.sh`.
- [ ] **Health Check Path**: dejarlo como está por ahora (ver paso 5).
- [ ] **Manual Deploy** → "Deploy latest commit" de `main`.
- [ ] En el log: `[3/5]` (Tailwind) y `[4/5]` (migraciones) sin error, y `BUILD COMPLETADO`.

## 5. Verificación en vivo (~20 min)

- [ ] Cada sitio real carga **con estilos** (sin estilos = faltó `./build.sh`).
- [ ] Login de un tenant; login de un usuario de otro tenant rechazado.
- [ ] `/privacidad/` abre.
- [ ] Formulario de contacto con consentimiento: el mensaje aparece en el dashboard (el correo
      depende del cron del paso 6).
- [ ] Borrar un servicio y subir una imagen desde el dashboard.
- [ ] `/sitemap.xml` responde; `/sitemap-sections.xml` da 404 (`DEUDA-16`).
- [ ] Health check: `curl -I https://<dominio>/health/` → 200. Si es 200, cambiar el **Health Check
      Path** a `/health/`. **Riesgo sin verificar:** Render consulta el health check por dentro y
      `SECURE_SSL_REDIRECT=True` podría responderle 301 y marcar el servicio como no saludable. Si
      pasa, volver a `/`; el arreglo es `SECURE_REDIRECT_EXEMPT` para `/health/`.

## 6. Crons (`OPS-06`, ~15 min)

Render no sincroniza `render.yaml`: se crean a mano, ambos con el Environment Group `saasmvp-shared`.

- [ ] `contact-digest` — `python manage.py send_contact_digest` — `0 8 * * 1` (lunes 8:00). Corre
      también la purga de 365 días (`LEY-03`).
- [ ] `send-pending-emails` — `python manage.py send_pending_emails` — `*/5 * * * *`. Confirmar que el
      plan de Render admite intervalos de menos de una hora; luego volver a `EMAIL_ASYNC=true`.
- [ ] "Trigger Run" de cada uno una vez y revisar sus logs.

## 7. Cierre (~10 min)

- [ ] Borrar `saasmvp-staging` y las ramas de Neon `ensayo-deploy` y `staging-ensayo`.
      **Conservar `pre-deploy-2026-11` al menos una semana.**
- [ ] GitHub → Settings → Branches: protección en `main` y `develop` (exigir pull request).
- [ ] **No correr `audit_cloudinary_assets --fix`** sin antes revisar la lista en modo de prueba
      (`DEUDA-17` acotó las referencias y la purga podría borrar assets legacy).
- [ ] Kanban: producción en el commit nuevo; cerrar `OPS-07`, `CONS-01` y `OPS-06`.

## Si algo sale mal

- **Sitio caído tras el deploy:** Render → Events → **Rollback** al deploy anterior. El rollback del
  código **no** revierte la base de datos.
- **Base dañada:** `DATABASE_URL` de Render → `pre-deploy-2026-11` (endpoint `-pooler`) y rollback del
  código al deploy anterior. Detalle en [`Runbook_Incidentes.md`](Runbook_Incidentes.md).
