# LinkRevisar — Rancho Cachimba

> Referencias de diseño para Rancho Cachimba. Ninguna referencia entra al diseño sin pasar por aquí — ver convención en `Planificación/Kanban_RanchoCachimba.md`.
> Ruta real: `Documentacion/LinkRevisar.md` (el Kanban original proponía `Documentacion/clientes/rancho-cachimba/LinkRevisar.md`; se mantiene acá, ver nota en el Kanban).
> Cards que lo consultan y actualizan: `#RC-04` · `#RC-06` · `#RC-07` · `#RC-09` · `#RC-19`.

| Link | Qué se toma | Aplica a | Estado |
|---|---|---|---|
| `https://www.deere.com/latin-america/es/tractores/` | Fotografía real (no ilustración): plano general de campo + foto de producto/detalle limpia. Verde oscuro + tierra + blancos neutros de navegación — coincide con la paleta oficial ya cargada (`#RC-03`). | `components/hero.html`, `components/services.html` | ✅ aprobado |
| Tartán escocés — paleta propia, sin imágenes (decisión ya tomada, sin URL) | Textura, no color: 4 `repeating-linear-gradient` con los hex de marca (`#064B20` × `#0B642B` × `#6B4F32`, hilo `#FFD500`). CSS puro, exportable como patrón para redes. | `components/hero.html` (costura entre las dos fotos) | ✅ aprobado e implementado (`#RC-06`) |
| `https://www.morphicons.com/` | Transición animada entre ícono de menú (☰) y cierre (✕) en el toggle mobile, trazo fino consistente con el resto del navbar. | `components/navbar.html` (toggle menú móvil) | 🟡 por revisar — agrega una dependencia JS nueva; evaluar si vale la pena en esta etapa o queda para Etapa 2 |
| *Babe* (película, 1995) — sin URL | Tono cálido y honesto de granja, sin golpe de efecto. Falta precisar si aplica a tratamiento de fotografía, a copy, o a ambos. | Por definir | 🟡 por revisar — falta que el usuario precise el componente exacto |
| Afiche de sheepdog trials — sin URL | Composición/tipografía de afiche de competencia: tono editorial, de autoridad. | Sección del pastor (`#RC-10`, Etapa 2) | 🟡 por revisar — falta encontrar/adjuntar el afiche concreto de referencia |
| `https://www.behance.net/` | — | — | ❌ descartado — enlace genérico a la plataforma, no a un proyecto puntual. No cumple "la idea específica, no me gusta" (regla del Kanban). Si había un proyecto puntual en mente, agregar su URL directa. |
| `https://impeccable.style/` | Vocabulario de comandos de diseño para trabajar con Claude Code (`/polish`, `/audit`, `/typeset`...) — no es una referencia visual del sitio. | No aplica a ningún componente del tema | ❌ descartado de esta tabla — es una referencia de *proceso*, no de diseño visual. Candidato a `Kanban_Plataforma_v2.md` → `#TOOL-04` si se quiere adoptar como herramienta, no como look del sitio. |
| `https://github.com/ryanthedev/design-for-ai` | Plugin de metodología de diseño para agentes de IA (research → plan → mock → build) — no es una referencia visual del sitio. | No aplica a ningún componente del tema | ❌ descartado de esta tabla — mismo motivo que `impeccable.style`: proceso, no visual. Candidato a `#TOOL-04`. |

---

## Notas

- **Dos referencias no eran de diseño visual** (`impeccable.style`, `design-for-ai`): son herramientas/metodología para construir *con* IA, no ejemplos de cómo debe verse Rancho Cachimba. Se dejan registradas acá con el motivo del descarte (regla del Kanban: "lo descartado se queda, con el motivo") en vez de borrarlas, y quedan como pie para `#TOOL-04` (design system / librería de componentes) en `Kanban_Plataforma_v2.md`.
- **`behance.net` quedó descartado por genérico** — si el usuario tenía un proyecto puntual en mente, hay que reemplazar la entrada con esa URL específica.
- **`Babe` y el afiche de sheepdog trials** se registran sin URL porque no se proporcionó una — quedan como placeholder "por revisar" hasta tener el enlace/imagen concreto y el componente exacto al que aplican.
