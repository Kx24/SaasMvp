# Ronda 10 — estado

Rama `agent/ronda10` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-52` | `CONS-08` | Registro de módulos (opción A) | ✅ DONE | 721 | 0.41 |
| `BOLT-53` | `CONS-09` | Menú y acceso del dashboard desde el registro | ✅ DONE | 728 | 0.87 |
| `BOLT-54` | `BIZ-01` | Límites del plan con efecto real | ⏳ TODO |  |  |
| `BOLT-55` | `DASH-05` | Tests del dashboard | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-52`: La entrada de menú "Portada" quedó en gallery, no en core como decía la tabla del spec. Es consecuencia de poner dashboard_portada en gallery. Con la galería apagada, CONS-09 ocultaría "Portada" y la ruta daría 404.
- `BOLT-52`: Los valores de orden del menú (10 Inicio, 20 Marca, 30 Portada, 40 Secciones, 50 Galería, 60 Mensajes) los eligió el dev; el spec no los fijaba.
- `BOLT-52`: La sección "Módulos" de ARQUITECTURA.md quedó como subsección de §5 para no renumerar las demás.
- `BOLT-53`: CAMBIO VISIBLE: con la galería apagada, "Portada" y "Galería" ya no aparecen atenuados con "Off", desaparecen. "Portada" quedó en el módulo `gallery` (como lo dejó BOLT-52), así que también desaparece.
- `BOLT-53`: Revisar el menú en el navegador con cada rol (`owner`, `admin`, `editor`, `viewer`) y con galería y contacto apagados.
- `BOLT-53`: Cambio de permisos visibles: "Galería" y "Secciones" ahora exigen `edit_content` según el registro; `viewer` ya no los ve (antes los veían todos los roles). Confirmar que es lo deseado.
- `BOLT-53`: Las etiquetas del menú ahora salen del registro: "Marca" en vez de "Personalizar" y "Mensajes" en vez de "Contactos". Es un texto visible al cliente.
- `BOLT-53`: Con el contacto apagado, el formulario público desaparece de la home en `landing/home.html`, los parciales de contacto y el tema `electricidad`. Mirarlo en la home de un tenant con el contacto apagado.
- `BOLT-53`: `dashboard_sections` no lleva `module_required` porque no tiene flag. Verificar que un `viewer` aún pueda abrir esa URL a mano, ya que solo se le quitó el enlace del menú.
- `BOLT-53`: Se editó `config/settings/base.py` para registrar el context processor `dashboard_menu`.

## Hallazgos incidentales

- `BOLT-53`: `unread_contacts` no lo define ningún código, así que el contador de mensajes sin leer del menú nunca se muestra (ya ocurría antes). Conviene una card para cablearlo.
- `BOLT-53`: Ninguna plantilla ni templatetag consultaba `enable_contact_form`, contra lo que decía el spec. Se resolvió con la variable `contact_disabled`, pasada solo desde la vista `home`; cualquier otra vista que renderice esos parciales no la recibe y mostraría el formulario.
- `BOLT-53`: El estado `active` de Secciones y Contactos cambió de `'sections' in request.path` / `'contacts' in request.path` a comparar `url_name`. En subpáginas (editar sección, etc.) esas entradas ya no se marcan activas.
- `BOLT-53`: El dev no corrió el rojo antes de implementar. El gate sí lo confirmó: 4 de 7 tests fallan contra HEAD.
