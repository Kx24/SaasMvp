# Ronda 8 — estado

Rama `agent/ronda8` · generado por `orchestrate.py` (no editar a mano).

| Card | Maestra | Título | Estado | Tests | Costo USD |
|---|---|---|---|---|---|
| `BOLT-36` | `CONS-11` | Cobertura de tenants núcleo ≥ 90 % (1 de 4) | ✅ DONE | 423 | 0.53 |
| `BOLT-37` | `CONS-11` | Cobertura de orders ≥ 80 % (2 de 4) | ✅ DONE | 500 | 0.92 |
| `BOLT-38` | `CONS-11` | Cobertura de core y servicios de tenants (3 de 4) | ✅ DONE | 622 | 0.95 |
| `BOLT-39` | `CONS-11` | Cobertura total ≥ 70 % y cierre (4 de 4) | ✅ DONE | 622 | 0.27 |
| `BOLT-40` | `CONS-12` | Guardia de objetos de tenant en orders y accounts | ✅ DONE | 625 | 0.4 |
| `BOLT-41` | `SEC-18` | Un solo TenantAdminMixin | ✅ DONE | 631 | 0.59 |
| `BOLT-42` | `COMP-03` | Botón de enviar sin quedarse en Enviando | ✅ DONE | 635 | 0.38 |
| `BOLT-43` | `DEUDA-09` | Borrar la vista dashboard_services huérfana | ⏳ TODO |  |  |
| `BOLT-44` | `FLOW-04` | provision_tenant deja un Domain primario | ⏳ TODO |  |  |
| `BOLT-45` | `LEY-08` | Aviso previo antes de purgar mensajes sin leer | ⏳ TODO |  |  |
| `BOLT-46` | `TOOL-04` | Pulido de la CI y dependencias de desarrollo | ⏳ TODO |  |  |
| `BOLT-47` | `DOC-01` | Documentación al día tras las rondas 4 a 8 | ⏳ TODO |  |  |

## Revisar a mano en el PR

- `BOLT-36`: Cobertura antes y después: tenants_core 83,87 % → 100 %; total 65,04 % → 65,32 %; orders 70,41 % → 70,41 % (sin cambio).
- `BOLT-36`: scripts/gate_baseline.json lo actualizó el gate (--update-baseline). Ningún número bajó.
- `BOLT-36`: No hay test en rojo contra HEAD porque la card solo agrega cobertura sobre código que ya funcionaba. Es lo esperado, pero conviene saberlo.
- `BOLT-36`: El dev agregó CONS-11 (parte) al histórico con formato de fila de tabla, no de viñeta como decía el spec. Mira si te sirve así.
- `BOLT-37`: Cobertura antes y después: orders 70,41 % → 92,46 %; total 65,32 % → 69,22 % (aún bajo 70 %, CONS-11 sigue parcial); tenants_core 100 % sin cambios.
- `BOLT-37`: Cambio de código de producción en mercadopago_service.py (flujo de pagos): ahora MercadoPagoError se propaga sin envolver. Confirmar que las vistas que la capturan se comportan como se espera.
- `BOLT-37`: Los templates de checkout se movieron a templates/orders/. Confirmar que no hay otros overrides de tenant que dependan de la ruta antigua.
- `BOLT-37`: Confirmar en producción o en un sandbox que la página de éxito del checkout se renderiza, porque antes daba 500.
- `BOLT-38`: Cobertura total: 69,22 % antes y 74,76 % después. orders 92,46 % sin cambio y tenants_core 100 % sin cambio.
- `BOLT-38`: El rojo no se confirmó contra el código original: red_check es null y el dev no lo verificó. Los tests de los 3 bugs se escribieron contra el código ya corregido.
- `BOLT-38`: Se eliminaron los tags get_testimonials y get_featured_testimonials de website_tags. Confirma que ningún template de un tema fuera de esta rama, por ejemplo feature/RanchocachimbaEtapa1, los use.
- `BOLT-38`: Cambio visible en tenant_include: el comentario HTML de fallback ahora se renderiza como comentario real y ya no como texto escapado.
- `BOLT-38`: El dev no confirmó el rojo de los tests de los bugs: el import de cloudinary.api, el fallback de tenant_include y los tags eliminados. Conviene ejecutar --red-check.
- `BOLT-39`: El spec pedía priorizar tests de vistas de accounts, sitemaps y admins, pero el dev no escribió ninguno porque los umbrales ya se cumplían. Conviene decidir si se quiere una card aparte para esa cobertura.
- `BOLT-39`: No existe una fila BOLT-39 en el plan de ejecución, así que no se marcó ningún ✅. Revisar si hace falta registrarla.
- `BOLT-39`: Confirmar si se elimina `create_tenant` o se documenta como vigente.
- `BOLT-40`: Lista TENANT_EXCEPTIONS en apps/core/tests/test_tenant_objects.py: Plan por slug (x2, modelo global), Order por uuid (secreto), Order por order_number y mp_payment_id (webhook sin tenant), Order por pk en signals.py, Section en website_tags (filtra por client) y User por email en accounts.
- `BOLT-40`: Cambio de comportamiento en autenticación: apps/accounts/views.py, request_password_reset_view. Un usuario cuyo profile.client difiere de request.client no recibe reset; superusers y request.client None quedan exentos. Confirma que ese es el comportamiento deseado (por ejemplo, usuarios que piden el reset desde un dominio de preview).
- `BOLT-40`: El dev no corrió el rojo con git stash; lo confirmó el red-check del gate (1 test falla contra HEAD).
- `BOLT-41`: apps/accounts/mixins.py: la nueva regla de FK usa profile__client para los FK a User y el filtro lateral oculta tenant_field. Es un cambio de permisos del admin.
- `BOLT-41`: La fila de SEC-18 en SEGURIDAD.md quedó entre SEC-05 y SEC-06, fuera de orden numérico. Es solo cosmético.
- `BOLT-41`: Los permisos que el test da al staff (view/change/delete en 5 apps) y la lista cerrada de modelos cubiertos: un admin nuevo con el mixin hará fallar test_registry_is_covered_by_fixtures a propósito.
- `BOLT-42`: Los tests de plantilla verifican el texto del template con regex; la recuperación ante error de servidor en los formularios de POST nativo depende de pageshow (bfcache/volver atrás), no de un reset explícito. Conviene probar a mano un 400/500 en el navegador.
- `BOLT-42`: El e2e nuevo corre solo para tenants con contactFlow 'simple'. Los demás flujos no tienen caso e2e para este caso.

