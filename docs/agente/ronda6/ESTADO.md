# Ronda 6 — estado

Rama `agent/ronda6` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-21` | `CONS-04` | Borrar la edición inline pública (rutas legacy) | ✅ DONE | 341 | 0.59 |
| `BOLT-23` | `SEC-14` | Salidas sin escapar (mark_safe) y JSON-LD | ⏳ TODO |  |  |
| `BOLT-24` | `SEC-05b` | Filtros por cliente en el admin | ⏳ TODO |  |  |
| `BOLT-32` | `SEC-05b` | Desplegable de PaymentLog.order por tenant | ⏳ TODO |  |  |
| `BOLT-22` | `SEC-06` | Credenciales SMTP/API cifradas en reposo | ⏳ TODO |  |  |
| `BOLT-27` | `SEC-10` | Dependencias al día y pip-audit | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-21`: El dev cambió el Cancelar de service_confirm_delete.html a 'dashboard_sections' porque no hay ruta de listado de servicios. Confirmar que ese destino es el correcto.
- `BOLT-21`: Confirmar que la vista delete_service_dashboard renderiza service_confirm_delete.html y que el cambio de template es intencional. Se vio en el diff de services.py.
- `BOLT-21`: Mirar a mano en el navegador el flujo de borrado de un servicio desde el dashboard.

## Hallazgos incidentales

- `BOLT-21`: La vista dashboard_services en views/services.py sigue exportada, pero no tiene ruta en urls.py. Es código muerto previo a esta card.
- `BOLT-21`: El grep 'dashboard_services' del DoD sigue encontrando la función Python en apps/. Ya no hay ningún `{% url %}` que la use.
- `BOLT-21`: Los cambios de formato en views/__init__.py y test_views_package.py dejaron líneas largas que ruff acepta. Conviene ordenarlas.
