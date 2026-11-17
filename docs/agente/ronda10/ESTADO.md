# Ronda 10 — estado

Rama `agent/ronda10` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-52` | `CONS-08` | Registro de módulos (opción A) | ✅ DONE | 721 | 0.41 |
| `BOLT-53` | `CONS-09` | Menú y acceso del dashboard desde el registro | ✅ DONE | 728 | 0.87 |
| `BOLT-54` | `BIZ-01` | Límites del plan con efecto real | ✅ DONE | 742 | 0.72 |
| `BOLT-55` | `DASH-05` | Tests del dashboard | ✅ DONE | 810 | 2.01 |

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
- `BOLT-54`: Antes de desplegar, revisar en producción que ningún cliente ya esté por encima de su límite. Para cada Client c: Service.objects.filter(client=c).count() > c.max_services, y GalleryItem.objects.filter(client=c, section__section_type='gallery').count() > limit_for(c, 'gallery'). Quien esté por encima conserva su contenido, pero no podrá crear más.
- `BOLT-54`: Los clientes con max_images o gallery_images_limit en 0 o negativo quedan sin cupo de galería. Con los defaults (100 y 20) no aplica.
- `BOLT-54`: El tope de galería cambia: ahora es el menor entre gallery_images_limit y max_images. Verificar que ese valor sea el esperado para clientes existentes.
- `BOLT-54`: Texto visible al cliente: el mensaje 'Tu plan permite N servicios / imágenes de galería. Borra uno o pide una ampliación.' y el indicador 'N de M'.
- `BOLT-54`: Decisión del dev: el uso de galería cuenta solo los ítems de la sección gallery. Las imágenes de servicio y la portada no cuentan para el tope del tenant, y cada galería de servicio se limita por su propio conteo.
- `BOLT-54`: Decidir si se borra max_pages (DEUDA-11); borrarlo requiere una migración.
- `BOLT-55`: Restaurar `orders` a 92.46 en `scripts/gate_baseline.json` antes de commitear; el dev no pudo hacerlo por estar bloqueado el archivo.
- `BOLT-55`: Fallos de a11y que quedaron abiertos: `DASH-06` (token `--primary` roto en `base.html`) y `DASH-07`. Revisa el kanban para el detalle.
- `BOLT-55`: `BrandingForm` ahora rechaza colores en forma corta (`#abc`) y cualquier valor que no sea hex de 6 dígitos. Verifica que no haya tenants con colores guardados en otro formato.
- `BOLT-55`: Los mensajes con `is_spam=True` ya no se ven en el dashboard ni en las métricas: cambio de comportamiento visible al cliente.
- `BOLT-55`: `seed_e2e_tenants` crea el usuario `owner-e2e` con contraseña de desarrollo. Confirma que solo corre con `DEBUG=True` y nunca contra producción.
- `BOLT-55`: El menú tiene seis pantallas y no cinco; el dev lo decidió sin que el spec lo cubriera, y usó un tenant `dash-e2e` separado.

## Hallazgos incidentales

- `BOLT-53`: `unread_contacts` no lo define ningún código, así que el contador de mensajes sin leer del menú nunca se muestra (ya ocurría antes). Conviene una card para cablearlo.
- `BOLT-53`: Ninguna plantilla ni templatetag consultaba `enable_contact_form`, contra lo que decía el spec. Se resolvió con la variable `contact_disabled`, pasada solo desde la vista `home`; cualquier otra vista que renderice esos parciales no la recibe y mostraría el formulario.
- `BOLT-53`: El estado `active` de Secciones y Contactos cambió de `'sections' in request.path` / `'contacts' in request.path` a comparar `url_name`. En subpáginas (editar sección, etc.) esas entradas ya no se marcan activas.
- `BOLT-53`: El dev no corrió el rojo antes de implementar. El gate sí lo confirmó: 4 de 7 tests fallan contra HEAD.
- `BOLT-54`: Client.max_pages no tiene uso: no existe modelo de páginas. Quedó como DEUDA-11 en el kanban.
- `BOLT-54`: El botón 'Agregar servicio' del índice del dashboard (templates/dashboard/index.html) sigue activo al tope. La vista lo rechaza igual, pero no se deshabilita ni muestra el uso.
- `BOLT-54`: El dev no corrió el rojo (escribió el código antes que los tests). El red_check del orquestador sí lo confirmó.
- `BOLT-55`: `--update-baseline` bajó `orders` de 92.46 a 92.38 sin que el cambio toque `apps/orders`. Parece variación de medición, pero el trinquete quedó más laxo.
- `BOLT-55`: `DASH-06`: `var(--primary)` sigue roto en `templates/dashboard/base.html`; ya está en el kanban.
- `BOLT-55`: `DASH-07`: fallo de a11y abierto, ya está en el kanban. El informe del dev quedó truncado y no se ve el detalle.