## Hallazgos incidentales

- `BOLT-37`: Bug corregido: except mercadopago.exceptions.MPException inexistente en process_payment.
- `BOLT-37`: Bug corregido: los templates checkout_success.html y checkout_error.html estaban fuera de orders/, lo que daba 500 tras cada pago aprobado.
- `BOLT-37`: Sin cubrir en orders: admin.py 64 %, forms.py 72 %, email_service.py 82 %, views_onboarding.py 93 %.
- `BOLT-37`: No se corrió --red-check. El rojo está documentado en el informe, con el AttributeError y el TemplateDoesNotExist.
- `BOLT-38`: Los comandos de gestión con 0 % (audit_cloudinary_assets, check_cloudinary, create_tenant…) siguen sin cobertura. Es la card siguiente.
- `BOLT-38`: El spec citaba un 65,04 % de partida, pero el baseline de entrada ya era 69,22 % por BOLT-37.
- `BOLT-39`: `create_tenant` (110 sentencias, 0 % de cobertura) parece código muerto frente a `provision_tenant`. Nadie confirmó que no se invoque desde otro lado, y no se borró.
- `BOLT-39`: Siguen en 0 % los comandos `audit_cloudinary_assets`, `check_cloudinary`, `cloudinary_usage`, `verify_search_console`, `setup_cloudinary_folders`, `setup_dev_env` y `seed_e2e_tenants`. Además, varios archivos de admin y vistas listados en el spec siguen con huecos. Esto no afecta el contrato, pero queda como deuda.
- `BOLT-40`: Fuga corregida: reset de contraseña cross-tenant en accounts/views.py (User.objects.get(email=...) sin validar tenant).
- `BOLT-40`: La guardia ahora escanea todo website, no solo website/views/; apareció website_tags.py (Section.objects.get), que ya filtra por client.
- `BOLT-41`: UserProfile.user listaba usuarios de todos los tenants (corregido en esta card).
- `BOLT-41`: Los get_list_filter de SectionAdmin, ServiceAdmin y ContactSubmissionAdmin repiten lo que ya hace el mixin (deuda menor, sin tocar).
- `BOLT-41`: El dev no pudo ver el rojo con git stash; el gate --red-check sí lo confirmó, pero solo con un test fallando (el de la clase única). El test del desplegable user de UserProfileAdmin no se vio en rojo.
