#!/usr/bin/env bash
# build.sh - Script de build para Render
# ======================================

set -o errexit  # Salir si hay error

echo "=========================================="
echo "  🚀 INICIANDO BUILD - SaaS MVP"
echo "=========================================="

# 1. Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Crear directorios necesarios
echo ""
echo "📁 Preparando directorios..."
mkdir -p staticfiles
mkdir -p media/tenants
mkdir -p templates/tenants/_default/landing

# 3. Recolectar archivos estáticos
echo ""
echo "🎨 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# 4. Ejecutar migraciones
echo ""
echo "🗄️  Ejecutando migraciones..."
python manage.py migrate --noinput

# 5. Crear tenant por defecto si no existe
echo ""
echo "🏢 Verificando tenant por defecto..."
python manage.py shell << 'EOF'
from apps.tenants.models import Client, Domain

# Verificar si existe algún cliente
if not Client.objects.exists():
    print("📝 Creando tenant Servelec...")
    
    # Crear cliente
    client = Client.objects.create(
        name="Servelec Ingeniería",
        slug="servelec",
        company_name="Servelec Ingeniería SpA",
        contact_email="contacto@servelec-ingenieria.cl",
        contact_phone="+56912345678",
        is_active=True
    )
    
    # Configurar settings
    client.settings.primary_color = "#2563eb"
    client.settings.secondary_color = "#1e40af"
    client.settings.meta_title = "Servelec Ingeniería - Soluciones Eléctricas"
    client.settings.meta_description = "Servicios eléctricos profesionales"
    client.settings.save()
    
    # Crear dominios
    Domain.objects.create(
        client=client,
        domain="saasmvp-kajv.onrender.com",
        domain_type="subdomain",
        is_primary=True,
        is_active=True,
        is_verified=True
    )
    
    Domain.objects.create(
        client=client,
        domain="servelec-ingenieria.cl",
        domain_type="primary",
        is_primary=False,
        is_active=True,
        is_verified=True
    )
    
    print("✅ Tenant Servelec creado exitosamente")
    
    # Crear secciones básicas
    from apps.website.models import Section, Service
    
    Section.objects.create(
        client=client,
        section_type='hero',
        title='Bienvenido a Servelec Ingeniería',
        subtitle='Soluciones eléctricas profesionales',
        description='Expertos en instalaciones eléctricas industriales y residenciales.',
        order=10,
        is_active=True
    )
    
    Section.objects.create(
        client=client,
        section_type='about',
        title='Quiénes Somos',
        subtitle='Más de 10 años de experiencia',
        description='Somos una empresa dedicada a brindar soluciones eléctricas de calidad.',
        order=20,
        is_active=True
    )
    
    Section.objects.create(
        client=client,
        section_type='contact',
        title='Contáctanos',
        subtitle='Estamos para ayudarte',
        order=30,
        is_active=True
    )
    
    # Crear servicios de ejemplo
    Service.objects.create(
        client=client,
        name='Instalaciones Eléctricas',
        icon='⚡',
        description='Instalaciones residenciales e industriales',
        price_text='Cotizar',
        order=10,
        is_active=True,
        is_featured=True
    )
    
    Service.objects.create(
        client=client,
        name='Mantención Preventiva',
        icon='🔧',
        description='Programas de mantención para tu tranquilidad',
        price_text='Desde $50.000',
        order=20,
        is_active=True,
        is_featured=True
    )
    
    Service.objects.create(
        client=client,
        name='Emergencias 24/7',
        icon='🚨',
        description='Servicio de emergencias las 24 horas',
        price_text='Consultar',
        order=30,
        is_active=True,
        is_featured=False
    )
    
    print("✅ Secciones y servicios creados")
    
else:
    print("✅ Ya existen tenants en la base de datos")
    for c in Client.objects.all():
        print(f"   - {c.name} ({c.slug})")

EOF

# 6. Crear superusuario si no existe
echo ""
echo "👤 Verificando superusuario..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(is_superuser=True).exists():
    import os
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
    
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superusuario '{username}' creado")
else:
    print("✅ Ya existe un superusuario")

EOF

echo ""
echo "=========================================="
echo "  ✅ BUILD COMPLETADO EXITOSAMENTE"
echo "=========================================="