# Ronda 6 — estado

Rama `agent/ronda6` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-21` | `CONS-04` | Borrar la edición inline pública (rutas legacy) | ✅ DONE | 341 | 0.59 |
| `BOLT-23` | `SEC-14` | Salidas sin escapar (mark_safe) y JSON-LD | ✅ DONE | 349 | 0.71 |
| `BOLT-24` | `SEC-05b` | Filtros por cliente en el admin | ✅ DONE | 352 | 0.38 |
| `BOLT-32` | `SEC-05b` | Desplegable de PaymentLog.order por tenant | ✅ DONE | 354 | 0.4 |
| `BOLT-22` | `SEC-06` | Credenciales SMTP/API cifradas en reposo | ✅ DONE | 367 | 1.43 |
| `BOLT-27` | `SEC-10` | Dependencias al día y pip-audit | ✅ DONE | 372 | 0.47 |

## Revisar a mano en el PR

- `BOLT-21`: El dev cambió el Cancelar de service_confirm_delete.html a 'dashboard_sections' porque no hay ruta de listado de servicios. Confirmar que ese destino es el correcto.
- `BOLT-21`: Confirmar que la vista delete_service_dashboard renderiza service_confirm_delete.html y que el cambio de template es intencional. Se vio en el diff de services.py.
- `BOLT-21`: Mirar a mano en el navegador el flujo de borrado de un servicio desde el dashboard.
- `BOLT-23`: Confirmar que Playwright/e2e pase en CI o a mano: se toca el render de todas las páginas y el gate reportó e2e con ran=false.
- `BOLT-23`: El único mark_safe que queda (seo_tags.py:162, nosec B308 B703) depende de que _esc() se mantenga; revisar que la justificación escrita convenza.
- `BOLT-23`: Decidir si se abre card para el |safe de section_display.html y para actualizar SEGURIDAD.md.
- `BOLT-23`: Confirmar que el HTML de los tags de Cloudinary para entradas normales no cambió (por ejemplo el orden de atributos o los espacios del <video>).
- `BOLT-24`: `TenantAdminMixin.get_list_filter` llama a `super().get_list_filter`. Confirmar que ningún admin de un modelo con filtro `client` pierda el filtro a propósito, por ejemplo si un staff necesitara filtrar por cliente.
- `BOLT-24`: El `TenantAdminMixin` local de `apps/website/admin.py` no se tocó, como pedía el spec. No se comparó su comportamiento con el de `accounts`, así que su `get_list_filter` sigue sin cubrir.
- `BOLT-32`: Un staff sin tenant asignado ahora recibe `none()` en todos los FKs hacia modelos con `client`. Antes veía todas las filas. Confirmar que eso es lo que se quiere.
- `BOLT-32`: La regla aplica a todos los admins que usan TenantAdminMixin. Probar a mano en /superadmin/ con un staff de tenant que los formularios con FKs a modelos con `client` sigan funcionando.
- `BOLT-22`: ANTES DE DESPLEGAR: CREAR FIELD_ENCRYPTION_KEY EN RENDER (producción no arranca sin ella) y guardar una copia fuera de Render: perderla deja las credenciales ilegibles.
- `BOLT-22`: Migraciones 0028 y 0029 (datos): revisar contra Neon antes del deploy. El reverso deja las credenciales en texto plano.
- `BOLT-22`: Admin: ClientEmailSettingsForm con PasswordInput y conservación del valor vacío. Probarlo a mano en /superadmin/, incluido el inline dentro de Client.
- `BOLT-22`: Dependencia nueva cryptography==50.0.2 en requirements.txt: confirmar que la versión se instala en Render.
- `BOLT-27`: gunicorn pasó de 21.2.0 a 27.0.1, un salto de mayor que no se probó contra Render. Conviene revisar que el comando de inicio del servicio (Procfile y render.yaml) siga siendo compatible tras el deploy.
- `BOLT-27`: pillow subió de 11 a 13 (excepción autorizada). Los tests pasan, pero conviene mirar que las subidas e imágenes reales funcionen en staging.
- `BOLT-27`: pip-audit quedó sin pin en requirements-dev.txt.
- `BOLT-27`: development.py reasigna INSTALLED_APPS para agregar django_extensions. Hay que confirmar que ningún comando de producción o de CI dependa de django_extensions (por ejemplo shell_plus).
- `BOLT-27`: pip-audit y Playwright se corrieron solo en local, no en la CI real.

## Hallazgos incidentales

- `BOLT-21`: La vista dashboard_services en views/services.py sigue exportada, pero no tiene ruta en urls.py. Es código muerto previo a esta card.
- `BOLT-21`: El grep 'dashboard_services' del DoD sigue encontrando la función Python en apps/. Ya no hay ningún `{% url %}` que la use.
- `BOLT-21`: Los cambios de formato en views/__init__.py y test_views_package.py dejaron líneas largas que ruff acepta. Conviene ordenarlas.
- `BOLT-23`: Documentacion/SEGURIDAD.md (líneas 20 y 35) sigue diciendo 21 avisos Medium para SEC-14; falta actualizarlo.
- `BOLT-23`: {{ section.content|safe }} en templates/partials/section_display.html sigue sin escapar el contenido que escribe el cliente; queda fuera del alcance de esta card.
- `BOLT-23`: _esc() en seo_tags.py no escapa & (no es explotable como XSS, pero el HTML resultante no es estricto).
- `BOLT-32`: El mixin local de apps/website/admin.py sigue sin unificarse con el de apps/accounts/mixins.py. No se comparó su comportamiento en esta card, tal como pedía el spec.
- `BOLT-32`: La regla solo cubre FKs hacia modelos con campo `client` directo. Un FK hacia un modelo que llegue al tenant por otro camino (por ejemplo `order__client`) no queda acotado. No hay ningún caso hoy en los admins revisados, pero la regla no lo cubre.
