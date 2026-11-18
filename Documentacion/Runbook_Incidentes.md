# Runbook de incidentes (`SEC-15`)

Para una persona sola, de madrugada. Léelo de arriba abajo la primera vez; después ve directo a tu caso.
Qué es cada variable y cuándo/cómo rotarla: [`Inventario_Secretos.md`](Inventario_Secretos.md) (§ "Política de rotación"). Controles y hallazgos abiertos: [`SEGURIDAD.md`](SEGURIDAD.md). Servicios: [`ARQUITECTURA.md`](ARQUITECTURA.md).

> **Regla:** no pegues valores reales de claves en este documento, en el kanban, en commits ni en chats. Se guardan solo en el dashboard del servicio correspondiente.

---

## 1. Primeros 15 minutos (cualquier incidente)

1. **Anota la hora** y qué viste (captura, mensaje de error, quién avisó). Empieza el registro de la sección 5 aunque sea en borrador.
2. **Contén primero, investiga después.** Lo más rápido y reversible: rotar la credencial, cerrar sesiones, suspender la cuenta o desactivar el servicio afectado.
3. **No borres evidencia:** no elimines logs, commits, correos ni filas de la base; no reinicies servicios "a ver si se arregla" antes de copiar el log de Render. Si hay que ocultar algo (un commit con una clave), primero rota la clave; reescribir el historial es secundario.
4. **Haz capturas** de lo que ya ves (logs de Render, panel de Neon, mensajes).
5. **Decide el tipo** (sección 2) y sigue su receta. Si no sabes cuál es, contén como si fuera fuga de secreto (2a).

---

## 2. Por tipo de incidente

### 2a. Fuga de un secreto (clave en un commit, captura, correo, chat)

**Señales:** una clave aparece en git (`git log -p`), en un PR, una captura compartida o un correo; uso anómalo en el panel de Cloudinary/MercadoPago/Zoho; avisos de GitHub de secret scanning.

**Contener:** rota **solo lo filtrado** — y de inmediato, aunque sea de madrugada; la clave filtrada se considera comprometida desde que salió. Si no sabes qué se filtró, rota en este orden (de mayor a menor daño posible):

| Orden | Variable | Qué se rompe al rotar | Cómo |
|---|---|---|---|
| 1 | `DATABASE_URL` | Corte breve entre el reset y el redeploy | Resetear la password del rol en Neon, pegar el connection string nuevo (endpoint `-pooler`) en Render, redeploy |
| 2 | `SECRET_KEY` | **Todas** las sesiones activas (incluido tú en `/superadmin/`) y tokens firmados en tránsito (enlaces de set-password pendientes) | Generar una nueva, setear en Render, redeploy |
| 3 | `FIELD_ENCRYPTION_KEY` | Nada si se hace bien; si **pierdes** la clave vieja, las credenciales SMTP/API de `ClientEmailSettings` quedan ilegibles | Anteponer la nueva (`NUEVA,VIEJA`), redeploy, re-guardar cada `ClientEmailSettings`, recién ahí quitar la vieja. Guardar copia fuera de Render |
| 4 | `EMAIL_HOST_PASSWORD` (+ `EMAIL_HOST_USER`) | Ningún correo sale hasta actualizar Render; sin downtime del sitio | Cambiar en Zoho, actualizar Render |
| 5 | `CLOUDINARY_API_SECRET` (+ `CLOUDINARY_API_KEY`) | Las subidas de media fallan entre el cambio y el redeploy | Regenerar en Cloudinary, actualizar Render, redeploy |
| 6 | `MP_ACCESS_TOKEN` / `MP_WEBHOOK_SECRET` | Cobros y webhooks. `MP_WEBHOOK_SECRET`: cambiar **primero** en el panel de MP, luego en Render (si no, los webhooks responden 401 hasta que MP reintente). Hoy el checkout está pospuesto (no configuradas en Render) | Ver `Inventario_Secretos.md` |
| 7 | Token de GitHub (PAT, secretos de Actions si los hubiera) | Push/CI desde ese token | Revocar en GitHub → Settings → Developer settings, crear uno nuevo con el mínimo de scopes |

