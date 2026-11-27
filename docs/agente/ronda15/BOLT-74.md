# BOLT-74 — `DEUDA-15`: borrar el comando `create_tenant`

## Decisión del dueño (2026-11-22)

Se borra, con sus tests. `provision_tenant` es el comando vigente. Para algo rápido en local quedan
`setup_dev_env` y `seed_e2e_tenants`.

## Contexto verificado (2026-11-22)

- Comando: `apps/tenants/management/commands/create_tenant.py`.
- Sus tests están en `apps/tenants/tests_management_commands_misc.py`, **mezclados con los de otros
  comandos**: borra solo los de `create_tenant` (helper, clases y casos que lo usan) y deja el resto
  intacto. Si tras borrar el archivo queda vacío, bórralo.
- Menciones en docs vigentes: `Documentacion/README.md` (línea ~201, "Crea tenant interactivo") y,
  si aparece, `Documentacion/ARQUITECTURA.md`. `setup_dev_env.py` tiene un método propio llamado
  `create_tenant`: **no es el comando, no lo toques**.

## Qué hacer

1. Borra el comando y sus tests.
2. Quita las menciones del comando en los docs vigentes (no en `historico/` ni en `docs/agente/`).
3. Si algo más importaba el comando, corrígelo y anótalo en el informe.

## Tests de rojo

`apps.tenants.tests_create_tenant_removed` (archivo nuevo): comprueba con
`django.core.management.get_commands()` que `create_tenant` **no** está registrado y que
`provision_tenant` sí. Debe fallar contra el código actual.

## No tocar

`provision_tenant`, `setup_dev_env`, `seed_e2e_tenants`, `render.yaml`, `build.sh`.

## DoD

- [ ] `create_tenant` ya no existe como comando ni quedan tests suyos.
- [ ] La cobertura total no baja (el gate lo verifica; si bajara por borrar código cubierto, el
      trinquete lo marcará: anótalo en el informe).
- [ ] Cierre documental: borra la fila `DEUDA-15` del kanban y agrega la línea al histórico.
