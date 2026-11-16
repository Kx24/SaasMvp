# BOLT-53 — `CONS-09`: menú y acceso del dashboard desde el registro de módulos

> Decisiones del dueño (2026-11-15): un módulo apagado **no aparece en el menú y sus URLs
> responden 404**; excepción: con el contacto apagado, "Mensajes" sigue visible y accesible (hay
> mensajes ya recibidos) y lo que se apaga es el formulario público y su envío.

## Contexto verificado (2026-11-15)

- `BOLT-52` dejó `apps/tenants/modules.py` (`MODULES`, `is_enabled`, `enabled_modules`,
  `module_for_url`, `MenuEntry`).
- Hoy, con la galería apagada, el menú muestra "Portada" y "Galería" atenuados
  (`opacity-40 pointer-events-none` en `templates/dashboard/base.html`) y las vistas consultan
  `settings.enable_gallery` a mano (`views/gallery.py` ×2, `views/branding.py`,
  `views/services.py`) con respuestas distintas entre sí (mira cada una).
- `tenant_permission_required(action)` (`apps/accounts/decorators.py`) ya envuelve cada vista.

## Qué hacer

1. **Decorador** `module_required(key)` en `apps/tenants/modules.py` (o en
   `apps/accounts/decorators.py` si encaja mejor): si `is_enabled(request.client, key)` es falso
   → `Http404`. Se aplica **debajo** de `tenant_permission_required` (primero login y tenant,
   luego módulo). Aplícalo a todas las vistas de cada módulo con flag según `url_names`, y borra
   las consultas manuales de `enable_gallery` que solo servían para cortar el acceso. Las que
   deciden *contenido* (por ejemplo qué mostrar en la portada) pasan a usar `is_enabled`.
2. **Contacto apagado:** `contact_submit` responde 404 y el formulario público no se renderiza
   (los templatetags/plantillas que hoy miran `enable_contact_form` pasan a `is_enabled`);
   `dashboard_contacts`, `mark_contact_read` y `mark_contact_replied` siguen funcionando.
3. **Menú generado:** un context processor `dashboard_menu` (junto a `dashboard_permissions`, y
   registrado en `config/settings/base.py`) devuelve la lista ordenada de entradas visibles para
   ese usuario y tenant: módulo activo (o `menu_visible_when_disabled`) **y** permiso del rol.
   `templates/dashboard/base.html` recorre esa lista en vez de tener los enlaces fijos; conserva
   clases, iconos, el estado `active` y el contador de mensajes sin leer. Los iconos se resuelven
   por `MenuEntry.icon` con un parcial por icono o un `{% if %}` corto; no metas HTML en Python.
4. Un test del registro debe seguir cubriendo todas las rutas (el de `BOLT-52` no se debilita).

## Tests de rojo

`apps.tenants.tests_module_access` (archivo nuevo con ese nombre exacto). Casos:
- Galería apagada: cada URL del módulo `gallery` → 404 para un `owner`; el menú no contiene el
  enlace; con la galería encendida → 200 y el enlace aparece.
- Contacto apagado: `contact_submit` → 404, la home no renderiza el formulario,
  `dashboard_contacts` → 200 y "Mensajes" sigue en el menú.
- El menú de cada rol (`owner`, `admin`, `editor`, `viewer`) con todo activo contiene exactamente
  los enlaces que permite `DASHBOARD_PERMISSIONS` (misma matriz de `DASH-04`).
- Un usuario de otro tenant sigue recibiendo 403 (no 404) en un módulo apagado del tenant ajeno:
  el tenant se comprueba antes que el módulo.
- `base.html` no contiene `{% url 'dashboard_gallery' %}` ni los demás enlaces fijos.

## No tocar

La matriz de permisos. El registro (`MODULES`) salvo corrección demostrada por un test. Modelos y
migraciones. Los tests de `tests_dashboard_roles.py` no se editan para pasar.

## DoD

- [ ] Menú y acceso derivan del registro; sin consultas sueltas de `enable_gallery` para cortar
      acceso.
- [ ] Playwright y a11y verdes (cambia `templates/dashboard/base.html`).
- [ ] Suite de aislamiento y matriz de roles verdes sin editar.
- [ ] Cierre documental (`CONS-09`). En `revisar_humano`: **cambio visible** — con la galería
      apagada "Portada/Galería" ya no aparecen atenuados sino que desaparecen (si `Portada` quedó
      en `core`, dilo); revisar el menú en el navegador con cada rol.
