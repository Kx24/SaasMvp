# BOLT-52 — `CONS-08`: registro de módulos (opción A)

> **Spec aprobado por el dueño el 2026-11-15**, con tres decisiones: (1) con contacto apagado,
> "Mensajes" sigue visible; (2) servicios no lleva flag, siempre activo; (3) un módulo apagado
> responde 404. Sin migraciones ni dependencias nuevas.

## Contexto verificado (2026-11-15)

- El menú del dashboard está escrito a mano en `templates/dashboard/base.html` (enlaces a
  `dashboard`, `dashboard_branding`, `dashboard_portada`, `dashboard_gallery`,
  `dashboard_sections`, `dashboard_contacts`), con `dash_perms` (`DASH-04`) y con
  `client.settings.enable_gallery` consultado en la plantilla.
- `ClientSettings.enable_gallery` se consulta suelto en `apps/website/views/gallery.py` (2),
  `views/branding.py`, `views/services.py`, y `templatetags/website_tags.py` (2).
  `ClientSettings.enable_contact_form` existe (`apps/tenants/models.py:337`).
- Límites del plan en `Client`: `max_images`, `max_pages`, `max_services`
  (`apps/tenants/models.py:88-90`); además `ClientSettings.gallery_images_limit`.
- Permisos por rol: `apps/accounts/permissions.py::DASHBOARD_PERMISSIONS`.
- Rutas del dashboard: `apps/website/urls.py`.

## Qué hacer (esta card solo declara; no cambia comportamiento)

1. Archivo nuevo `apps/tenants/modules.py`:
   - `@dataclass(frozen=True) class MenuEntry`: `label`, `url_name`, `icon` (nombre corto),
     `permission` (clave de `DASHBOARD_PERMISSIONS`), `order`.
   - `@dataclass(frozen=True) class Module`: `key`, `label`, `flag` (nombre de un campo booleano
     de `ClientSettings`, o `None` = siempre activo), `limit_field` (nombre de un campo de
     `Client`, o `None`), `url_names` (todas las rutas del dashboard que pertenecen al módulo),
     `menu` (tupla de `MenuEntry`), `public_component` (ruta de plantilla o `None`),
     `menu_visible_when_disabled` (bool, default `False`).
   - `MODULES`: tupla con exactamente estos cuatro módulos:

     | key | flag | limit_field | menú | notas |
     |---|---|---|---|---|
     | `core` | `None` | `None` | Inicio, Marca, Portada, Secciones | siempre activo |
     | `services` | `None` | `max_services` | sin entrada propia (vive en Secciones) | siempre activo |
     | `gallery` | `enable_gallery` | `max_images` | Galería | |
     | `contact` | `enable_contact_form` | `None` | Mensajes | `menu_visible_when_disabled=True` |

     Asigna cada ruta de `apps/website/urls.py` con prefijo `dashboard/` (más `mark_contact_read`
     y `mark_contact_replied`) a un módulo. `dashboard_portada`: decide por el código si pertenece
     a `core` o a `gallery` (hoy depende de `enable_gallery`) y justifícalo en un comentario.
   - Funciones: `get_module(key)`, `is_enabled(client, key) -> bool`,
     `enabled_modules(client) -> tuple[Module]`, `module_for_url(url_name) -> Module | None`.
     `is_enabled` con `client=None` o sin `settings` → solo los módulos sin flag.
2. `Documentacion/ARQUITECTURA.md`: sección "Módulos" con la tabla y cómo se declara uno nuevo.

## Tests de rojo

`apps.tenants.tests_modules` (archivo nuevo con ese nombre exacto). Casos:
- **Cobertura de rutas:** toda ruta del dashboard en `apps/website/urls.py` pertenece a
  exactamente un módulo; una ruta nueva sin declarar hace fallar el test.
- Cada `flag` es un campo booleano real de `ClientSettings`; cada `limit_field` es un campo real
  de `Client`; cada `permission` existe en `DASHBOARD_PERMISSIONS`; cada `url_name` resuelve con
  `reverse` (usa argumentos de prueba cuando la ruta los pide).
- `is_enabled`: galería apagada → `False`; contacto apagado → `False`; `core` y `services`
  siempre `True`; cliente sin settings → solo los módulos sin flag.
- Las claves de módulo son únicas y `MODULES` es inmutable.

## No tocar

`templates/dashboard/base.html`, las vistas y los templatetags: el menú y los decoradores son la
card siguiente (`BOLT-53`). Modelos y migraciones.

## DoD

- [ ] El registro declara los cuatro módulos y cubre todas las rutas del dashboard.
- [ ] Ningún cambio de comportamiento: la suite previa pasa sin editar.
- [ ] Cierre documental (`CONS-08`).
