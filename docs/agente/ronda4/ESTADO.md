# Ronda 4 — estado

Rama `agent/ronda4` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Commit | Costo USD |
|---|---|---|---|---|---|
| `BOLT-17` | `SEC-17` | Comentarios DEBUG fuera del HTML público | ✅ DONE |  | 0.36 |
| `BOLT-18` | `CONS-05` | Eliminar flags sin módulo (blog, testimonios) | ⏳ TODO |  |  |
| `BOLT-19` | `DEUDA-08` | Portada de sitio nuevo con titular | ⏳ TODO |  |  |
| `BOLT-20` | `SEC-08` | Un solo login y next validado | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-17`: El rojo del gate (red_check) se confirmó por un error de entorno: en el checkout temporal de HEAD faltaba SECRET_KEY y los tests no llegaron a correr. El rojo real solo lo reporta el dev, que lo vio localmente al fallar el render antes de editar los templates.
- `BOLT-17`: El test de render usa `assertNotContains(response, 'DEBUG')`, que es amplio: un texto legítimo con 'DEBUG' en la home lo haría fallar. Hoy pasa.
- `BOLT-17`: La fila SEC-17 del histórico usa el formato de sus vecinas, no el de la línea que indica `_CIERRE.md`.
