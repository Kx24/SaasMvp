# BOLT-22 — `SEC-06`: credenciales SMTP y API cifradas en reposo

## Contexto verificado (2026-11-14)

`ClientEmailSettings` (`apps/tenants/models.py`) guarda en texto plano `smtp_password` (línea
504, su `help_text` dice "se almacena encriptada" y no es cierto) y `api_key` (línea 521). Las
lee `apps/tenants/services/email_dispatcher.py` (líneas 228, 239, 249, 259) y las muestra el admin
(`apps/tenants/admin.py:101` y `:106`, `ClientEmailSettingsAdmin` en la línea 340).

`config/settings/production.py` falla al importar si faltan `SECRET_KEY` (líneas 27–29) o las
credenciales de correo (174–181). `apps/core/tests/test_production_settings.py` inyecta esas
variables por subproceso.

## Decisiones del dueño (2026-11-14)

- Cifrado con **`MultiFernet`** (paquete `cryptography`, dependencia autorizada).
- Clave en la variable de entorno **`FIELD_ENCRYPTION_KEY`**: una o más claves Fernet separadas
  por coma; la primera cifra, todas descifran (rotación sin downtime).
- **Producción falla al importar** si `FIELD_ENCRYPTION_KEY` falta (mismo patrón que `SECRET_KEY`).
- Migración de datos **reversible**.

## Diseño

1. `apps/core/fields.py` (nuevo): `EncryptedTextField(models.TextField)`.
   - `get_prep_value`: `None`/`''` pasan tal cual; lo demás se guarda como
     `'fernet:' + token`. Si el valor ya empieza con `fernet:` no se vuelve a cifrar.
   - `from_db_value` / `to_python`: si empieza con `fernet:`, descifra; si no, devuelve el valor
     tal cual (filas antiguas aún en texto plano siguen funcionando hasta que corra la migración).
   - Token inválido (clave equivocada): levanta un error claro
     (`ImproperlyConfigured` con un mensaje que nombra `FIELD_ENCRYPTION_KEY`), no devuelve basura.
   - La construcción del `MultiFernet` lee `settings.FIELD_ENCRYPTION_KEYS` en cada uso o con
     caché invalidable (los tests usan `override_settings`).
2. Settings:
   - `config/settings/base.py`: `FIELD_ENCRYPTION_KEYS = [k.strip() for k in
     os.environ.get('FIELD_ENCRYPTION_KEY', '').split(',') if k.strip()]`.
   - `config/settings/development.py` (y `e2e` si no hereda de development): si la lista está
     vacía, derivar una clave de desarrollo determinista desde `SECRET_KEY`
     (`base64.urlsafe_b64encode(hashlib.sha256(SECRET_KEY.encode()).digest())`), para que dev y
     tests no necesiten variables de entorno.
   - `config/settings/production.py`: `raise ValueError(...)` al importar si la lista está vacía.
     Sin clave derivada en producción.
3. Modelo: `smtp_password` y `api_key` pasan a `EncryptedTextField(blank=True)`; corrige el
   `help_text`. Migración de esquema (`AlterField`) + migración de datos (`RunPython`) que cifra
   las filas existentes y cuyo reverso las descifra. Itera con `.iterator()` y guarda con
   `update_fields`.
4. Admin (`ClientEmailSettingsAdmin`): los dos campos se muestran con
   `forms.PasswordInput(render_value=False)`; si el formulario llega vacío se conserva el valor
   guardado (no se borra la credencial por editar otro campo).
5. `render.yaml`: agrega `FIELD_ENCRYPTION_KEY` con `sync: false` junto a las demás variables
   secretas. `Documentacion/Inventario_Secretos.md`: una fila nueva (qué es, dónde vive, cómo
   generarla: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`,
   cómo rotarla: anteponer la clave nueva y re-guardar).
6. `requirements.txt`: `cryptography` con versión fijada (la que instale `pip` hoy).
   Instálala con `python -m pip install cryptography` y fija la versión exacta.
7. `apps/core/tests/test_production_settings.py`: agrega `FIELD_ENCRYPTION_KEY` a las variables
   que inyecta, y un caso nuevo: sin ella, importar production falla.

## Tests (archivo nuevo `apps/tenants/tests_encryption.py`)

- Tras guardar, el valor **crudo** en la base (SQL directo con `connection.cursor()`, no el ORM)
  empieza con `fernet:` y no contiene el texto ingresado — para `smtp_password` y `api_key`.
- Releer con el ORM devuelve el texto original.
- Una fila escrita en texto plano por SQL directo se lee tal cual (compatibilidad).
- Rotación: valor cifrado con la clave A; con `FIELD_ENCRYPTION_KEYS=[B, A]` se sigue leyendo, y
  al re-guardar queda cifrado con B (se lee con `[B]` sola).
- Clave equivocada → error claro, no texto basura.
- La función forward de la migración de datos cifra filas en texto plano y la reverse las
  descifra (llámalas directamente con `django.apps.apps` y `connection.schema_editor()` o
  ejercítalas con `MigrationExecutor`; elige lo más simple que sea confiable).
- Admin: el HTML del formulario de cambio no contiene la contraseña guardada; un POST con el
  campo vacío no la borra.
- `email_dispatcher` recibe la contraseña en claro (un test que arme el backend SMTP y verifique
  el `password` basta; mira los tests existentes del dispatcher).

## No tocar

Otros campos del modelo; la lógica de envío de `email_dispatcher`; `build.sh`; `.env`.

## Tests de rojo

`apps.tenants.tests_encryption`

## DoD

- [ ] Valor en base ≠ texto ingresado, para los dos campos (test con SQL directo).
- [ ] Migración de datos con forward y reverse probados.
- [ ] Producción no arranca sin `FIELD_ENCRYPTION_KEY`; dev y tests no la necesitan.
- [ ] Admin no devuelve el secreto al navegador.
- [ ] `render.yaml` e `Inventario_Secretos.md` actualizados.
- [ ] Cierre documental (`SEC-06`). En el informe, bajo DECISIONES, repite en mayúsculas:
      "ANTES DE DESPLEGAR: crear FIELD_ENCRYPTION_KEY en Render".
