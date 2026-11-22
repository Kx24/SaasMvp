# BOLT-75 — `DEUDA-16`: quitar `TenantSectionsSitemap` del sitemap

## Decisión del dueño (2026-11-22)

Se quita. Las secciones (hero, about, contact) son bloques de la home, no páginas con URL propia;
no se inventan vistas `section_detail` para llenar el sitemap.

## Contexto verificado (2026-11-22)

- `apps/marketing/sitemaps.py`: `TenantSectionsSitemap` (~línea 83) filtra por `Section.slug`,
  campo que no existe, y apunta a `website:section_detail`, ruta que no existe; un `except` lo
  oculta y `/sitemap-sections.xml` sale vacío.
- `apps/marketing/views_sitemap.py`: `get_tenant_sitemaps` devuelve `{"pages", "sections"}`; el
  docstring de `tenant_sitemap_section` dice "(pages, sections)". `/sitemap.xml` usa
  `tenant_sitemap_simple`, que junta todos los sitemaps.
- Tests existentes que la mencionan: `apps/marketing/tests_seo_views.py` (importa la clase, afirma
  `{'pages', 'sections'}` en la línea ~94 y tiene `test_sections_sitemap_*` hacia la ~117-127).

## Qué hacer

1. Borra la clase `TenantSectionsSitemap` y su entrada en `get_tenant_sitemaps`; actualiza el
   docstring.
2. Actualiza los tests de `tests_seo_views.py`: borra los de la clase y cambia la aserción a
   `{'pages'}`. **No debilites** ninguna otra aserción.
3. `TenantStaticSitemap`, `/sitemap.xml`, `/robots.txt` y la verificación de Search Console no deben
   cambiar de comportamiento. Si `robots.txt` o alguna plantilla enlaza `sitemap-sections.xml`,
   quítalo.

## Tests de rojo

`apps.marketing.tests_sitemap_sin_secciones` (archivo nuevo): `get_tenant_sitemaps` devuelve solo
`pages`; `sitemaps.py` ya no expone `TenantSectionsSitemap`; `GET /sitemap-sections.xml` responde
404 en un tenant con dominio válido. Debe fallar contra el código actual.

## No tocar

`TenantStaticSitemap`, modelos de `website`, migraciones.

## DoD

- [ ] El sitemap solo expone `pages`; `/sitemap-sections.xml` da 404.
- [ ] Tests de SEO actualizados y en verde, cobertura total no baja.
- [ ] Cierre documental: borra la fila `DEUDA-16` y agrega la línea al histórico.