Además: si la clave está en un commit, revocarla basta; reescribir el historial no recupera una clave ya copiada. Revisa `.env` en `git log --all -- .env` (nunca debió entrar).

**Recuperar:** confirma que el sitio carga, que se puede iniciar sesión, que sale un correo de prueba y que la subida de una imagen funciona. Anota qué se rotó y a qué hora. Revisa en los servicios si hubo uso de la clave filtrada (logs de Neon, uso de Cloudinary, bandeja de Zoho).

### 2b. Acceso indebido a un tenant o a `/superadmin/`

**Señales:** cambios de contenido que nadie hizo; logins desconocidos; correos de contacto/dashboard alterados; usuarios staff que no reconoces; ráfaga de 401/403 o de intentos en el log. Nota: `/superadmin/` aún no tiene segundo factor ni rate limit propio (`SEC-13`, abierto).

**Contener:**
1. Cambiar la contraseña de la cuenta afectada (en `/superadmin/` o con `python manage.py changepassword <usuario>` desde la shell de Render).
2. Desactivar (`is_active=False`) cuentas staff/usuarios sospechosos; revisar en el admin quién tiene `is_staff`/`is_superuser`.
3. **Cerrar todas las sesiones:** borrar `django.contrib.sessions.models.Session` (shell: `Session.objects.all().delete()`), o rotar `SECRET_KEY` (2a) si hay sospecha de cookie robada. Esto desconecta a todos los clientes: avisa.
4. Si el acceso vino por una contraseña filtrada o reutilizada, pide al cliente cambiarla.
5. Si un tenant ve datos de otro: es un bug de aislamiento, no solo un acceso — captura la URL y el usuario, y corre `python manage.py test apps.tenants.tests_isolation` contra el código desplegado.

**Recuperar:** revisar y revertir los cambios hechos (galería, secciones, servicios, marca) desde el dashboard o el admin; comprobar `ClientSettings` y destinos de los correos de contacto; avisar al cliente afectado. Cuando exista `SEC-13`, activar el segundo factor para staff.

### 2c. Base de datos dañada o borrada

> **Importante:** `DB-02` (backup con restore probado) **aún está pendiente**. Hoy no hay un restore probado ni tiempos medidos; lo que sigue es lo que ofrece Neon, sin garantía verificada.

**Señales:** errores 500 masivos con excepciones de BD; tablas o filas faltantes; migración mal aplicada; el panel de Neon muestra el proyecto o la rama eliminados.

**Contener:**
1. Pon el sitio en pausa si se siguen escribiendo datos malos (suspender el servicio web en Render) para no pisar el punto de recuperación.
2. **No ejecutes más migraciones ni comandos de datos** hasta entender qué pasó.
3. En el panel de Neon, usa el historial de restauración (restore a un instante anterior) **hacia una rama nueva**, no sobre la rama de producción: así se compara antes de reemplazar.

**Recuperar:**
1. Verifica en la rama restaurada que los datos esperados están (tenants, `Domain`, usuarios, pedidos).
2. Apunta `DATABASE_URL` de Render a la rama restaurada (endpoint `-pooler`) y redeploy; o restaura sobre la rama principal si Neon lo permite y ya validaste.
3. Anota cuánto se perdió (ventana entre el punto de restauración y el incidente) y qué hay que reingresar. Cuando se cierre `DB-02`, reemplaza esta sección con los pasos y tiempos medidos.

### 2d. Sitio caído tras un deploy

**Señales:** 500/502/503 justo después de un deploy; el build falla en Render; el servicio no arranca.

**Contener / recuperar:**
1. Render → servicio web → **Events/Deploys**: abre el deploy fallido y lee el **log del build** y luego el log de runtime. Cópialo antes de seguir.
2. **Volver al deploy anterior:** en la lista de deploys, elegir el último que funcionó y usar **Rollback** (redeploy de ese commit). Es el camino más rápido; investiga después.
3. Causas frecuentes (ver `CLAUDE.md` → Gotchas): `production.py` falla al importar si faltan `SECRET_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` o `FIELD_ENCRYPTION_KEY`; `setup_production` falla si falta `DJANGO_SUPERUSER_PASSWORD`; el Build Command debe ser `./build.sh`; una migración fallida a medias.
4. Si el rollback de código no basta porque la migración ya corrió, no reviertas la base a ciegas: ve a 2c.
5. Verifica el dominio principal y un tenant de cliente tras el rollback.

