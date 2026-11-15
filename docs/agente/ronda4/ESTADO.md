# Ronda 4 — estado

Rama `agent/ronda4` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-17` | `SEC-17` | Comentarios DEBUG fuera del HTML público | ✅ DONE | 297 | 0.36 |
| `BOLT-18` | `CONS-05` | Eliminar flags sin módulo (blog, testimonios) | ✅ DONE | 300 | 0.41 |
| `BOLT-19` | `DEUDA-08` | Portada de sitio nuevo con titular | ✅ DONE | 302 | 0.66 |
| `BOLT-20` | `SEC-08` | Un solo login y next validado | ✅ DONE | 309 | 0.48 |
| `BOLT-21` | `CONS-04` | Borrar la edición inline pública (rutas legacy) | ❌ REJECTED |  | 0.47 |
| `BOLT-22` | `SEC-06` | Credenciales SMTP/API cifradas en reposo | ⛔ BLOCKED |  | 0 |
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
- `BOLT-20`: Cambio de autenticación: `client_login` ahora redirige a `next`. Confirmar que un staff que llega con `next=/superadmin/` aterriza bien. Antes iba a `/superadmin/`; ahora va ahí solo si `next` es interno, y el login del admin sigue siendo `/superadmin/`.
- `BOLT-20`: Se borraron 3 tests de `apps/core/tests/test_logging_pii.py` (login sin dirección en el log, mensajes indistinguibles, helper). Confirmar que la cobertura equivalente de `client_login` es suficiente.
- `BOLT-20`: Se eliminó `templates/accounts/login.html` y los enlaces de recuperar contraseña apuntan ahora a `/auth/login/`. Probar a mano el flujo de recuperar contraseña.
- `BOLT-20`: El dev no corrió Playwright (lo hizo el gate: e2e pasó). La cifra de cobertura de `apps/accounts` (78 %) es del informe del dev.

## Hallazgos incidentales

- `BOLT-19`: provision_tenant no crea Domain.
- `BOLT-19`: provision_tenant imprime "Template origen _default no existe".
- `BOLT-19`: El informe del dev no registró estos hallazgos como filas nuevas en el kanban.
- `BOLT-20`: `apps/accounts/forms.py::LoginForm` quedó sin uso (código muerto); borrarlo en una card aparte.
- `BOLT-20`: El test de forgot_password probablemente no falla contra HEAD: su rojo inicial fue un 404 por falta de host en el test, no por el código. El red-check dio 4 fallos de 9, así que cumple igual.

## Pendiente de tu decisión

- `BOLT-21` (REJECTED): el validador no devolvió un veredicto: You've hit your 5-hour limit · resets 2:10pm (America/Santiago)
- `BOLT-22` (BLOCKED): la sesión del agente falló: You've hit your 5-hour limit · resets 2:10pm (America/Santiago)
