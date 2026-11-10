#!/usr/bin/env bash
# =============================================================================
# build.sh - Script de build para Render
# =============================================================================
# Este script SOLO prepara el entorno. Los datos se crean via management command.
# =============================================================================

set -o errexit  # Salir si hay error
set -o pipefail # Fallar si algún comando en pipe falla

echo ""
echo "=========================================="
echo "  🚀 BUILD - SaaS MVP Multi-Tenant"
echo "=========================================="
echo ""

# -----------------------------------------------------------------------------
# 1. INSTALAR DEPENDENCIAS
# -----------------------------------------------------------------------------
echo "📦 [1/5] Instalando dependencias..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "   ✓ Dependencias instaladas"

# -----------------------------------------------------------------------------
# 2. CREAR DIRECTORIOS
# -----------------------------------------------------------------------------
echo ""
echo "📁 [2/5] Creando directorios..."
mkdir -p staticfiles
mkdir -p media/tenants
mkdir -p templates/tenants/_default/landing
echo "   ✓ Directorios creados"

# -----------------------------------------------------------------------------
# 3. BUILD DE TAILWIND (#AUD-11) + ARCHIVOS ESTÁTICOS
# -----------------------------------------------------------------------------
# El compilado (static/css/output.css) tiene que existir en static/ ANTES
# de collectstatic --clear, que es lo que lo copia a staticfiles/.
echo ""
echo "🎨 [3/5] Compilando Tailwind y recolectando archivos estáticos..."
npm ci --quiet
npm run build:css
python manage.py collectstatic --noinput --clear --verbosity=0
echo "   ✓ Archivos estáticos listos"

# -----------------------------------------------------------------------------
# 4. MIGRACIONES
# -----------------------------------------------------------------------------
echo ""
echo "🗄️  [4/5] Ejecutando migraciones..."
python manage.py migrate --noinput --verbosity=0
echo "   ✓ Migraciones aplicadas"

# -----------------------------------------------------------------------------
# 5. SETUP DE PRODUCCIÓN
# -----------------------------------------------------------------------------
echo ""
echo "⚙️  [5/5] Configurando datos iniciales..."
python manage.py setup_production
echo "   ✓ Setup completado"

# -----------------------------------------------------------------------------
# RESUMEN
# -----------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "  ✅ BUILD COMPLETADO"
echo "=========================================="
echo ""
echo "  Variables de entorno detectadas:"
echo "  - RENDER_EXTERNAL_HOSTNAME: ${RENDER_EXTERNAL_HOSTNAME:-'(no definido)'}"
echo "  - DEFAULT_TENANT_SLUG: ${DEFAULT_TENANT_SLUG:-'(no definido)'}"
echo "  - DEBUG: ${DEBUG:-'(no definido)'}"
echo ""