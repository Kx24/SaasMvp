# BOLT-78 — `SEC-19`: rutas con `../` en `tenant_static` y `get_tenant_media_url`

## Decisión del dueño (2026-11-22)

Se rechazan las rutas que salgan del directorio del tenant.

## Contexto verificado (2026-11-22)

- `apps/tenants/templatetags/tenant_tags.py`: `tenant_static` (~línea 39) y `get_tenant_media_url`
  (~línea 79) arman `Path(settings.MEDIA_ROOT) / 'tenants' / client.slug / str.__str__(path)` y
  llaman `.exists()`. Con `'../otro/x.png'` se sondea fuera de `MEDIA_ROOT/tenants/<slug>/`.
- `str.__str__` está a propósito: `path` llega como `SafeString` y `Path / SafeString` lanza
  `TypeError` en Python 3.11 (el de la CI). **No lo cambies por `str()`**, que devuelve el mismo
  `SafeString`.
- `tenant_media` arma una URL sin tocar el disco; aplícale el mismo criterio solo si es barato.

## Qué hacer

1. Un helper privado que resuelva la ruta (`.resolve()`) y compruebe que queda dentro del directorio
   del tenant (`is_relative_to` o comparación de `parents`). Si sale, se comporta como "no existe":
   `tenant_static` cae al fallback de `STATIC_URL` y `get_tenant_media_url` devuelve lo mismo que
   para un archivo inexistente.
2. Rechaza también rutas absolutas.

## Tests de rojo

`apps.tenants.tests_tenant_tags_traversal` (archivo nuevo): con un archivo real fuera del directorio
del tenant (en un `MEDIA_ROOT` temporal), `{% tenant_static '../otro/x.png' %}` no devuelve la URL
de media sino el fallback; lo mismo con `get_tenant_media_url`. Debe fallar contra el código actual.
Usa `SimpleTestCase` y `override_settings`, como `apps/website/tests/test_template_tags.py`.

## No tocar

Los otros tags, `MEDIA_URL` y `STATIC_URL`.

## DoD

- [ ] Ningún tag del archivo revela archivos fuera de `MEDIA_ROOT/tenants/<slug>/`.
- [ ] Los 49 tests de `apps.website.tests.test_template_tags` siguen en verde.
- [ ] Cierre documental: borra la fila `SEC-19` y agrega la línea al histórico.
