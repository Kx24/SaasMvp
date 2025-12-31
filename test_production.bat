@echo off
REM =============================================================================
REM test_production.bat - Probar configuración de producción localmente (Windows)
REM =============================================================================
REM
REM Uso:
REM   test_production.bat
REM
REM Este script simula el entorno de producción en tu máquina local.
REM =============================================================================

echo.
echo ==========================================
echo   TEST PRODUCCION LOCAL
echo ==========================================
echo.

REM -----------------------------------------------------------------------------
REM CONFIGURAR VARIABLES DE ENTORNO
REM -----------------------------------------------------------------------------
set DJANGO_SETTINGS_MODULE=config.settings.production
set DEBUG=False
set SECRET_KEY=test-secret-key-for-local-production-testing-only
set DATABASE_URL=sqlite:///db_production_test.sqlite3
set RENDER_EXTERNAL_HOSTNAME=localhost
set DEFAULT_TENANT_SLUG=servelec
set ALLOWED_HOSTS=localhost,127.0.0.1

echo Variables de entorno configuradas:
echo    DJANGO_SETTINGS_MODULE=%DJANGO_SETTINGS_MODULE%
echo    DEBUG=%DEBUG%
echo    RENDER_EXTERNAL_HOSTNAME=%RENDER_EXTERNAL_HOSTNAME%
echo    DEFAULT_TENANT_SLUG=%DEFAULT_TENANT_SLUG%
echo.

REM -----------------------------------------------------------------------------
REM VERIFICAR PYTHON
REM -----------------------------------------------------------------------------
echo Verificando Python...
python --version
echo.

REM -----------------------------------------------------------------------------
REM EJECUTAR CHECKS
REM -----------------------------------------------------------------------------
echo Ejecutando checks de Django...
python manage.py check --deploy
echo.

REM -----------------------------------------------------------------------------
REM MIGRACIONES
REM -----------------------------------------------------------------------------
echo Ejecutando migraciones...
python manage.py migrate --verbosity=1
echo.

REM -----------------------------------------------------------------------------
REM ARCHIVOS ESTATICOS
REM -----------------------------------------------------------------------------
echo Recolectando archivos estaticos...
python manage.py collectstatic --noinput --clear --verbosity=0
echo    OK Archivos estaticos listos
echo.

REM -----------------------------------------------------------------------------
REM SETUP DE PRODUCCION
REM -----------------------------------------------------------------------------
echo Ejecutando setup_production...
python manage.py setup_production --domain=localhost --tenant=servelec
echo.

REM -----------------------------------------------------------------------------
REM INICIAR SERVIDOR
REM -----------------------------------------------------------------------------
echo ==========================================
echo   INICIANDO SERVIDOR DE PRODUCCION
echo ==========================================
echo.
echo   URL: http://localhost:8000
echo   Admin: http://localhost:8000/superadmin/
echo.
echo   Presiona Ctrl+C para detener
echo.
echo ==========================================
echo.

REM Usar gunicorn si está disponible
where gunicorn >nul 2>nul
if %ERRORLEVEL% == 0 (
    echo Usando gunicorn...
    gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1
) else (
    echo Usando runserver...
    python manage.py runserver 0.0.0.0:8000
)
