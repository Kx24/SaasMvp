# BOLT-67 — `SEC-15`: runbook de incidentes y rotación de secretos

> Card de documento. Sin código, sin tests de rojo (`red_tests` vacío).

## Contexto verificado (2026-11-18)

- `Documentacion/Inventario_Secretos.md` ya trae el inventario completo de variables y una
  sección **"Política de rotación"** (línea ~49) con una tabla por variable (cuándo y cómo rotar).
  **No la dupliques**: el runbook la enlaza.
- `Documentacion/SEGURIDAD.md` lista los controles y hallazgos abiertos; `Documentacion/ARQUITECTURA.md`
  describe los servicios (Render, Neon, Cloudinary, Zoho, MercadoPago, GitHub).
- La Ley 21.719 pasó a vigencia 15-oct-2027 (2026-11-18). `LEY-06` (procedimiento de brechas,
  art. 14 sexies) queda para 2027: este runbook debe dejar un apartado "Datos personales" que lo
  referencie como pendiente, sin inventar plazos legales.

## Qué hacer

Crea `Documentacion/Runbook_Incidentes.md`, en español, corto y accionable (una persona sola lo
sigue a las 2 de la mañana). Secciones:

1. **Primeros 15 minutos** (cualquier incidente): contener, no borrar evidencia, anotar hora y
   qué se vio.
2. **Por tipo de incidente**, cada uno con "señales", "contener" y "recuperar":
   a) fuga de un secreto (clave en un commit, captura, correo): qué rotar según
      `Inventario_Secretos.md`, en qué orden (`SECRET_KEY`, `DATABASE_URL`, `FIELD_ENCRYPTION_KEY`,
      SMTP, Cloudinary, MercadoPago, token de GitHub) y qué se rompe al rotar cada una;
   b) acceso indebido a un tenant o al panel `/superadmin/` (sesiones, cuentas staff, 2FA);
   c) base de datos dañada o borrada: rama de Neon / restore (referencia a `DB-02`, aún pendiente:
      dilo explícitamente);
   d) sitio caído tras un deploy: volver al deploy anterior en Render, ver el log del build;
   e) correo o dominio comprometido (Zoho, DNS).
3. **Datos personales:** apartado breve que remite a `LEY-06` (pendiente) y a la herramienta
   `data_subject` ya implementada; sin plazos legales.
4. **Contactos y cuentas** (solo nombres de servicios y dónde mirar; **sin contraseñas, claves ni
   correos personales**).
5. **Después del incidente:** registro (fecha, causa, qué se hizo) en una tabla al final del
   documento, vacía, para ir llenándola.

Enlázalo desde `Documentacion/INDEX.md` y desde `SEGURIDAD.md` (donde se mencione la rotación).

## No tocar

Código, `Inventario_Secretos.md` (solo se enlaza), `render.yaml`. No pegues ningún valor real de
variable.

## DoD

- [ ] `Documentacion/Runbook_Incidentes.md` existe, con las cinco secciones, y se llega a él desde
      `INDEX.md`.
- [ ] Cierre documental (`SEC-15`).
