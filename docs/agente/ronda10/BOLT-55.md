# BOLT-55 — `DASH-05`: tests del dashboard

## Contexto verificado (2026-11-15)

- El dashboard tiene tests de autorización (`apps/accounts/tests_dashboard_roles.py`,
  `apps/website/tests/test_tenant_authorization.py`) y de módulos (`BOLT-52` a `BOLT-54`), pero
  casi ninguno de **lo que hace**: guardar una sección, subir una imagen, reordenar servicios,
  editar la marca, marcar un mensaje.
- Playwright: `tests/e2e/smoke.spec.js` y `a11y.spec.js` cubren solo páginas públicas. Los
  tenants de prueba los crea `seed_e2e_tenants`; el servidor de e2e usa el puerto 8811 (mira la
  configuración de Playwright y `scripts/gatekeeper.py` antes de tocar nada).
- Cobertura al 2026-11-15: `views/gallery.py` 76 %, `views/branding.py`, `views/sections.py` y
  `views/services.py` con ramas de error sin cubrir.

## Qué hacer

1. **Tests de Django** (cliente de test, usuario `owner` del tenant, datos reales), un archivo por
   área en `apps/website/tests/`:
   - Secciones: editar título, texto e imagen; validación de campos; el cambio se ve en la home.
   - Servicios: crear, editar, activar/desactivar, destacar, reordenar (el orden persiste y es
     por tenant), borrar con confirmación.
   - Galería: agregar (con la subida a Cloudinary **parcheada**), editar, ocultar, borrar; archivo
     no permitido rechazado (`SEC-11`).
   - Marca: cambiar colores, fuente y logo; valores inválidos rechazados; la home refleja los
     tokens nuevos.
   - Mensajes: listar, marcar leído y respondido; el contador de no leídos baja.
   Cada test afirma el efecto en la base **y** en la respuesta.
2. **Playwright:** extiende `seed_e2e_tenants` con un usuario `owner` de prueba (contraseña solo
   de desarrollo) y agrega `tests/e2e/dashboard.spec.js`: login, las cinco pantallas del menú
   cargan sin errores de consola, y a11y (mismas reglas de `a11y.spec.js`) sobre el inicio del
   dashboard y la pantalla de secciones. Si a11y destapa fallos del dashboard, arregla los
   simples (contraste, `label`, `alt`) y reporta el resto como hallazgos con una fila en el
   kanban.
3. Sin red: Cloudinary y SMTP parcheados en los tests de Django.
4. Al final, con todo verde: `python scripts/gatekeeper.py --strict --update-baseline`.

## No tocar

Las vistas, salvo bug demostrado por un test (se arregla y se reporta). El usuario de e2e no debe
crearse fuera de `seed_e2e_tenants` ni existir en producción (el comando ya se niega a correr con
`DEBUG=False`: verifícalo y, si no, agrégale esa guardia con test).

## DoD

- [ ] Cada flujo del dashboard tiene al menos un test de éxito y uno de error.
- [ ] Playwright cubre el dashboard con login; a11y verde en dos pantallas.
- [ ] La cobertura total no baja; el baseline sube.
- [ ] Cierre documental (`DASH-05`). En `revisar_humano`: fallos de a11y que quedaron abiertos.
