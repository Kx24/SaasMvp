# Ronda 11 — estado

Rama `agent/ronda11` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-56` | `COMP-02` | Ordenar el árbol de temas | ✅ DONE | 818 | 2.75 |
| `BOLT-57` | `COMP-01` | Componente cta compartido (1 de 7) | ✅ DONE | 822 | 0.63 |
| `BOLT-58` | `COMP-01` | Componente about compartido (2 de 7) | ✅ DONE | 826 | 0.66 |
| `BOLT-59` | `COMP-01` | Componente services compartido (3 de 7) | ✅ DONE | 830 | 0.62 |
| `BOLT-60` | `COMP-01` | Componente contact compartido (4 de 7) | ⏳ TODO |  |  |
| `BOLT-61` | `COMP-01` | Componente footer compartido (5 de 7) | ⏳ TODO |  |  |
| `BOLT-62` | `COMP-01` | Componente navbar compartido (6 de 7) | ⏳ TODO |  |  |
| `BOLT-63` | `COMP-01` | hero_ctas y hero_overlay_theme compartidos; cierre (7 de 7) | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-56`: Migración 0031: es solo de datos. Hay que ensayarla en una rama de Neon antes de desplegar. Cambia Client.template del tenant con slug PLATFORM_TENANT_SLUG, y la reversa devuelve a 'themes/default' todos los clientes con 'themes/andesscale'.
- `BOLT-56`: Carpetas y archivos borrados: templates/themes/electricidad/ completa (base.html, landing/home.html y 4 componentes), templates_library/ (2 .gitkeep) y themes/default/components/about.html y contact.html (vacíos).
- `BOLT-56`: Abrir la home de la plataforma en el navegador. Se verificó que el HTML sea idéntico a la fixture, pero la fixture se generó en este mismo cambio y no se puede comprobar que sea anterior al movimiento.
- `BOLT-56`: THEME_CHOICES ahora incluye 'themes/andesscale', y por eso aparece en el onboarding (apps/orders/forms.py, con la etiqueta 'Plataforma'). Confirmar que un cliente no pueda elegirlo, o que Plan.available_themes lo filtre.
- `BOLT-56`: test_docs_theme_choices.py excluye 'themes/andesscale' de la comparación con las guías de agente, una decisión del dev que el spec no cubría.
- `BOLT-56`: El cambio en tests/e2e/a11y.spec.js (esperar animaciones finitas antes de axe) quedó fuera del alcance de la card. No cambia umbrales ni selectores.
- `BOLT-57`: Revisar en el navegador la sección CTA en servelec (con y sin teléfono) y en andesscale. El tema base no usa cta, así que ahí solo hay que confirmar que no cambió.
- `BOLT-57`: Decisión del dev que el spec no cubría: no se dejaron envoltorios por la recursión del loader. Queda anotado en design-system.md como regla para los demás componentes de COMP-01.
- `BOLT-57`: El dev no corrió Playwright. Solo hay constancia del e2e del gate, que pasó.
- `BOLT-57`: La variante orbs conserva el comentario HTML de cabecera de andesscale porque tests_theme_tree.py lo compara con su fixture.
- `BOLT-58`: Revisar en el navegador la sección about en servelec, andesscale y el tema base. No hay cambios de HTML esperados salvo espacios y comentarios.
- `BOLT-58`: La variante stripe emite el comentario HTML 'ANDESSCALE' fuera del bloque condicional, para que apps.tenants.tests_theme_tree siga idéntico. Es un resto cosmético que habrá que limpiar luego.
- `BOLT-58`: Decisión del dev que el spec no cubría: no dejar envoltorios en los temas (el DoD permite 'o sin archivo').
- `BOLT-58`: Los textos de relleno ('Desarrollo ágil', 'Confianza', '5+', '100%') siguen visibles al cliente en la variante stripe.
- `BOLT-59`: Revisar en el navegador la sección Servicios en Servelec y andesscale (renderizado, grilla de 4/5 columnas, panel de detalle).
- `BOLT-59`: Confirmar que el tema base (default) no cambió: su home renderiza en línea y ya no tiene services.html.
- `BOLT-59`: El normalizador del test colapsa espacios dentro de class="..." y quita comentarios HTML. Las únicas diferencias aceptadas son de espacios y comentarios, y servelec tenía atributos multilínea con espacios sobrantes.
- `BOLT-59`: La decisión de no dejar envoltorios en los temas la tomó el dev. El spec ofrecía envoltorio fino o sin archivo, así que está dentro del DoD.

## Hallazgos incidentales

- `BOLT-56`: themes/servelec/components/stats.html usa rgba(255,255,255,0.5) sobre #0f3320, con contraste estimado ~4,4:1 (cálculo manual, sin medir), cerca del mínimo AA de 4,5:1. No se tocó porque cambiaría el aspecto del sitio.
- `BOLT-56`: Dos tests de smoke de formularios de contacto fallaron con --repeat-each=4. El dev supone que es el límite anti-spam por email repetido y no lo comprobó. Una corrida normal pasa los 14 tests.
- `BOLT-56`: El dev no comprobó si el flake de a11y de Servelec ocurre también en el código original.
- `BOLT-56`: Líneas de CLAUDE.md que quedaron desfasadas: la mención a templates/{tema} como ruta de andesscale, y el texto que lista los temas sin themes/andesscale. Esta card no toca CLAUDE.md.
- `BOLT-56`: Comentarios obsoletos que citan themes/electricidad en apps/website/tests/test_contact_submit.py, apps/website/tests/test_navbar_cta.py y static/css/input.css.
- `BOLT-57`: La variante glow mantiene style="" inline y colores hardcodeados de servelec (#0b2818, #1DB954, etc.). Falta migrarlos a tokens y utilidades Tailwind, y no hay fila en el kanban para eso.
- `BOLT-57`: El test test_theme_files_do_not_repeat_shared_markup no comprueba nada mientras no existan archivos de tema, porque los salta. El rojo real sale del test de existencia del compartido y del de 15 líneas.
- `BOLT-58`: La variante blocks conserva style="" inline y colores hardcodeados de servelec (#0f3320, #1DB954) para no alterar el HTML. Es la misma deuda que en cta y va contra la preferencia Tailwind.
- `BOLT-58`: El test Playwright del formulario multi-step de andesscale falló una vez por timeout y pasó en las dos corridas siguientes; parece intermitente y no toca about.
- `BOLT-58`: El informe del dev admite que no corrió el rojo contra HEAD. Lo confirma red_check del gate: 3 tests estructurales fallan contra el código original.
- `BOLT-59`: themes/default/components/services.html era huérfano (su home renderiza la sección en línea); se borró como código muerto.
