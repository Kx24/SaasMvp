# BOLT-81 — `MOD-01` parte 1a de 3: modelo `MediaAsset` y embeds de video

> Primera de dos cards de la parte 1 (`BOLT-81` modelo, `BOLT-82` subida firmada). **Sin UI**: la
> grilla multiarchivo es la parte 2 y la migración de las imágenes existentes es la parte 3.
> Nada de lo que ve hoy un visitante o un cliente debe cambiar.

## Decisiones del dueño (2026-11-22)

- Video **solo como embed** de YouTube o Vimeo. Nada de video subido a Cloudinary.
- Límite del plan **por cantidad de archivos**, con un tope técnico por peso (ese tope lo aplica
  `BOLT-82`).
- `MOD-00` opción A: el sitio se compone por bloques. No hay page-builder.

## Contexto verificado (2026-11-22)

- `apps/website/models.py::GalleryItem` (~línea 438) ya es "el pool único del tenant"
  (`DEUDA-02` fase 1), pero cada ítem pertenece a una `section` o a un `service`, y solo guarda
  imágenes. `MediaAsset` es la **biblioteca** del tenant, sin dueño: en la parte 3, `GalleryItem`,
  `Section.image`/`background_image` y `Service.image` pasarán a apuntar a ella. **En esta card no
  toques `GalleryItem` ni esos campos.**
- Registro de módulos: `apps/tenants/modules.py` (`Module`, `MODULES`, `limit_for`, `usage_for`,
  `check_limit`, `ModuleLimitReached`). La galería usa `limit_field='max_images'`.
- Helpers de Cloudinary: `apps/core/cloudinary_utils.py` (`cloudinary_upload_path`,
  `get_cloudinary_folder`, `get_cloudinary_url`, que acepta un `CloudinaryField`, un
  `CloudinaryResource` o un `public_id` en texto). No armes URLs de Cloudinary a mano.
- Aislamiento: `TenantAwareManager` **no** filtra solo. Toda consulta va con
  `.filter(client=...)` o `for_client(...)` (ver `CLAUDE.md`).

## Qué hacer

1. **Modelo `MediaAsset`** en `apps/website/models.py`, con migración en `apps/website/migrations/`:
   - `client` (FK a `tenants.Client`, `CASCADE`, `related_name='media'`).
   - `kind`: `image` o `embed`.
   - `image`: `CloudinaryField` con `folder=cloudinary_upload_path('media')`, `blank=True`, `null=True`.
     Agrega `'media'` a la lista de categorías de `cloudinary_utils.py` si existe esa lista.
   - Para embeds: `provider` (`youtube` / `vimeo`, en blanco si es imagen) y `video_id`. **Se guarda
     el ID, nunca la URL ni el HTML que pegó el usuario.**
   - Metadatos: `title` (opcional), `alt_text` (opcional, para accesibilidad), `bytes`, `width`,
     `height` y `format` (enteros/texto en blanco permitidos; los llena `BOLT-82`), `uploaded_by`
     (FK a `User`, `SET_NULL`, `null=True`), `created_at`, `is_active` (default `True`).
   - `clean()`: un `image` exige `image` y nada de `provider`/`video_id`; un `embed`, lo contrario.
   - `objects = TenantAwareManager()` si los demás modelos del archivo lo usan.
   - Índice por `(client, kind, created_at)`.
   - Métodos: `embed_url()` → `https://www.youtube-nocookie.com/embed/<id>` o
     `https://player.vimeo.com/video/<id>?dnt=1`; `thumbnail_url()` → para YouTube
     `https://img.youtube.com/vi/<id>/hqdefault.jpg`, para Vimeo `None` (requiere su API), para una
     imagen `get_cloudinary_url(self.image, 'thumbnail')`.
2. **Parser de embeds**, función pura `parse_video_url(url) -> (provider, video_id)` (en
   `apps/website/media.py` o junto al modelo). Acepta solo:
   - YouTube: `youtube.com/watch?v=ID`, `youtu.be/ID`, `youtube.com/shorts/ID`,
     `youtube.com/embed/ID`, con o sin `www.` o `m.`, con parámetros extra (`&t=30s`, `?si=…`). El ID
     cumple `^[A-Za-z0-9_-]{11}$`.
   - Vimeo: `vimeo.com/ID` y `player.vimeo.com/video/ID`, con ID numérico.
   - Solo `http`/`https`, host exacto en la lista (nada de `youtube.com.evil.test`). Cualquier otra
     cosa lanza `ValidationError` con un mensaje en español para el usuario.
3. **Módulo en el registro** (`apps/tenants/modules.py`): `Module(key='media', label='Medios',
   flag=None, limit_field='max_images', usage=<cuenta MediaAsset kind='image' del cliente>,
   limit_noun='archivos', url_names=())`, sin entradas de menú. Las rutas llegan en `BOLT-82`.
   - **Los embeds no cuentan para el límite** (no son archivos). Para que nadie llene la base, un
     tope técnico fijo de embeds por tenant: `MEDIA_MAX_EMBEDS = 200`, en `config/settings/base.py`.
   - `max_images` lo usan ahora la galería y los medios a la vez. Es a propósito y transitorio: en la
     parte 3 la galería pasará a usar el pool. **No cambies cómo se cuenta la galería.**
4. **Admin**: registra `MediaAsset` siguiendo el patrón de los admins de `apps/website/admin.py`
   (incluido el scope por tenant de `SEC-05b`, si los demás lo tienen). Solo lectura de los
   metadatos.

## Tests de rojo

`apps.website.tests.test_media_asset` (archivo nuevo). Debe fallar contra el código actual:

- `parse_video_url`: cada forma válida de YouTube y Vimeo devuelve `(provider, id)`; rechaza otro
  host, un host parecido (`youtube.com.evil.test`), `javascript:`, un ID con longitud o caracteres
  inválidos, y un texto que no es URL.
- `MediaAsset.clean()` rechaza un `image` sin imagen, un `embed` sin `video_id` y las mezclas.
- `embed_url()` y `thumbnail_url()` dan las URLs esperadas.
- `usage_for(client, 'media')` cuenta solo las imágenes de ese cliente: no los embeds ni las de
  otro tenant.

Sin red: no hace falta Cloudinary para estos tests; si `get_cloudinary_url` lo pidiera, parchéalo.

## No tocar

`GalleryItem`, `Section`, `Service`, las 6 subidas actuales del dashboard (`views/branding.py`,
`gallery.py`, `sections.py`, `services.py`) y `admin.py` salvo para registrar `MediaAsset`, los
templates, `max_images` y su conteo de galería.

## DoD

- [ ] `MediaAsset` existe con su migración, `makemigrations --check` limpio.
- [ ] `parse_video_url` acepta solo YouTube y Vimeo y guarda el ID.
- [ ] El módulo `media` está en el registro y su uso cuenta solo imágenes del tenant.
- [ ] Ningún template ni vista existente cambió.
- [ ] Cierre documental: `MOD-01` se **acota** (parte 1a hecha). Anota `MOD-01 (parte)` en el
      histórico.
