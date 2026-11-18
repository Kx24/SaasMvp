# BOLT-70 — `CONS-13` (parte 1 de 2): comandos de gestión sin cobertura

> Card de tests. Sin cambios de comportamiento: si al testear aparece un bug real, arréglalo
> mínimo y regístralo como hallazgo (regla del arnés).

## Contexto verificado (2026-11-18)

Estos comandos de gestión quedaron en 0 % de cobertura tras `CONS-11` (`BOLT-38`/`39`):

- `apps/core/management/commands/audit_cloudinary_assets.py`
- `apps/core/management/commands/check_cloudinary.py`
- `apps/tenants/management/commands/setup_cloudinary_folders.py`
- `apps/tenants/management/commands/setup_dev_env.py`
- `apps/tenants/management/commands/seed_e2e_tenants.py` (crea el usuario `owner-e2e` con
  contraseña de desarrollo; el test debe correr con `DEBUG=True` y comprobar el comportamiento
  cuando no lo está, si el comando lo valida)
- `apps/marketing/management/commands/verify_search_console.py`
- `apps/tenants/management/commands/create_tenant.py` — **solo cúbrelo si es barato; no lo borres**
  (¿muerto frente a `provision_tenant`? es decisión del dueño, queda en el kanban).

Ya tienen tests: `cloudinary_usage`, `data_subject`, `purge_expired_data`, `send_contact_digest`,
`send_pending_emails`, `provision_tenant`, `check_tenant_setup`, `list_tenants`,
`add_preview_domain`, `update_domain`, `setup_production`.

## Qué hacer

1. Mide primero: `python -m coverage run --source=apps manage.py test apps` y
   `python -m coverage report --include='*/management/commands/*'` para ver los porcentajes
   reales antes de escribir nada.
2. Un archivo de tests por comando (o agrupados por app) en `apps/<app>/tests/`; llamar con
   `call_command(...)` y `StringIO` para stdout/stderr. **Nada de llamadas reales** a Cloudinary,
   Google ni red: parchea `cloudinary.api`, `cloudinary.uploader`, `requests` y lo que haga falta.
   Casos: camino feliz, argumento inválido / falta de configuración (mensaje claro, `CommandError`)
   y `--dry-run` o equivalente si existe.
3. Meta: cada comando listado ≥ 80 % de líneas y ninguno queda en 0 %. No bajes ningún umbral del
   `scripts/gate_baseline.json` (lo actualiza el gate al subir).

## Tests de rojo

Ninguno (`red_tests` vacío): solo se agrega cobertura a código existente. Documéntalo en el informe.

## No tocar

El comportamiento de los comandos (salvo un bug real mínimo), `render.yaml`, `build.sh`,
`setup_production.py` (ya cubierto).

## DoD

- [ ] Ningún comando de la lista queda en 0 %; cobertura total no baja.
- [ ] Cierre documental: `CONS-13` se **acota** (parte 1 hecha: comandos de gestión); anota
      `CONS-13 (parte)` en el histórico.
