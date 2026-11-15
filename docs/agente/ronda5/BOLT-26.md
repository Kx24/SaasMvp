# BOLT-26 — `LEY-03` (resto): tope legal de conservación para mensajes de contacto

## Contexto verificado (2026-11-14)

`apps/tenants/management/commands/send_contact_digest.py`: `_purge_all` (línea 272) recorre los
tenants activos con `settings__auto_purge_enabled=True` y `_purge_old_contacts` (línea 293) borra
los `ContactSubmission` más viejos que `inbox_retention_days` (mínimo 7) **solo** si están
`read`/`replied` o son spam (líneas 306–308). Un mensaje `new` no se borra nunca, y un tenant con
la purga apagada conserva todo para siempre. La Ley 21.719 (art. 14 d, proporcionalidad) no
admite conservación indefinida.

## Decisión del dueño (2026-11-14)

**Los mensajes `new` antiguos también se purgan.** Regla:

- Tope duro de **365 días** para todo `ContactSubmission`, cualquiera sea su estado, en **todo
  tenant activo, tenga o no `auto_purge_enabled`** (es un máximo legal, no una preferencia).
- El plazo vive en un setting: `CONTACT_MAX_RETENTION_DAYS = 365` en `config/settings/base.py`.
- La purga existente por `inbox_retention_days` (leídos/respondidos/spam, solo con
  `auto_purge_enabled`) no cambia.

## Qué hacer

1. Tests en un archivo **nuevo**, `apps/tenants/tests_contact_purge.py` (no edites los tests de
   purga que dejó `BOLT-14`; puedes mirarlos para armar los datos):
   - Mensaje `new` de 366 días → se borra; de 364 días → se conserva.
   - Tenant con `auto_purge_enabled=False`: mensajes de más de 365 días (cualquier estado) se
     borran; los de menos, no.
   - Tenant inactivo: no se toca.
   - `--dry-run` no borra nada y reporta la cantidad.
   - `override_settings(CONTACT_MAX_RETENTION_DAYS=30)` cambia el tope.
   - Borrar en el tenant A no toca al tenant B.
   (`created_at` es `auto_now_add`: para fechar un mensaje en el pasado usa
   `ContactSubmission.objects.filter(pk=...).update(created_at=...)`.)
2. Implementa el tope como un paso separado dentro de `_purge_all` (método propio, por ejemplo
   `_purge_beyond_legal_cap`), que corre para todos los tenants activos antes de la purga por
   preferencia. Registra en el log la cantidad por tenant, **sin datos personales** (regla de
   `BOLT-12`).
3. El digest informa esa purga igual que la existente (usa `purge_info`).
4. `Documentacion/SEGURIDAD.md` §3: actualiza el estado del art. 14 d con el tope de 365 días.

## No tocar

Plazos de `Order`, `PaymentLog`, `EmailOutbox`: siguen pendientes de decisión. En el cierre
documental **acota** la fila `LEY-03` del kanban a eso + "plazo publicado en la política" +
"cron en Render (`OPS-06`)"; no la borres.

## Tests de rojo

`apps.tenants.tests_contact_purge`

## DoD

- [ ] Ningún `ContactSubmission` de un tenant activo sobrevive más de `CONTACT_MAX_RETENTION_DAYS`.
- [ ] Purga por preferencia sin cambios (sus tests siguen verdes sin tocarlos).
- [ ] Cierre documental (fila `LEY-03` acotada, línea en el histórico).
