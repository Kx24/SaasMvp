# BOLT-38 — `CONS-11` (parte 3 de 4): cobertura de `core` y servicios de `tenants`

## Contexto verificado (2026-11-15)

- Contrato: total ≥ 70 %. Hoy 65,04 % (5.329 sentencias, 1.863 sin cubrir). Faltan unas 270
  sentencias cubiertas; esta card y la siguiente se las reparten.
- Huecos de esta card (sentencias sin cubrir):
  `apps/core/cloudinary_utils.py` 126 de 191 (34 %),
  `apps/tenants/services/email_dispatcher.py` 56 de 105 (47 %),
  `apps/tenants/templatetags/tenant_tags.py` 41 de 62 (34 %),
  `apps/website/templatetags/website_tags.py` 48 de 166 (71 %),
  `apps/website/templatetags/cloudinary_tags.py` 22 de 94 (77 %).

## Qué hacer

1. `cloudinary_utils.py`: tests **sin red** (parchea `cloudinary.uploader` / `cloudinary.api` /
   `cloudinary.utils` con `unittest.mock`). Cubre `get_cloudinary_url` por preset y con
   transformaciones, `get_srcset_urls`, `upload_to_cloudinary` (éxito, error del SDK, carpeta
   `tenants/{slug}/…`), borrado y el resto de funciones públicas del módulo, incluidos los casos
   de entrada vacía o `None`.
2. `email_dispatcher.py`: envío con la configuración SMTP del tenant, fallback a la global,
   error de conexión, tenant sin `ClientEmailSettings`. Usa `django.core.mail` con el backend
   `locmem` y `mock` para el SMTP; nada sale a la red.
3. `tenant_tags.py`, `website_tags.py`, `cloudinary_tags.py`: renderiza plantillas mínimas con
   `Template(...).render(Context(...))` y afirma el HTML resultante; cubre las ramas sin tenant,
   con flag apagado y con datos vacíos.
4. Tests de comportamiento con aserciones reales. Bug real destapado: se arregla y se reporta.
5. Al final, con todo verde: `python scripts/gatekeeper.py --strict --update-baseline`.

## No tocar

Código de producción salvo bug demostrado. `COVERAGE_OMIT`, `# pragma: no cover`. Los comandos de
gestión con 0 % (`audit_cloudinary_assets`, `check_cloudinary`, `create_tenant`…) quedan para la
card siguiente.

## DoD

- [ ] `total` sube al menos 3 puntos respecto del baseline de entrada; `orders` y `tenants_core`
      no bajan.
- [ ] Ningún test hace red.
- [ ] Cierre documental: `CONS-11` **parcial**. En `revisar_humano`: porcentajes antes y después.
