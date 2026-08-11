# 📋 Kanban: Onboarding Rancho Cachimba (`ranchocachimba.cl`) — 2º Tenant Real

Este tablero cubre el alta del **segundo cliente real** de la plataforma. Sigue el patrón de `[[KanBan_NuevoCliente.md]]` (piloto "En Construcción", ya en `main`/producción con Servelec): publicar primero una landing temporal para capturar leads mientras se construye el sitio definitivo.

Este documento es una **instancia** del procedimiento general — el runbook completo (con todos los pasos, comandos y follow-ups manuales) vive en `[[Procedimiento_Nuevo_Tenant.md]]`. Acá solo se trackea el estado específico de este cliente.

> **Estado (actualizado 2026-08-10, rama `feature/mejorar-provisioning-tenant`):**
> - Producción ya sirve `servelec-ingenieria.cl` con sitio completo (tema `servelec`).
> - El `Client` `ranchocachimba` **ya existe en dev** (creado 2026-08-03, `mode_under_construction=True`, tema `themes/default`, dominio dev ya actualizado a `ranchocachimba.cl` con `update_domain`).
> - `render.yaml` tiene `ranchocachimba.cl,www.ranchocachimba.cl` agregado a `EXTRA_DOMAINS` (pendiente de commitear/pushear junto con el resto de esta rama).
> - Se auditó y corrigió el proceso de provisioning completo en esta misma rama (ver `[[Procedimiento_Nuevo_Tenant.md]]` para el detalle): el bug de fondo que obligaba a arreglar `client.template` a mano ya no existe — `provision_tenant` ahora valida `--theme` contra `Client.THEME_CHOICES` directamente. `list_tenants`/`update_domain` (rotos, referenciaban un campo `Client.domain` inexistente) y el crash de encoding en Windows también quedaron resueltos.

---

## 1. 📥 BACKLOG

* **[RC-01] Definir tema visual real para Rancho Cachimba**
  * No es rubro eléctrico → no corresponde reusar `servelec` como carpeta final. Por ahora se puede lanzar con `themes/default` (genérico) en modo construcción, y decidir después si se crea una carpeta de tema dedicada (`templates/rancho-cachimba/` o un nuevo tema reutilizable tipo `themes/rural`) antes de desactivar `mode_under_construction`.
* **[RC-02] Confirmar propietario y acceso DNS del dominio `ranchocachimba.cl`**
  * Necesario para el paso de CNAME hacia Render más adelante (no bloquea el trabajo en dev).
* **[RC-03] Reunir branding inicial** (logo, teléfono, redes sociales, tagline) para pasar como flags a `provision_tenant` o cargar después vía admin/dashboard.

---

## 2. 📝 TO DO

* **[RC-04] Commitear el cambio en `render.yaml`**
  * Ya está editado localmente (`EXTRA_DOMAINS` incluye `ranchocachimba.cl,www.ranchocachimba.cl`) pero no está en un commit. Confirmar que va en la rama de esta feature, no suelto en `main`.
* **[RC-05] Crear rama de trabajo**
  ```bash
  git checkout develop
  git pull origin develop
  git checkout -b feature/onboarding-rancho-cachimba
  ```
* **[RC-06] Provisionar el tenant en DEV local** — **DONE** (ya existe, creado 2026-08-03; ver estado arriba)
  ```bash
  python manage.py provision_tenant ranchocachimba \
    --industry=servicios_profesionales --theme=themes/default \
    --under-construction \
    --settings=config.settings.development
  # (usar --logo/--phone/--facebook/--whatsapp/etc. si ya se cuenta con el branding de RC-03)
  ```
  * Sin `--domain` en dev: se accede vía `http://localhost:8000/?tenant=ranchocachimba`.
* **[RC-07] Verificar el provisioning con `check_tenant_setup`** — reemplaza el workaround manual que este documento pedía antes (ya no hace falta corregir `client.template` a mano: `--theme` valida directo).
  ```bash
  python manage.py check_tenant_setup ranchocachimba --settings=config.settings.development
  ```
  * Esperado hoy: `[OK]` en tema y dominio, `[WARN]` en email/SEO (son los pasos manuales de la sección 2 del runbook, todavía pendientes para este cliente).

---

## 3. 🚧 IN PROGRESS

* **[RC-08] Validar la landing "En Construcción" localmente**
  * `http://localhost:8000/?tenant=ranchocachimba` → debe verse el logo/branding cargado, mensaje "Próximamente...", y el formulario de leads funcionando (POST a `/contact/submit/`).
  * `http://localhost:8000/dashboard/?tenant=ranchocachimba` → debe seguir accesible pese al modo construcción (bypass del middleware).
* **[RC-09] Cargar branding pendiente vía dashboard o admin**
  * Cualquier dato no pasado por flags en RC-06 (logo, contacto, redes) se completa acá.

---

## 4. 🧪 TESTING & QA

* **[RC-10] Test de aislamiento multi-tenant**
  ```bash
  python manage.py test_isolation --settings=config.settings.development
  ```
  * Confirmar que `servelec` (o el tenant de dev que simule producción) y `ranchocachimba` conviven sin fuga de datos.
  * (Ya no hace falta `$env:PYTHONIOENCODING` a mano — `manage.py` fuerza UTF-8 para todos los commands.)
* **[RC-11] Revisión de código y PR**
  * PR de `feature/onboarding-rancho-cachimba` → `develop`.
  * Confirmar que `render.yaml` quedó correcto y que no se tocó nada de `apps/orders/` (onboarding post-pago, fuera de alcance — mismo criterio que el piloto anterior).

---

## 5. 🚀 DEPLOY A PRODUCCIÓN

* **[RC-12] PR `develop` → `main`** (dispara auto-deploy en Render).
* **[RC-13] Provisionar el tenant en producción**
  ```bash
  python manage.py provision_tenant ranchocachimba \
    --industry=servicios_profesionales --theme=themes/default \
    --domain=ranchocachimba.cl \
    --under-construction \
    --settings=config.settings.production
  ```
  * `check_tenant_setup ranchocachimba --settings=config.settings.production` debe salir `[OK]` en tema y dominio de entrada — ya no requiere corrección manual.
* **[RC-14] Configurar dominio en Render**
  * Render → Settings → Custom Domains → agregar `ranchocachimba.cl` y `www.ranchocachimba.cl`.
  * En el proveedor DNS del cliente: `CNAME @ → <servicio>.onrender.com` (o el registro que Render indique).
  * Confirmar que `EXTRA_DOMAINS` (ya actualizado en `render.yaml`, RC-04) llegó a producción con el deploy.
* **[RC-15] Verificación en vivo**
  * `https://ranchocachimba.cl` → debe mostrar la landing "En construcción", no un 404 ni el fallback genérico.
  * Confirmar que `servelec-ingenieria.cl` sigue funcionando normalmente en paralelo (sin regresión).
  * `python manage.py check_tenant_setup ranchocachimba --settings=config.settings.production` como cierre.

---

## 6. 📌 Fuera de alcance de este tablero (para cuando el sitio definitivo esté listo)

* Definir/crear el tema visual final (si no se queda en `themes/default`).
* Cargar contenido real de secciones y servicios (reemplazar el seed genérico de `provision_tenant`).
* Desactivar `mode_under_construction` cuando el sitio esté aprobado por el cliente.
* Verificación de Google Search Console (`python manage.py verify_search_console --domain ranchocachimba.cl`).
