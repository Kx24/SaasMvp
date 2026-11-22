# BOLT-45 — `LEY-08`: aviso previo antes de purgar mensajes sin leer

## Contexto verificado (2026-11-15)

- `apps/tenants/management/commands/send_contact_digest.py`: `_purge_all` corre para todo tenant
  activo; `_purge_beyond_legal_cap` borra los mensajes de contacto con más de
  `settings.CONTACT_MAX_RETENTION_DAYS` (365) días contados desde `created_at`, **también los
  `new` sin leer** y también en tenants con la purga automática apagada (`BOLT-26`, Ley 21.719).
- El digest (`_process_tenant` → `_send_digest_email`) informa lo ya purgado (`purge_info`), pero
  no avisa **antes**: un cliente puede perder un mensaje que nunca leyó sin haber sido advertido.

## Qué hacer

1. Nuevo setting `CONTACT_PURGE_WARNING_DAYS` (default 30) en `config/settings/base.py`.
2. En el digest de cada tenant, calcula los mensajes con estado `new` que alcanzarán el tope
   legal dentro de los próximos `CONTACT_PURGE_WARNING_DAYS` días y agrégalos al contexto
   (`expiring_count` y la fecha de borrado más próxima).
3. La plantilla del correo del digest muestra, solo si `expiring_count > 0`, un bloque visible:
   cuántos mensajes sin leer se borrarán, desde qué fecha, y el enlace al dashboard de mensajes
   (URL del sitio vía el mecanismo existente: `Domain` primario / `BASE_URL`; nada hardcodeado).
4. Si un tenant tiene mensajes por vencer, el digest **se envía aunque no haya mensajes nuevos**
   esa semana (el aviso es el motivo). Respeta `--dry-run`.
5. El aviso cuenta, no lista datos personales: sin nombres ni correos de los remitentes.

## Tests de rojo

`apps.tenants.tests_digest_warning` (archivo nuevo con ese nombre exacto: el orquestador confirma el rojo con esa etiqueta).
Casos: mensaje `new` a 340 días → el correo incluye el
aviso con el conteo; mensaje `new` a 100 días → sin aviso; mensaje `read` a 340 días → sin aviso;
tenant sin mensajes nuevos pero con uno por vencer → el digest sale; `--dry-run` no envía.

## No tocar

La lógica de purga (`_purge_beyond_legal_cap`, `_purge_old_contacts`). El tope de 365 días.
Modelos y migraciones.

## DoD

- [ ] El cliente recibe el aviso con 30 días de margen (configurable).
- [ ] El correo no incluye datos personales de los remitentes.
- [ ] Cierre documental (`LEY-08`) y una línea en `Documentacion/SEGURIDAD.md` §3.
