# Ronda 6 — estado

Rama `agent/ronda6` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-21` | `CONS-04` | Borrar la edición inline pública (rutas legacy) | ✅ DONE | 341 | 0.59 |
| `BOLT-23` | `SEC-14` | Salidas sin escapar (mark_safe) y JSON-LD | ✅ DONE | 349 | 0.71 |
| `BOLT-24` | `SEC-05b` | Filtros por cliente en el admin | ⏳ TODO |  |  |
| `BOLT-32` | `SEC-05b` | Desplegable de PaymentLog.order por tenant | ⏳ TODO |  |  |
| `BOLT-22` | `SEC-06` | Credenciales SMTP/API cifradas en reposo | ⏳ TODO |  |  |
| `BOLT-27` | `SEC-10` | Dependencias al día y pip-audit | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-21`: El dev cambió el Cancelar de service_confirm_delete.html a 'dashboard_sections' porque no hay ruta de listado de servicios. Confirmar que ese destino es el correcto.
- `BOLT-21`: Confirmar que la vista delete_service_dashboard renderiza service_confirm_delete.html y que el cambio de template es intencional. Se vio en el diff de services.py.
- `BOLT-21`: Mirar a mano en el navegador el flujo de borrado de un servicio desde el dashboard.
- `BOLT-23`: Confirmar que Playwright/e2e pase en CI o a mano: se toca el render de todas las páginas y el gate reportó e2e con ran=false.
- `BOLT-23`: El único mark_safe que queda (seo_tags.py:162, nosec B308 B703) depende de que _esc() se mantenga; revisar que la justificación escrita convenza.
- `BOLT-23`: Decidir si se abre card para el |safe de section_display.html y para actualizar SEGURIDAD.md.
- `BOLT-23`: Confirmar que el HTML de los tags de Cloudinary para entradas normales no cambió (por ejemplo el orden de atributos o los espacios del <video>).

## Hallazgos incidentales

- `BOLT-21`: La vista dashboard_services en views/services.py sigue exportada, pero no tiene ruta en urls.py. Es código muerto previo a esta card.
- `BOLT-21`: El grep 'dashboard_services' del DoD sigue encontrando la función Python en apps/. Ya no hay ningún `{% url %}` que la use.
- `BOLT-21`: Los cambios de formato en views/__init__.py y test_views_package.py dejaron líneas largas que ruff acepta. Conviene ordenarlas.
- `BOLT-23`: Documentacion/SEGURIDAD.md (líneas 20 y 35) sigue diciendo 21 avisos Medium para SEC-14; falta actualizarlo.
- `BOLT-23`: {{ section.content|safe }} en templates/partials/section_display.html sigue sin escapar el contenido que escribe el cliente; queda fuera del alcance de esta card.
- `BOLT-23`: _esc() en seo_tags.py no escapa & (no es explotable como XSS, pero el HTML resultante no es estricto).
