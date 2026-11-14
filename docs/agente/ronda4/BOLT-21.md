# BOLT-21 — `CONS-04`: borrar la edición inline pública (rutas y vistas legacy)

## Contexto verificado (2026-11-14)

Conviven dos formas de editar contenido: la del dashboard (vigente) y una edición inline pública
con htmx, anterior, que nadie enlaza desde los temas actuales.

Legacy (se borra):

- Rutas en `apps/website/urls.py` líneas 42–54: `edit_section`, `cancel_edit_section`,
  `edit_service`, `cancel_edit_service`, `delete_service`, `add_service`, `login_modal`.
- Vistas en `apps/website/views.py`: `login_modal` (259), `edit_section` (611),
  `cancel_edit_section` (640), `edit_service` (651), `add_service` (680), `delete_service` (708),
  `cancel_edit_service` (728).
- Templates: `templates/partials/section_display.html`, `section_edit.html`, `service_card.html`,
  `service_delete_confirm.html`, `service_edit.html` y `templates/auth/login_modal.html`.

Vigente (no se toca): `edit_section_dashboard`, `edit_service_dashboard`,
`delete_service_dashboard` y sus templates en `templates/dashboard/`.

Bug a confirmar: `templates/dashboard/service_confirm_delete.html:43` usa
`{% url 'dashboard_services' %}`, ruta que no existe. La vista `delete_service_dashboard`
(línea 534) renderiza `dashboard/delete_service.html`, así que ese template parece huérfano.

## Qué hacer

1. Antes de borrar, confirma con `grep -rn` que ningún template de tema ni vista vigente incluye
   o renderiza los parciales legacy (`partials/section_`, `partials/service_`, `login_modal`).
   Si alguno **sí** se usa desde código vigente, no lo borres y repórtalo en DECISIONES.
2. Test nuevo `apps/website/tests/test_legacy_routes_removed.py`:
   - `reverse()` de los 7 nombres legacy levanta `NoReverseMatch`.
   - `GET` a `/section/1/edit/`, `/service/1/edit/`, `/service/add/`, `/login-modal/` responde 404
     (con el host de un tenant de prueba).
   - Las rutas del dashboard siguen resolviendo (`reverse('edit_section_dashboard', args=[1])`…).
   - `GET` autenticado de `delete_service_dashboard` responde 200 (prueba que su template
     renderiza sin `NoReverseMatch`).
3. Borra rutas, vistas, templates legacy e imports que queden sin uso.
4. `service_confirm_delete.html`: si confirmas que nadie lo renderiza, bórralo; si alguien lo
   usa, corrige el `{% url %}` a la ruta real del listado de servicios del dashboard.

## No tocar

Las vistas y templates del dashboard, `partials/contact_form*.html`, `partials/contact_success.html`.
No reorganices `views.py` (eso es `CONS-07`).

## Tests de rojo

`apps.website.tests.test_legacy_routes_removed`

## DoD

- [ ] Los 7 nombres de ruta y sus vistas no existen; los 6 templates legacy borrados.
- [ ] `grep -rn "dashboard_services" templates apps` sin resultados.
- [ ] Suite, ruff y Playwright verdes.
- [ ] Cierre documental (`CONS-04`).
