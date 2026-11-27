# BOLT-82 — `MOD-01` parte 1b de 3: subida directa firmada a Cloudinary y alta de embeds

> Segunda card de la parte 1. Depende de `BOLT-81` (`MediaAsset`, `parse_video_url`, módulo
> `media`). **Sin UI**: son tres endpoints JSON que consumirá la grilla de la parte 2.

## Decisiones del dueño (2026-11-22)

Video solo como embed. Límite por cantidad de archivos (`max_images`), con un tope técnico por peso.

## Cómo funciona la subida firmada

El navegador pide una firma al servidor, sube el archivo **directo a Cloudinary** (el archivo no
pasa por Render) y avisa al servidor qué subió. El servidor **no confía** en ese aviso: consulta a
Cloudinary con su API y recién entonces crea el `MediaAsset`.

## Contexto verificado (2026-11-22)

- Decoradores del dashboard: copia la pila de `gallery_item_add` en
  `apps/website/views/gallery.py` (~línea 67): `@tenant_permission_required('edit_content')` +
  `@module_required(...)`, con `module_required('media')`. Mira también si esa vista lleva
  `@require_POST` o equivalente.
- Rate limit: `apps/core/rate_limit.py::RateLimiter(request, scope, limit, period)` (uso en
  `apps/website/auth_views.py` ~29).
- Límite: `check_limit(client, 'media')` lanza `ModuleLimitReached`; su `.message` es el texto para
  el usuario.
- Rutas del dashboard: `apps/website/urls.py` (p. ej. `dashboard/gallery/add/`).
- Helpers: `apps/core/cloudinary_utils.py` (`get_cloudinary_folder`, `delete_from_cloudinary`).
  La firma se arma con `cloudinary.utils.api_sign_request`; la consulta, con
  `cloudinary.api.resource(public_id)`.

## Qué hacer

Tres vistas en `apps/website/views/media.py`, en `url_names` del módulo `media` y con nombre en
`apps/website/urls.py`. Todas exigen POST, sesión de un miembro del tenant con `edit_content` y CSRF.

1. **`media_upload_signature`** (`dashboard/media/firma/`):
   - Rate limit: 30 firmas por 10 minutos por tenant e IP.
   - Si `check_limit(client, 'media')` falla: 403 con `{"error": <mensaje>}`.
   - El servidor fija **todos** los parámetros firmados; del navegador no se toma ninguno:
     `folder = get_cloudinary_folder(client.slug, 'media')`, `public_id` = un `uuid4().hex`,
     `timestamp`, `allowed_formats = "jpg,jpeg,png,webp,heic"`.
   - Responde `{"signature", "timestamp", "api_key", "cloud_name", "folder", "public_id",
     "allowed_formats", "upload_url"}`. **Nunca `api_secret`.**
2. **`media_upload_confirm`** (`dashboard/media/confirmar/`), recibe `public_id`:
   - Rechaza (400) un `public_id` que no empiece con la carpeta del tenant. Así un tenant no puede
     registrar un archivo de otro.
   - Consulta `cloudinary.api.resource(public_id)`. Si no existe: 400.
   - Tope técnico: `bytes` hasta `MEDIA_MAX_IMAGE_MB` (nuevo setting en `config/settings/base.py`,
     **10**) y `format` dentro de los permitidos. Si no cumple: borra el archivo con
     `delete_from_cloudinary`, y 400 con un mensaje claro.
   - Vuelve a llamar a `check_limit` (otra pestaña pudo subir mientras tanto). Si falla: borra el
     archivo y 403.
   - Idempotente: un `public_id` ya registrado devuelve el asset existente, sin duplicar.
   - Crea `MediaAsset(kind='image', ...)` con `bytes`, `width`, `height` y `format` de la respuesta
     de Cloudinary y `uploaded_by=request.user`. Responde 201 con `id`, `kind` y `thumbnail_url`.
3. **`media_embed_add`** (`dashboard/media/embed/`), recibe `url`:
   - `parse_video_url`; un error de validación da 400 con su mensaje.
   - Tope `MEDIA_MAX_EMBEDS`: si ya se alcanzó, 403.
   - Un mismo `(provider, video_id)` en el mismo tenant no se duplica: devuelve el existente.
   - Responde 201 con `id`, `kind`, `embed_url` y `thumbnail_url`.

## Tests de rojo

`apps.website.tests.test_media_upload` (archivo nuevo). Sin red: parchea
`cloudinary.utils.api_sign_request`, `cloudinary.api.resource` y `delete_from_cloudinary`. Debe
fallar contra el código actual.

- **Firma:** devuelve la carpeta del tenant y un `public_id` generado por el servidor, y la respuesta
  no contiene `api_secret`; ignora un `folder` enviado por el navegador; 403 al alcanzar el límite;
  429 (o el código que use `RateLimiter` en el resto del repo) al pasar el rate limit.
- **Confirmar:** crea el asset con los metadatos de Cloudinary; rechaza un `public_id` de la carpeta
  de **otro tenant**; rechaza y borra un archivo de más de 10 MB y un formato no permitido; es
  idempotente; 403 y borrado si el límite se alcanzó entre la firma y la confirmación.
- **Embed:** crea con una URL válida, rechaza una inválida, no duplica, respeta el tope.
- **Acceso:** anónimo → login; usuario de otro tenant → rechazado (`tenant_member_required`); rol
  sin `edit_content` → rechazado; GET → 405.

## No tocar

Las 6 subidas actuales del dashboard (las unifica la parte 3), `GalleryItem`, templates, el menú del
dashboard, `render.yaml`. Sin dependencias nuevas: `cloudinary` ya está en `requirements.txt`.

## DoD

- [ ] Tres endpoints POST con aislamiento por tenant, límite del plan, tope de peso y rate limit.
- [ ] El servidor nunca confía en el navegador: carpeta y `public_id` los fija él, y verifica en
      Cloudinary antes de crear.
- [ ] `api_secret` no sale nunca en una respuesta.
- [ ] Cierre documental: `MOD-01` se **acota** (parte 1 completa: queda UI multiarchivo y
      migración). Anota `MOD-01 (parte)` en el histórico.
- [ ] En `revisar_humano`: "Probar a mano en desarrollo la subida real a Cloudinary con un archivo
      del teléfono (HEIC incluido) antes de la parte 2; los tests la simulan".
