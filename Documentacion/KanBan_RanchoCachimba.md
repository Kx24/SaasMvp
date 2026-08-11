# 📋 Kanban: Onboarding Rancho Cachimba (`ranchocachimba.cl`) — 2º Tenant Real

Este tablero cubre el alta del **segundo cliente real** de la plataforma. Sigue el patrón de `[[KanBan_NuevoCliente.md]]` (piloto "En Construcción", ya en `main`/producción con Servelec): publicar primero una landing temporal para capturar leads mientras se construye el sitio definitivo.

Este documento es una **instancia** del procedimiento general — el runbook completo (con todos los pasos, comandos y follow-ups manuales) vive en `[[Procedimiento_Nuevo_Tenant.md]]`. Acá solo se trackea el estado específico de este cliente.

> **Estado (actualizado 2026-08-10, rama `feature/mejorar-provisioning-tenant`):**
> - Producción ya sirve `servelec-ingenieria.cl` con sitio completo (tema `servelec`).
> - El `Client` `ranchocachimba` **ya existe en dev** (creado 2026-08-03, `mode_under_construction=True`, tema `themes/default`, dominio dev ya actualizado a `ranchocachimba.cl` con `update_domain`).
> - `render.yaml` tiene `ranchocachimba.cl,www.ranchocachimba.cl` agregado a `EXTRA_DOMAINS` (pendiente de commitear/pushear junto con el resto de esta rama).
> - Se auditó y corrigió el proceso de provisioning completo en esta misma rama (ver `[[Procedimiento_Nuevo_Tenant.md]]` para el detalle): el bug de fondo que obligaba a arreglar `client.template` a mano ya no existe — `provision_tenant` ahora valida `--theme` contra `Client.THEME_CHOICES` directamente. `list_tenants`/`update_domain` (rotos, referenciaban un campo `Client.domain` inexistente) y el crash de encoding en Windows también quedaron resueltos.

---

# 🛠️ Parte 1: Onboarding y hardening del proceso de provisioning

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

## 6. 📌 Fuera de alcance de esta parte (para cuando el sitio definitivo esté listo)

* Cargar contenido real de secciones y servicios (reemplazar el seed genérico de `provision_tenant`).
* Desactivar `mode_under_construction` cuando el sitio esté aprobado por el cliente.
* Verificación de Google Search Console (`python manage.py verify_search_console --domain ranchocachimba.cl`).

---

# 🎨 Parte 2: Estructura de carpetas — theme dedicado

> **Estado: DONE (ejecutado 2026-08-10).** `ranchocachimba` ya no usa `templates/themes/default/` — tiene su propia carpeta `templates/ranchocachimba/` + `static/js/clients/ranchocachimba/`, clonada de `servelec` y con el branding/texto heredado neutralizado. Verificado con `check_tenant_setup` y una carga real en `localhost` (sin errores, sin `electricCanvas` ni menciones de Servelec/electricidad visibles). `Client.template` ya apunta a `'ranchocachimba'` y `THEME_CHOICES` lo incluye. `mode_under_construction` se dejó de nuevo en `True` — el theme está listo pero la landing pública sigue siendo "En construcción" hasta que el diseño esté terminado.

Hoy `ranchocachimba` usa una carpeta propia (`templates/ranchocachimba/`), clonada estructuralmente de `servelec`. El objetivo de esta parte fue clonar la **estructura de carpetas** de un theme real hacia `templates/ranchocachimba/`, dejando el andamiaje Django/HTML listo y "vacío" — de ahí en adelante el trabajo restante es 100% diseño (colores, textos, imágenes), sin tocar Python.

No implicó escribir el diseño final — solo dejar la carpeta con la misma forma que un theme real, lista para rellenar. Todo texto/color heredado de Servelec que no se pudo generalizar automáticamente quedó marcado explícitamente como `PLACEHOLDER` / "pendiente de redacción" en el código (`cta.html`, `why_us.html`, `canvas_hero.js`), para que quien haga el diseño sepa exactamente qué reemplazar.

## 0. Qué existe hoy (verificado en código)

Cada theme "propio" (no `themes/default`) tiene **dos partes**, no solo `templates/`:

| Parte | Ejemplo (`servelec`) | Contenido |
|---|---|---|
| Templates | `templates/servelec/` | `base.html`, `components/*.html`, `landing/home.html` |
| JS específico | `static/js/clients/servelec/` | Canvas/efectos del hero (`canvas_electric.js`) |

`templates/servelec/base.html` extiende el `templates/base.html` global, que define los blocks que cualquier theme puede/debe usar: `extra_seo`, `favicon`, `theme_styles`, `navbar`, `content` (lo llena `landing/home.html`), `footer`, `floating_widgets`, `analytics`, `extra_js`. No hace falta memorizarlos — se copian ya resueltos al clonar `servelec/base.html`.

