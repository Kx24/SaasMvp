#!/usr/bin/env bash
# build.sh - Script de build para Render
# ======================================
# Este script se ejecuta cada vez que Render despliega la aplicación

set -o errexit  # Salir si hay error

echo "=========================================="
echo "  🚀 INICIANDO BUILD - SaaS MVP"
echo "=========================================="

# 1. Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Crear directorio de archivos estáticos
echo ""
echo "📁 Preparando directorios..."
mkdir -p staticfiles
mkdir -p media/tenants

# 3. Recolectar archivos estáticos
echo ""
echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# 4. Ejecutar migraciones
echo ""
echo "🗄️  Ejecutando migraciones..."
python manage.py migrate --noinput

# 5. Crear directorios de templates si no existen
echo ""
echo "📄 Verificando estructura de templates..."
mkdir -p templates/tenants/_default/landing

# 6. Verificar configuración
echo ""
echo "✅ Verificando configuración..."
python manage.py check --deploy

echo ""
echo "=========================================="
echo "  ✅ BUILD COMPLETADO EXITOSAMENTE"
echo "=========================================="