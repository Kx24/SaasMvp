# Ronda 16 — estado

Rama `agent/ronda16` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-77` | `DEUDA-18` | Teléfono del JSON-LD desde ClientSettings.contact_phone | ✅ DONE | 942 | 0.42 |
| `BOLT-78` | `SEC-19` | Rechazar rutas fuera del directorio del tenant en tenant_tags | ✅ DONE | 947 | 0.36 |
| `BOLT-79` | `DEUDA-17` | Acotar las referencias de audit_cloudinary_assets | ✅ DONE | 950 | 0.4 |
| `BOLT-80` | `BIZ-04` | Client.plan como FK a Plan | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-78`: tenant_media sigue devolviendo URLs con `../` sin validar. No lee el disco y el spec lo dejaba como opcional.
- `BOLT-78`: test_tenant_static_rechaza_ruta_absoluta construye la ruta con repr() dentro de la plantilla. En Windows las barras invertidas quedan duplicadas, y el test pasa por la comprobación de `drive` y no por la de is_absolute.
- `BOLT-78`: Es solo lectura, así que no pude confirmar que la fila SEC-19 ya no esté en la tabla del kanban; la búsqueda solo encontró menciones en las líneas 29 y 33 del texto de arriba, que son narrativa.
- `BOLT-79`: Antes de correr --fix en producción, ejecutar la auditoría en modo dry-run y revisar la lista de huérfanos, porque la dirección del cambio es de riesgo para la purga.
- `BOLT-79`: Decisión del dev que el spec no cubría: usar los slugs de Client como prefijos legacy y la heurística del segundo segmento en VALID_RESOURCE_TYPES.
- `BOLT-79`: El dev no ejecutó el rojo por su cuenta, pero el red_check del gate lo confirmó: el test de no-referencia falla en HEAD.

## Hallazgos incidentales

- `BOLT-79`: Brecha de riesgo anotada por el dev: un asset legacy de un tenant ya borrado (slug que ya no existe en Client) cuyo segundo segmento no es una categoría conocida, p. ej. viejo/foo.jpg, ya no cuenta como referenciado, así que --fix podría purgarlo. Es un residuo sin dueño.
- `BOLT-79`: Un CharField cuyo valor no contiene '/' (p. ej. un public_id suelto en la raíz de Cloudinary) deja de contar como referencia. Es coherente con el spec, pero amplía lo que --fix puede considerar huérfano.
