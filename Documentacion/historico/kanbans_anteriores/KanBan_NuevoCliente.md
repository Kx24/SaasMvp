# 📋 Planificación Kanban: Piloto Página "En Construcción" & Onboarding Base

Este tablero Kanban define el flujo de trabajo para implementar la página temporal "En construcción" para el primer cliente piloto, usándola como modelo funcional para el onboarding multi-tenant de **Andesscale**. Objetivo a corto plazo: publicar la página temporal, capturar leads, y sacar conclusiones del proceso para mejorar el onboarding real (pre-diseño final) de cada nuevo cliente.

> ⚠️ **Nota de alcance:** Este flujo es un onboarding *pre-pago / manual* (alta directa por el equipo). Es distinto del onboarding *post-pago* que ya existe en `apps/orders/` (`views_onboarding.py`, ruta `/onboarding/<uuid:token>/`), disparado automáticamente tras un pago con MercadoPago. No mezclar ambos flujos: este piloto no debe tocar `apps/orders`.

---

## 0. ✅ Housekeeping previo

* **[TASK-00] Separar el refactor de autenticación en curso** — **DONE**
  * El refactor de login/auth que estaba mezclado en esta rama se movió a `feature/Mejora_Login`. `feature/landing-en-construccion` parte limpia desde `develop`.

  ---

  ## 1. 📥 BACKLOG

  * **[EP-01] Definición del Modelo de Registro Piloto** — **DONE**
    * El modelo real es **`Client`** (`apps/tenants/models.py`), no `Tenant`. Ya tenía `name`, `slug`, `contact_email`, `contact_phone`, `is_active`.
      * El dominio/subdominio se gestiona con el modelo `Domain` (relación 1-N vía `client.domains`), no como campo del `Client`.

      ---

      ## 2. 📝 TO DO

      * **[TASK-01] Preparación del Entorno Git** — **DONE**

      * **[TASK-02] Campo `mode_under_construction` en `Client`** — **DONE**
        * Agregado `mode_under_construction = models.BooleanField(default=False)` en `apps/tenants/models.py` + migración `0015_client_mode_under_construction_alter_client_template.py`.
          * Expuesto en el admin (`apps/tenants/admin.py`): agregado a `fieldsets` (grupo "Estado"), `list_display` y `list_filter` de `ClientAdmin` — sin esto no aparecía en `superadmin/tenants/client/add/`.

          * **[TASK-03] Interceptar el modo construcción antes del render normal** — **DONE**
            * Resuelto en `TenantMiddleware.__call__` (`apps/tenants/middleware.py`): si `client.mode_under_construction` es `True`, sirve `errors/under_construction.html` para cualquier ruta del tenant.
              * Bypass explícito para `/dashboard`, `/auth`, `/superadmin` y `/contact` — así el cliente puede loguearse y administrar su sitio, y el propio formulario de leads de la landing temporal (POST a `/contact/submit/`) sigue funcionando.

              ---

              ## 3. 🚧 IN PROGRESS

              * **[TASK-04] Template "En Construcción"** — **DONE**
                * `templates/errors/under_construction.html`, clonado del patrón de `templates/errors/payment_required.html` (antes huérfana, sin uso).
                  * Logo del cliente, mensaje "Próximamente...", formulario de leads reutilizando `ContactForm`/`ContactSubmission` (honeypot + rate limiting ya incluidos).

                  * **[TASK-05] Alta del cliente piloto vía comando existente** — **DONE**
                    * `provision_tenant` extendido con `--under-construction` para setear la bandera al crear el `Client`.
                      * **Extensión adicional (branding reutilizable):** el comando ahora también acepta `--logo`, `--phone`, `--address`, `--tagline`, `--facebook`, `--instagram`, `--twitter`, `--linkedin`, `--youtube`, `--whatsapp`. El logo se sube a Cloudinary automáticamente (mismo patrón que usan las vistas del dashboard) y el resto se guarda en `ClientSettings`. Permite dar de alta un cliente piloto completo — datos + branding — en un solo comando:
                          ```bash
                              python manage.py provision_tenant mi-empresa \
                                    --template=servicios_profesionales --domain=miempresa.com \
                                          --logo=/ruta/local/logo.png --phone="+56912345678" \
                                                --facebook=https://facebook.com/miempresa --whatsapp=56912345678 \
                                                      --under-construction
                                                          ```
                                                            * Alternativa manual probada: alta directa desde `superadmin/tenants/client/add/` (con el fix de TASK-02, el campo `mode_under_construction` y todos los de branding ya están disponibles en el formulario del admin).

                                                            * **[TASK-05b] Limpieza de código muerto** — **DONE**
                                                              * Eliminadas `HomeView`/`ContactView` en `apps/website/views.py` (código no enrutado, con un `render(request, '...', ...)` roto) y el import `View` no usado. La vista real de home es la función `home()`.

                                                              ---

                                                              ## 4. 🧪 TESTING & QA

                                                              * **[TASK-06] Pruebas de Multi-Tenancy y Formulario**
                                                                * Verificado con un tenant de prueba (creado y eliminado en la sesión de desarrollo): `mode_under_construction=True` sirve la landing temporal (200, con el form de leads); `/dashboard` sigue redirigiendo a login en vez de mostrar la landing; al desactivar la bandera, el sitio vuelve a la normalidad.
                                                                  * Pendiente: repetir en Staging vía subdominio real, y confirmar aislamiento con un segundo tenant activo en paralelo.

                                                                  * **[TASK-07] Code Review y Integración**
                                                                    * PR de `feature/landing-en-construccion` → `develop` (solo con el trabajo de esta feature).
                                                                      * Ejecutar `python manage.py test_isolation` antes del PR.
                                                                        * Validar en Staging.

                                                                        ---

                                                                        ## 5. 🚀 DONE

                                                                        * **[TASK-08] Despliegue a Producción y Publicación Final**
                                                                          * PR de `develop` → `main` (dispara auto-deploy en Render).
                                                                            * Provisionar el tenant real en producción con `provision_tenant --settings=config.settings.production`.
                                                                              * Verificación en vivo del subdominio/dominio final del primer cliente.

                                                                              ---

                                                                              ## 📝 Conclusiones / Hallazgos para el próximo onboarding

                                                                              * **Bug de encoding en management commands (Windows):** `apps/tenants/signals.py` y `provision_tenant.py` usaban `print()`/`self.stdout.write()` con emojis, lo que lanzaba `UnicodeEncodeError` y **abortaba toda la transacción de creación del `Client`** en una consola Windows sin `PYTHONIOENCODING=utf-8` (cp1252 por defecto). Corregido en ambos archivos. **Pendiente:** el mismo patrón existe en otros 9 management commands (`create_tenant.py`, `list_tenants.py`, `test_isolation.py`, `update_domain.py`, `send_contact_digest.py`, `setup_cloudinary_folders.py`, `setup_dev_env.py`, `setup_production.py`, `verify_search_console.py`) — no se tocaron por estar fuera del alcance de esta feature, pero vale la pena una pasada dedicada antes de que alguien los use en Windows.

                                                                              * **Inconsistencia `--template` vs `Client.template` en `provision_tenant`:** el flag `--template` de `provision_tenant` se usa para dos cosas distintas que no siempre coinciden:
                                                                                1. Selecciona el **contenido de industria** (`TEMPLATE_CONFIGS`: `electricidad`, `construccion`, `servicios_profesionales`, `portafolio`) — colores y servicios iniciales.
                                                                                  2. Se guarda tal cual en `Client.template`, que es el campo que decide la **carpeta visual** vía `TenantTemplateLoader` (valores válidos: `THEME_CHOICES` = `themes/default`, `servelec`, `themes/industrial`).

                                                                                    Si se usa un valor de industria que no está en `THEME_CHOICES` (ej. `servicios_profesionales`), el contenido/colores se aplican bien, pero el tema visual no matchea ningún folder real y el `TenantTemplateLoader` cae a un fallback poco predecible (`templates/default/...` en vez de `templates/themes/default/...`). No se corrigió en esta pasada — recomendado separar ambos conceptos en dos flags (`--industry` para contenido, `--theme` para carpeta visual) antes del próximo onboarding real.

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
