# Ronda 5 — estado

Rama `agent/ronda5` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-24` | `SEC-05b` | Restos de alcance por tenant en el admin | ⛔ BLOCKED |  | 0 |
| `BOLT-25` | `DEUDA-06` | Código muerto | ✅ DONE | 313 | 0.39 |
| `BOLT-26` | `LEY-03` | Tope legal de 365 días para mensajes de contacto | ✅ DONE | 320 | 0.57 |
| `BOLT-27` | `SEC-10` | Dependencias al día y pip-audit | ❌ REJECTED |  | 0.57 |
| `BOLT-28` | `CONS-06` | Camino único para objetos del tenant | ✅ DONE | 325 | 0.48 |
| `BOLT-29` | `CONS-07` | Separar views.py por área | ✅ DONE | 329 | 0.66 |
| `BOLT-30` | `SEC-12` | Integración continua con el gate | ✅ DONE | 333 | 0.34 |
| `BOLT-31` | `CONS-02` | Documentación al día | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-25`: Que borrar cloudinary_settings.py (CLOUDINARY_DEFAULT_LIMITS y CLOUDINARY_ALERT_THRESHOLDS) sea aceptable: OPS-04 los necesitará, aunque estaban sin uso.
- `BOLT-25`: Que la fila de DEUDA-06 se haya movido a la tabla del histórico en vez de dejarla como viñeta.
- `BOLT-25`: Documentación todavía desactualizada en README.md y MASTER_PLAN_Y_ARQUITECTURA.md (hallazgo sin card en el kanban).
- `BOLT-26`: Hay un cambio de comportamiento destructivo en producción: los mensajes new sin leer de más de 365 días se borrarán, incluso en tenants con la purga apagada. La decisión es del dueño, pero conviene que lo confirme al mergear.
- `BOLT-26`: La purga solo corre cuando se ejecuta send_contact_digest. Sin el cron de OPS-06 en Render no se ejecuta en producción.
- `BOLT-26`: El plazo de 365 días todavía no está publicado en la política de privacidad (sigue pendiente en LEY-03).
- `BOLT-26`: El texto visible al cliente en el digest es nuevo: «Se eliminaron N mensajes con más de 365 días (plazo máximo de conservación)».
- `BOLT-28`: Confirmar que la guardia estática solo mira views.py (o el paquete views/) y no los templatetags, que contienen un .objects.get(.
- `BOLT-28`: gallery_item_add, gallery_item_edit y gallery_item_delete consultan GalleryItem con client directo, no con section__client; el mismo valor que antes, pero vale mirarlo.
- `BOLT-28`: Ninguna URL, template ni decorador cambió; hay que confirmar que los decoradores @tenant_member_required siguen en todas las vistas editadas.
- `BOLT-29`: Hacer un diff de movimiento (git diff --color-moved o similar) contra el views.py original para confirmar que los cuerpos de las vistas no cambiaron. Esta validación no pudo hacerlo.
- `BOLT-29`: Los decoradores @tenant_member_required están en todas las vistas de dashboard del paquete; home, contact_submit y login_modal no tienen decorador. Confirmar que ese era el estado original.
- `BOLT-29`: El dev no usó git mv, así que se pierde el historial de blame del archivo.
- `BOLT-29`: El dev no corrió Playwright; el gate lo reportó con ran=false. No se tocaron templates ni estáticos.
- `BOLT-29`: Se descartó el comentario de cabecera obsoleto de views.py (sobre contact_submit).
- `BOLT-29`: ARQUITECTURA.md:57 sigue diciendo que views.py tiene 1.099 líneas y que se separa en CONS-07. Está desactualizado.
- `BOLT-30`: El primer resultado real del workflow se ve en GitHub Actions al hacer push de esta rama. Si falla por una variable de entorno faltante, se corrige en una card siguiente.
- `BOLT-30`: pip-audit puede dejar el workflow en rojo si hay vulnerabilidades en requirements.txt. Es el objetivo del control y enlaza con SEC-10.
- `BOLT-30`: En CI el paso e2e del gatekeeper se omite solo, porque no hay archivos cambiados respecto de HEAD.
- `BOLT-30`: El trigger push sin filtro de ramas más pull_request hacia develop/main ejecuta CI dos veces en ramas con PR abierto. Decide si te sirve.
- `BOLT-30`: Python 3.11 resuelve al último parche, mientras que render.yaml fija 3.11.0.

## Hallazgos incidentales

- `BOLT-25`: Documentacion/README.md (líneas ~304, 312, 541, 665) todavía describe order_processor.py y cloudinary_settings.py como vigentes.
- `BOLT-25`: Documentacion/MASTER_PLAN_Y_ARQUITECTURA.md (líneas 86, 87, 149, 158) todavía menciona cloudinary_settings.py, CLOUDINARY_DEFAULT_LIMITS y OrderProcessor como existentes.
- `BOLT-25`: docs/kanban_agente.md (líneas 130, 444) menciona order_processor. Es histórico, pero puede inducir a error.
- `BOLT-25`: OPS-04 (alerta de créditos Cloudinary) sigue citando CLOUDINARY_ALERT_THRESHOLDS, que vivía en el archivo borrado; al implementarla habrá que definir los umbrales de nuevo.
- `BOLT-26`: _purge_beyond_legal_cap está anotado como -> str pero devuelve None en los casos sin purga y en dry-run (cosmético; el método existente _purge_old_contacts tiene el mismo patrón).
- `BOLT-26`: El tope se aplica por created_at, no por la última actividad del mensaje, y no hay aviso previo al cliente antes de borrar mensajes new sin leer.
- `BOLT-28`: apps/website/templatetags/website_tags.py:44 usa .objects.get( fuera del alcance de la guardia (solo cubre views.py); conviene revisar que filtre por tenant.
- `BOLT-28`: El dev no buscó el mismo patrón (get_object_or_404 sin helper) en orders ni accounts, como pedía el spec; queda sin verificar.

## Pendiente de tu decisión

- `BOLT-24` (BLOCKED): la sesión del agente falló: timeout de 3600s
- `BOLT-27` (REJECTED): El DoD exige `pip-audit` limpio sobre requirements.txt y el propio informe dice que sigue con pillow==11.0.0 y 71 avisos. Tampoco hay evidencia de Playwright con las versiones nuevas (el gate marca e2e `ran: false`).
