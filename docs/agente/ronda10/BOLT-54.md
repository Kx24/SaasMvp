# BOLT-54 — `BIZ-01`: límites del plan con efecto real

## Contexto verificado (2026-11-15)

- `Client.max_images` (default 100), `Client.max_services` (default 20) y `Client.max_pages`
  (default 10) existen (`apps/tenants/models.py:88-90`) y **nada los verifica** al crear
  contenido. `Plan` (`apps/orders/models.py:111-116`) tiene `max_services` y `max_images`, que el
  onboarding copia al `Client` (verifícalo en `views_onboarding.py`).
- La galería ya tiene un tope propio: `ClientSettings.gallery_images_limit`
  (`views/gallery.py:57`, `gallery_at_limit`).
- `BOLT-52` declaró `limit_field` por módulo en `apps/tenants/modules.py`
  (`services` → `max_services`, `gallery` → `max_images`).
- No existe un modelo de "páginas": `max_pages` no tiene a qué aplicarse.

## Qué hacer

1. En `apps/tenants/modules.py`: cada módulo con `limit_field` declara cómo contar su uso
   (un callable `usage(client) -> int`, por ejemplo servicios del tenant; imágenes de galería del
   tenant). Funciones `limit_for(client, key) -> int | None`, `usage_for(client, key) -> int` y
   `check_limit(client, key) -> None` que lanza `ModuleLimitReached(module, limit)` si
   `usage >= limit`. Un límite `0` o negativo se trata como "sin cupo"; `None` = sin límite.
2. **Galería:** el tope efectivo es el menor entre `ClientSettings.gallery_images_limit` y
   `Client.max_images`. Unifica el cálculo (`gallery_at_limit` pasa a usar el registro).
3. **Aplicación:** `create_service` y `gallery_item_add` (y cualquier otra vista que cree un
   servicio o una imagen de galería: búscalas) llaman a `check_limit` antes de crear. Al tope:
   no se crea nada y el usuario ve un mensaje claro, por el mismo mecanismo que la vista ya usa
   para sus errores (`messages` o JSON): "Tu plan permite N servicios. Borra uno o pide una
   ampliación." Editar y borrar nunca se bloquean.
4. La interfaz muestra el uso junto al botón de crear ("12 de 20") y deshabilita el botón al
   tope. Utilidades Tailwind; sin estilos en línea.
5. El admin (`/superadmin/`) no se limita: el superuser puede crear por encima del tope.
6. `max_pages`: no lo apliques. Repórtalo en `hallazgos` (campo sin uso) y agrega una fila
   `DEUDA` en el kanban para decidir si se borra.

## Tests de rojo

`apps.tenants.tests_module_limits` (archivo nuevo con ese nombre exacto). Casos: con
`max_services=2` y 2 servicios, `create_service` no crea y devuelve el mensaje; con 1 servicio sí
crea; lo mismo con la galería y `max_images`; el tope efectivo de la galería es el menor de los
dos; editar y borrar funcionan al tope; el conteo es por tenant (los servicios de otro tenant no
cuentan); `limit_for` de un módulo sin límite es `None`.

## No tocar

`Plan` y el checkout. Los valores por defecto de los límites. Migraciones (no hacen falta).

## DoD

- [ ] Servicios e imágenes de galería respetan el plan, con mensaje claro y uso visible.
- [ ] Ningún tenant existente pierde contenido ni queda bloqueado para editar.
- [ ] Playwright verde.
- [ ] Cierre documental (`BIZ-01`). En `revisar_humano`: revisar en producción que ningún
      cliente actual esté ya por encima de su límite (comando o consulta sugerida).
