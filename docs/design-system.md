# Sistema de diseño: contrato de tema y componentes compartidos

Paso 2 de `#AUD-11` (consolida `#AUD-11` + `#TOOL-04` + `#DS-01`/`#DS-02` — ver
`Documentacion/KANBAN_PROYECTO.md`). Este documento no migra nada: deja por
escrito el contrato que ya cumple el pipeline de build (Paso 1) y la regla de
componentes compartidos, para que la próxima vez que haga falta un tema nuevo
o un componente repetido, el camino correcto sea obvio.

## 1. Contrato de variables CSS (obligatorio en todo `base.html`)

Cada tema (`servelec`, `andesscale`, `ranchocachimba`, `themes/default`,
`themes/electricidad`) define, en un único bloque `:root` dentro de su
`base.html`, templado desde `ClientSettings`:

```css
:root {
    --color-primary:   {{ client.settings.primary_color|default:"#..." }};
    --color-secondary: {{ client.settings.secondary_color|default:"#..." }};
    --color-accent:    {{ client.settings.accent_color|default:"#..." }};
    --font-sans:       '{{ client.settings.font_family|default:"Inter" }}';
    --font-display:    '...';
}
```

`tailwind.config.js` (raíz del repo, compartido por todos los temas) referencia
estas variables directo — `colors.primary` es `var(--color-primary)`, no un
hex — así que un tenant nuevo con una paleta distinta no requiere tocar el
config ni recompilar nada especial, solo cambiar los valores en
`ClientSettings`.

Reglas duras (rompieron algo real, no son estilo):

- **Un solo bloque `:root` por página.** Antes de `#AUD-11` cada tema tenía la
  paleta duplicada dos veces — una en un `tailwind.config` JS inline, otra en
  un `:root` CSS aparte — y las dos copias no se referenciaban entre sí.
- **Nombres de fuente con comillas** dentro de `--font-sans`/`--font-display`
  (`'{{ ... }}'`, no `{{ ... }}` a secas) — un nombre con espacio rompe
  `font-family: var(--font-sans)` sin comillas.
- **Ningún comentario Django `{# ... #}` puede cruzar un salto de línea.**
  `django.template.base.tag_re` se compila sin `re.DOTALL`: un comentario
  multilínea no matchea como tag y Django lo dejaba como texto literal,
  visible en la página (`#BUG-01`, ver kanban). Partir en un `{# ... #}` por
  línea.
- **Sin `cdn.tailwindcss.com` ni `tailwind.config` inline.** El único link de
  CSS es `<link rel="stylesheet" href="{% static 'css/output.css' %}">`,
  compilado por `npm run build:css` (ver `tailwind.config.js` y `build.sh`).
- **Alpine.js con versión fijada** (`@3.16.2`), no `@3.x.x` flotante.

Un tema nuevo que no siga este contrato simplemente no va a heredar paleta ni
tipografía del tenant — el resto del sitio (componentes compartidos,
`components/navbar.html`, etc.) asume que estas variables existen.

## 2. Regla de componentes compartidos (`#RC-09`)

Antes de escribir un componente que podría repetirse en más de un tema:
revisar si ya existe una versión equivalente en 2+ temas. Si existe,
generalizarlo a `templates/components/` en vez de duplicarlo.

Dos mecanismos ya en uso — elegir según el caso, no inventar un tercero:

### a) Parámetro de modo + slots de override (el caso normal)

Precedente real: `templates/components/media_collection.html`. Un solo
componente compartido, con:

- **Un parámetro de modo** (`mode="slideshow"|"grid"`) que decide la
  estructura — no dos componentes casi idénticos por variante.
- **Slots de override opcionales, pasados como ruta de template**
  (`effects`, `overlay`, `theme_ctas`), no como bloques de contenido inline.
  Cada tema pasa su propio archivo (p. ej.
  `servelec/components/hero_overlay_theme.html`) o los deja vacíos para el
  comportamiento por defecto.

Consumido por `servelec/components/hero.html`, `andesscale/components/hero.html`
y `themes/default/components/hero.html` — cada uno un wrapper de ~10 líneas
que llama a `media_collection.html` con sus propios paths de override. Ese
wrapper por tema es aceptable: lo que no debe duplicarse es la lógica de
slideshow/grid en sí.

*(Nota: versiones anteriores de este documento y del kanban citaban "`hero`
con variante `layout: single|split`" como precedente — no existe tal
parámetro en el código; era una descripción inexacta del mecanismo real de
arriba. Corregido acá y en `CLAUDE.md`/kanban al escribir este Paso 2, tal
como pide su propio criterio de verificación.)*

### b) Excepción documentada, no generalizada (cuando el layout es distinto, no solo el estilo)

Precedente real: `ranchocachimba/components/hero.html` — hero de dos fotos
simultáneas lado a lado ("hero split"), estructuralmente distinto del
slideshow de `media_collection.html`. Deliberadamente **no** se forzó a
encajar en el componente compartido; el archivo lo dice explícito en su
propio comentario ("Específico de este theme — Servelec sigue con el
slideshow genérico... sin tocarse").

Regla: si la diferencia es de *estilo* (colores, tipografía, efectos) →
slot de override sobre el componente compartido (caso a). Si la diferencia
es de *estructura* (otra grilla, otro número de elementos, otra lógica) →
componente propio del tema, documentado igual de explícito que en este caso.
No hay una tercera opción de "generalizar con un flag más" — eso es lo que
ya pasó una vez con el `tailwind.config` duplicado y es el tipo de deuda que
`#AUD-11` vino a sacar, no a repetir en otro lugar.

## 3. Dónde se aplica esto

`#RC-09` (landing de Rancho Cachimba por componente, sección por sección) es
el primer trabajo real que va a ejercitar esta regla — antes de escribir cada
sección nueva (experiencias, el pastor, galería, cómo visitar, colegios),
revisar contra este documento primero.
