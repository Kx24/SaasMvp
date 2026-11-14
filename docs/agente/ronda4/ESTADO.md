# Ronda 4 — estado

Rama `agent/ronda4` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-17` | `SEC-17` | Comentarios DEBUG fuera del HTML público | ✅ DONE | 297 | 0.36 |
| `BOLT-18` | `CONS-05` | Eliminar flags sin módulo (blog, testimonios) | ✅ DONE | 300 | 0.41 |
| `BOLT-19` | `DEUDA-08` | Portada de sitio nuevo con titular | ✅ DONE | 302 | 0.66 |
| `BOLT-20` | `SEC-08` | Un solo login y next validado | ⏳ TODO |  |  |
| `BOLT-21` | `CONS-04` | Borrar la edición inline pública (rutas legacy) | ⏳ TODO |  |  |
| `BOLT-22` | `SEC-06` | Credenciales SMTP/API cifradas en reposo | ⏳ TODO |  |  |
| `BOLT-23` | `SEC-14` | Salidas sin escapar (mark_safe) y JSON-LD | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-17`: El rojo del gate (red_check) se confirmó por un error de entorno: en el checkout temporal de HEAD faltaba SECRET_KEY y los tests no llegaron a correr. El rojo real solo lo reporta el dev, que lo vio localmente al fallar el render antes de editar los templates.
- `BOLT-17`: El test de render usa `assertNotContains(response, 'DEBUG')`, que es amplio: un texto legítimo con 'DEBUG' en la home lo haría fallar. Hoy pasa.
- `BOLT-17`: La fila SEC-17 del histórico usa el formato de sus vecinas, no el de la línea que indica `_CIERRE.md`.
- `BOLT-18`: Migración 0027: RemoveField irreversible en cuanto a datos (se pierden los valores de los flags en producción); es lo que pide el spec.
- `BOLT-18`: El dev no corrió Playwright, pero el gate determinista reportó e2e en verde.
- `BOLT-18`: La fila D11 del kanban quedó con '✅' en la dependencia CONS-05; confirmar que el formato es el esperado.
- `BOLT-19`: Cambio visible al cliente: los sitios existentes con slot_key='hero' y galería apagada ahora muestran portada con titular. Antes no mostraban nada.
- `BOLT-19`: seed_e2e_tenants crea la hero sin slot_key (queda en 'empty'). Confirmar que Playwright 7/7 sigue pasando. El gate e2e no corrió (ran: false).
- `BOLT-19`: El test del default del get_or_create del dashboard se comprueba por inspección de código, no levantando la vista. Es débil, pero el spec lo permitía.
- `BOLT-19`: El dev no vio el rojo antes de editar. El red_check del orquestador sí lo confirmó: 4 fallos contra HEAD.

## Hallazgos incidentales

- `BOLT-19`: provision_tenant no crea Domain.
- `BOLT-19`: provision_tenant imprime "Template origen _default no existe".
- `BOLT-19`: El informe del dev no registró estos hallazgos como filas nuevas en el kanban.
