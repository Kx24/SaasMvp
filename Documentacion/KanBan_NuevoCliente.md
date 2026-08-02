# 📋 Planificación Kanban: Piloto Página "En Construcción" & Onboarding Base

Este tablero Kanban define el flujo de trabajo para implementar la página temporal "En construcción" para el primer cliente piloto, usándola como modelo funcional para el onboarding multi-tenant de **Andesscale**. Objetivo a corto plazo: publicar la página temporal, capturar leads, y sacar conclusiones del proceso para mejorar el onboarding real (pre-diseño final) de cada nuevo cliente.

> ⚠️ **Nota de alcance:** Este flujo es un onboarding *pre-pago / manual* (alta directa por el equipo). Es distinto del onboarding *post-pago* que ya existe en `apps/orders/` (`views_onboarding.py`, ruta `/onboarding/<uuid:token>/`), disparado automáticamente tras un pago con MercadoPago. No mezclar ambos flujos: este piloto no debe tocar `apps/orders`.

---

## 0. ⚠️ Housekeeping previo (bloqueante)

* **[TASK-00] Separar el refactor de autenticación en curso**
  * La rama `feature/landing-en-construccion` tiene cambios sin commitear ajenos a esta feature: unificación de login en `apps/accounts` (retiro de `apps.website.auth_urls`), y edits en `config/urls.py`, `config/settings/base.py`, navbars de `andesscale`/`servelec` y `login_modal.html`.
  * Antes de empezar TASK-01, commitear ese trabajo por separado (o moverlo a su propia rama) para no mezclar el historial de "auth" con el de "landing en construcción".

---

## 1. 📥 BACKLOG

* **[EP-01] Definición del Modelo de Registro Piloto**
  * El modelo real se llama **`Client`** (`apps/tenants/models.py`), no `Tenant`. Ya existen los campos necesarios para el alta básica: `name`, `slug`, `contact_email`, `contact_phone`, `is_active`.
  * Definir únicamente los campos **nuevos** que faltan: bandera de conmutación `mode_under_construction` (Boolean) y, opcionalmente, `expected_launch_date` para mostrar en la landing.
  * El dominio/subdominio no es un campo del `Client`: se gestiona en el modelo `Domain` (relación 1-N vía `client.domains`). Reutilizar ese modelo, no crear uno nuevo.

---

## 2. 📝 TO DO

* **[TASK-01] Preparación del Entorno Git**
  * Confirmar que `feature/landing-en-construccion` parte limpia de `develop` (ver TASK-00).

* **[TASK-02] Campo `mode_under_construction` en `Client`**
  * Agregar `mode_under_construction = models.BooleanField(default=False)` al modelo `Client` en `apps/tenants/models.py` + migración.
  * No duplicar `is_active` (ya existe y controla si el tenant responde en absoluto — ver `TenantMiddleware._detect_tenant`). `mode_under_construction` es un estado *dentro* de un tenant activo, no un reemplazo de `is_active`.

* **[TASK-03] Interceptar el modo construcción antes del render normal**
  * El punto de intercepción natural es la vista `home()` en `apps/website/views.py:64` (es la vista real conectada en `apps/website/urls.py`; **no** usar como referencia la clase `HomeView` más abajo en el mismo archivo — es código muerto/roto, con un `render(request, '...', ...)` placeholder sin terminar; limpiar esa clase junto con `ContactView` de paso).
  * Alternativa más limpia: chequear `request.client.mode_under_construction` dentro de `TenantMiddleware.__call__` (`apps/tenants/middleware.py`), justo después de resolver `client`, y devolver ahí la vista temporal — así cualquier ruta del tenant (no solo home) queda cubierta sin tocar cada view.

---

## 3. 🚧 IN PROGRESS

* **[TASK-04] Template "En Construcción" (reutilizar patrón existente)**
  * Ya existe una plantilla huérfana con exactamente este patrón: `templates/errors/payment_required.html` (branding del cliente, mensaje central, datos de contacto — actualmente no está enlazada desde ningún view). Clonarla como base para `templates/errors/under_construction.html` en lugar de diseñar desde cero.
  * Incluir: logo del cliente (`client.settings.get_logo_url()`), título, mensaje personalizable ("*Próximamente...*"), y formulario de captura de leads.
  * Para el formulario de leads, evaluar reutilizar `ContactForm` + `ContactSubmission` de `apps/website/models.py` (ya filtran por tenant vía `TenantAwareManager`) en lugar de crear un modelo de leads nuevo.

* **[TASK-05] Alta del cliente piloto vía comando existente**
  * Ya existe `python manage.py provision_tenant <slug> --template=<...> --domain=<...> --email=<...>` (`apps/tenants/management/commands/provision_tenant.py`), que crea `Client` + `Domain` + `ClientSettings` + contenido inicial en un solo paso.
  * En lugar de un procedimiento 100% manual, extender este comando con un flag `--under-construction` que setee `mode_under_construction=True` al crear el `Client`. Documentar el procedimiento resultante:
    1. `provision_tenant <slug> --domain=cliente.andesscale.com --under-construction`
    2. Verificar `Domain` creado y activo.
    3. Confirmar que el subdominio sirve la vista temporal (TASK-03).
    4. Cuando el sitio esté listo: desactivar la bandera (vía admin o `update_domain`/nuevo comando `toggle_construction_mode`).

---

## 4. 🧪 TESTING & QA

* **[TASK-06] Pruebas de Multi-Tenancy y Formulario**
  * Probar vía `?tenant=<slug>` en dev (atajo ya soportado por `TenantMiddleware` cuando `DEBUG=True`) y vía subdominio real en staging.
  * Verificar aislamiento: un segundo tenant sin `mode_under_construction` debe seguir viendo su home normal sin cambios.
  * Validar guardado del formulario de contacto/leads y notificación (si se reutiliza `ContactForm`, ya dispara el flujo de `ClientEmailSettings`).

* **[TASK-07] Code Review y Integración**
  * PR de `feature/landing-en-construccion` → `develop` (solo con el trabajo de esta feature, ver TASK-00).
  * Ejecutar `python manage.py test_isolation` (comando ya existente) antes del PR para confirmar que no se rompió el aislamiento entre tenants.
  * Validar en Staging.

---

## 5. 🚀 DONE

* **[TASK-08] Despliegue a Producción y Publicación Final**
  * PR de `develop` → `main` (dispara auto-deploy en Render).
  * Provisionar el tenant real en producción con `provision_tenant --settings=config.settings.production`.
  * Verificación en vivo del subdominio/dominio final del primer cliente.

---

## Rama Github (referencia)

```bash
# 1. Rama de desarrollo
git checkout develop
git pull origin develop

# 2. Desarrollo particular de este feature
git checkout -b feature/landing-en-construccion

# 3. Push inicial
git push -u origin feature/landing-en-construccion
```
