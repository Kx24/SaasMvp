# BOLT-44 — `FLOW-04`: `provision_tenant` deja el `Domain` claro y sin aviso confuso

## Contexto verificado (2026-11-15)

- `apps/tenants/management/commands/provision_tenant.py` sí llama a `Domain.objects.create(...)`
  (líneas 254 y 265), pero `BOLT-19` reportó que al provisionar un tenant de prueba no quedaba
  `Domain` y que el comando imprime `Template origen "_default" no existe` (línea 394). El
  argumento `--source-template` tiene default `_default` (línea 172), carpeta que ya no existe:
  los temas viven en `templates/themes/…` y los resuelve `TenantTemplateLoader`.
- Sin `Domain`, el middleware no resuelve el tenant por Host: el sitio no abre.

## Qué hacer

1. Reproduce primero: en un test, `call_command('provision_tenant', 'x', '--industry=…',
   '--theme=themes/default')` y observa qué `Domain` quedan y qué imprime. Documenta en el
   informe en qué condiciones no se crea el `Domain` (¿falta un argumento?, ¿rama `--dry-run`?,
   ¿depende de `BASE_DOMAIN`?).
2. Deja el comportamiento explícito: tras provisionar, el tenant tiene **un `Domain` primario**
   utilizable (en desarrollo `<slug>.localhost`; en producción lo que derive de `BASE_DOMAIN` /
   `PREVIEW_DOMAIN`, sin hardcodear `.andesscale.cl`), o el comando termina con un mensaje claro
   que dice qué falta y cómo crearlo. Nunca un tenant "provisionado" que no abre sin aviso.
3. El aviso de `_default`: si la copia de plantillas por tenant ya no aplica (el loader resuelve
   por tema), elimina ese paso muerto y su argumento, o cámbialo por un mensaje correcto. No dejes
   un warning que describe una carpeta inexistente.
4. `check_tenant_setup <slug>` debe pasar (o avisar con precisión) sobre un tenant recién
   provisionado.

## Tests de rojo

`apps.tenants.tests_provision_domain` (archivo nuevo con ese nombre exacto: el orquestador confirma el rojo con esa etiqueta).
Caso mínimo: tras el comando
existe exactamente un `Domain` primario del tenant y la salida no contiene "no existe".

## No tocar

`setup_production`. El modelo `Domain`. Los tenants existentes (el test usa slugs nuevos).

## DoD

- [ ] Provisionar deja un `Domain` primario o falla con un mensaje accionable.
- [ ] Sin avisos sobre `_default`.
- [ ] `CLAUDE.md` no se toca; si el uso del comando cambió, repórtalo en `revisar_humano` para
      que el dueño actualice la sección "Comandos frecuentes".
- [ ] Cierre documental (`FLOW-04`).