### 2e. Correo o dominio comprometido (Zoho, DNS)

**Señales:** correos enviados que nadie escribió; rebotes inesperados; el dominio apunta a otra IP o muestra otro sitio; registros DNS cambiados; avisos de Zoho o del registrador.

**Contener:**
1. **Zoho:** cambiar la contraseña de la casilla, cerrar sesiones activas, revisar reglas de reenvío y filtros (un atacante suele dejar un reenvío), activar segundo factor. Luego actualizar `EMAIL_HOST_PASSWORD` en Render (2a).
2. **DNS/registrador:** cambiar la contraseña de la cuenta del registrador/DNS, activar segundo factor, revisar los registros (A/CNAME hacia Render, MX/SPF/DKIM/DMARC de Zoho) contra la copia en `Procedimiento_Nuevo_Tenant.md` (checklist de custodia DNS) y restaurar los valores correctos.
3. Si el dominio de un cliente está afectado, avísale: la custodia del DNS suele ser suya.

**Recuperar:** envía un correo de prueba y comprueba que llega; revisa SPF/DKIM/DMARC; verifica que los enlaces de correos (`BASE_URL`) siguen apuntando al dominio correcto; pide el reinicio de la reputación del remitente si hubo spam.

---

## 3. Datos personales

Si el incidente expuso o pudo exponer datos personales (mensajes de contacto, correos de clientes, datos de pedidos), además de contener, **anota qué datos, de qué tenants y cuántos titulares aproximadamente**: servirá cuando exista el procedimiento formal.

- El procedimiento de brechas (Ley 21.719, art. 14 sexies) es `LEY-06`: **pendiente**, previsto para 2027 (la ley rige desde el 15-oct-2027). Este runbook no fija plazos ni obligaciones de reporte; cuando `LEY-06` exista, se enlaza aquí.
- Para atender solicitudes de titulares (exportar, suprimir, bloquear) ya existe el comando `data_subject`: procedimiento en [`SEGURIDAD.md`](SEGURIDAD.md) → "Atender una solicitud de derechos".
- Marco legal y estado de cada artículo: `SEGURIDAD.md` §3.

---

## 4. Contactos y cuentas

Solo nombres de servicios y dónde mirar. Sin contraseñas, claves ni correos personales.

| Servicio | Para qué | Dónde mirar |
|---|---|---|
| Render | Hosting web, deploys, variables de entorno, logs | Dashboard → servicio web → Events, Logs, Environment |
| Neon | Base de datos Postgres (ramas, restauración) | Consola → proyecto → Branches, Restore |
| Cloudinary | Media de los tenants | Dashboard → Settings → API Keys; Reports (uso) |
| Zoho Mail | Correo saliente/entrante | Consola de administración → Seguridad, Reglas de reenvío |
| Registrador / DNS | Dominios de la plataforma (y de clientes que delegaron) | Panel del registrador; checklist de custodia en `Procedimiento_Nuevo_Tenant.md` |
| MercadoPago | Pagos y webhooks (checkout pospuesto) | Panel de desarrolladores → Credenciales, Webhooks |
| GitHub | Código, CI, tokens | Repo → Settings → Security; cuenta → Developer settings |

Las cuentas y accesos viven en el gestor de contraseñas del dueño, no en el repo.

---

## 5. Después del incidente

1. Confirma que todo lo rotado quedó en Render y que `Inventario_Secretos.md` sigue siendo cierto.
2. Si el incidente mostró un hueco (control que faltaba, paso confuso de este runbook), abre una card en `KANBAN_PROYECTO.md` y corrige el runbook.
3. Llena una fila:

| Fecha | Tipo (2a–2e) | Causa | Qué se hizo | Qué se rotó/restauró | Pendiente |
|---|---|---|---|---|---|
| | | | | | |