`landing/home.html` solo **orquesta** `{% include %}` de `components/*.html` — no tiene HTML propio (así lo dejaron documentado en el archivo). Dos tipos de sección:
- **Estática** (`hero`, `stats`, `cta`): contenido fijo en el HTML del theme, la edita quien programa.
- **Dinámica** (`services`, `about`, `contact`, `gallery`): se llena sola desde el CMS (`{% get_section %}`, `{% get_services %}`) — no hay que tocarla al clonar.

## 1. 📥 Decisión: clonar `servelec`, no `andesscale`

Comparé los dos themes reales que existen hoy:

| | `servelec` | `andesscale` |
|---|---|---|
| Componentes extra | `hero_ctas`, `hero_effects`, `hero_overlay(_theme)`, `stats`, `why_us` | `how_we_work`, `tech_stack` |
| Encaje con Rancho Cachimba | Genéricos de "empresa de servicios" (hero fuerte, prueba social, por qué elegirnos) — reusables para casi cualquier rubro | Específicos de una SaaS/software (stack tecnológico, cómo trabajamos) — no aplican a un rubro rural/turístico |

**`servelec` es la mejor base estructural**, aunque el contenido/colores sean de electricidad — eso es justamente lo que se reemplaza en Parte 2.

## 2. 📝 To Do — clonado (todas DONE)

* **[RC-16] Clonar carpetas** — DONE
  ```bash
  cp -r templates/servelec templates/ranchocachimba
  cp -r static/js/clients/servelec static/js/clients/ranchocachimba
  ```

* **[RC-17] Reemplazar referencias internas `servelec` → `ranchocachimba`** — DONE
  El primer `sed` (case-sensitive) dejó pasar las variantes con mayúscula (`Servelec`, `SERVELEC`) en comentarios — hubo que correr una segunda pasada `s/Servelec/Rancho Cachimba/g` + fix manual de dos headers en `ALL CAPS`. Ojo con esto si se repite el proceso para otro cliente: verificar con `grep -rni servelec ...` (case-insensitive), no solo `grep -rn`.

* **[RC-18] Renombrar el JS del hero a algo neutro** — DONE (`canvas_hero.js`, id DOM `electricCanvas` → `heroCanvas` en el HTML y el JS)

* **[RC-19] Registrar el theme en `Client.THEME_CHOICES`** — DONE (migración `0017_alter_client_template`)
  En `apps/tenants/models.py`:
  ```python
  THEME_CHOICES = [
      ('themes/default', 'Tema Base (Servicios Profesionales)'),
      ('servelec',       'Electricidad (Servelec)'),
      ('ranchocachimba', 'Rancho Cachimba (Turismo Rural)'),
  ]
  ```
  Requiere `python manage.py makemigrations tenants`.

* **[RC-20] Apuntar el `Client` al theme nuevo** — DONE (`client.template = 'ranchocachimba'`)

* **[RC-21] Limpiar herencia visual de Servelec en lo copiado** — DONE
  Se dejó neutro: favicon fallback (ahora un círculo con el color primario del cliente, no el rayo ⚡), los 3 fallbacks de color en `base.html` (`--primary`/`--secondary`/`--accent`, ahora `#0F441A`/`#D2B35C`), todos los `rgba(22,163,74,...)` hardcodeados (ahora `rgba(15,68,26,...)`), y el copy explícitamente eléctrico en `cta.html`, `why_us.html` (los 4 "pilares" tenían texto de rubro eléctrico, incluyendo uno sobre normativa SEC) y `footer.html` (descripción por defecto). Lo que se dejó **sin tocar a propósito**: los `#1DB954`/`#0b2818` hardcodeados dentro de cada componente (esos sí son trabajo de diseño real, no branding — recolorear cada inline style es la tarea de diseño que esta parte busca dejar pendiente, no resolverla).

## 3. 🧪 Verificación — DONE

```bash
python manage.py check_tenant_setup ranchocachimba --settings=config.settings.development
```
Debe seguir en `[OK]` para el tema (ahora resolviendo a `templates/ranchocachimba/` en vez de `templates/themes/default/`).

```
http://localhost:8000/?tenant=ranchocachimba
```
Con `mode_under_construction=True` esto sigue mostrando "En construcción" (el middleware intercepta antes de llegar al theme) — para ver el theme nuevo hay que desactivar `mode_under_construction` temporalmente o revisar directo el template. Confirmar que no queda texto/ícono de Servelec visible.

### Cómo previsualizar el theme en dev (con el runserver ya corriendo)

- `/dashboard/?tenant=ranchocachimba` y `/superadmin/` siempre funcionan, aunque `mode_under_construction=True` (bypass del middleware).
- Para ver `http://localhost:8000/?tenant=ranchocachimba` con el theme real (no "En construcción"), desactivar la bandera temporalmente:
  ```bash
  python manage.py shell --settings=config.settings.development -c "
  from apps.tenants.models import Client
  c = Client.objects.get(slug='ranchocachimba')
  c.mode_under_construction = False
  c.save()
  "
  ```
  y volver a activarla (`= True`) al terminar de mirar — el sitio no está listo para mostrarse público todavía.

A partir de acá, el trabajo restante es diseño puro: contenido de `Section`/`Service` vía dashboard, imágenes, y ajuste fino de `components/*.html`.
