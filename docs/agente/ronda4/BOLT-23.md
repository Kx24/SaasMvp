# BOLT-23 — `SEC-14`: salidas sin escapar (`mark_safe`) y JSON-LD

## Contexto verificado (2026-11-14)

`python -m bandit -r apps config -x "*/tests/*,*/migrations/*" -ll -q` reporta 21 avisos de
severidad media (12 `B308` uso de `mark_safe`, 9 `B703` posible XSS), todos en dos archivos:

- `apps/tenants/templatetags/seo_tags.py`: línea 155 (JSON-LD).
- `apps/website/templatetags/cloudinary_tags.py`: líneas 97, 101, 118, 161, 166, 203, 260, 264,
  302, 336, 353.

Los datos que llegan a esos tags los escribe el cliente desde su dashboard (títulos, textos
alternativos, nombres, datos de SEO): son entrada no confiable.

## Qué hacer

1. Tests nuevos primero, en `apps/website/tests/test_output_escaping.py`:
   - **JSON-LD:** un tenant cuyo nombre / descripción SEO contiene `</script><script>alert(1)</script>`
     renderiza una home donde ese texto **no** cierra el bloque `application/ld+json` (la
     secuencia `</script>` no aparece dentro del bloque; el JSON sigue siendo parseable con
     `json.loads` tras extraerlo).
   - **Tags de Cloudinary:** por cada tag público que hoy use `mark_safe`, un caso con
     `alt`/`title`/`class` que contenga `"><script>alert(1)</script>` y `" onerror="alert(1)`:
     la salida no contiene `<script>` ni un atributo `onerror` inyectado.
   Llama los tags vía `Template('{% load ... %}...').render(Context(...))`.
2. Revisa los 12 `mark_safe` uno por uno:
   - Si interpola datos variables: reemplaza por `format_html` / `format_html_join` /
     `conditional_escape` de modo que cada valor quede escapado. Para atributos armados desde un
     dict, escapa nombre y valor.
   - JSON-LD: serializa con `json.dumps` y escapa `<`, `>`, `&` como `<`, `>`,
     `&` antes de marcarlo seguro (o usa `django.utils.html.json_script` si calza con el
     `type="application/ld+json"`).
   - Si el contenido es 100 % estático o ya viene escapado por construcción, se puede mantener
     `mark_safe` con `# nosec B308 B703 — <razón concreta>` en esa línea. Esta card **sí autoriza
     `# nosec`**, pero solo con razón escrita y solo donde no hay dato variable sin escapar.
3. Corre bandit y confirma el resultado.

## No tocar

La firma pública de los tags (nombres, parámetros) ni el HTML que producen para entradas
normales: los templates existentes deben renderizar igual. Nada fuera de los dos archivos, salvo
los tests.

## Tests de rojo

`apps.website.tests.test_output_escaping`

## DoD

- [ ] `bandit -ll` en 0 avisos, o cada aviso restante con `# nosec` y razón en la línea.
- [ ] Los casos de inyección de los tests pasan y al menos uno fallaba antes. Si **ninguno**
      falla contra el código original (todo ya escapaba), no fuerces un rojo artificial: termina
      con `RESULTADO: BLOQUEADA — no hay rojo posible, las salidas ya escapaban`.
- [ ] Suite y Playwright verdes (se toca el render de todas las páginas).
- [ ] Cierre documental (`SEC-14`); en la línea del histórico, cuántos `mark_safe` se
      reemplazaron y cuántos quedaron justificados.
