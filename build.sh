#!/usr/bin/env bash
# build.sh - Script de build para Render
# ======================================

set -o errexit

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

# 5. Setup de producción
echo ""
echo "🏢 Configurando tenant y dominios..."
python manage.py shell << 'PYTHON_SCRIPT'
import os
from apps.tenants.models import Client, Domain
from django.contrib.auth import get_user_model

User = get_user_model()

# Obtener el hostname de Render
render_hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'saasmvp-kajv.onrender.com')
print(f"📍 Render hostname: {render_hostname}")

# Crear o obtener cliente
client, created = Client.objects.get_or_create(
    slug='servelec',
    defaults={
        'name': 'Servelec Ingeniería',
        'company_name': 'Servelec Ingeniería SpA',
        'contact_email': 'contacto@servelec-ingenieria.cl',
        'contact_phone': '+56912345678',
        'is_active': True
    }
)

if created:
    print("✅ Cliente Servelec creado")
    # Configurar settings
    client.settings.primary_color = "#2563eb"
    client.settings.secondary_color = "#1e40af"
    client.settings.meta_title = "Servelec Ingeniería"
    client.settings.save()
else:
    print("✅ Cliente Servelec ya existe")

# Asegurar que el dominio de Render existe
domain_render, created = Domain.objects.get_or_create(
    domain=render_hostname,
    defaults={
        'client': client,
        'domain_type': 'subdomain',
        'is_primary': True,
        'is_active': True,
        'is_verified': True
    }
)
if created:
    print(f"✅ Dominio {render_hostname} creado")
else:
    # Asegurar que está activo y vinculado al cliente correcto
    domain_render.client = client
    domain_render.is_active = True
    domain_render.save()
    print(f"✅ Dominio {render_hostname} verificado")

# Agregar dominio de producción si no existe
prod_domain = 'servelec-ingenieria.cl'
domain_prod, created = Domain.objects.get_or_create(
    domain=prod_domain,
    defaults={
        'client': client,
        'domain_type': 'primary',
        'is_primary': False,
        'is_active': True,
        'is_verified': True
    }
)
if created:
    print(f"✅ Dominio {prod_domain} creado")
else:
    print(f"✅ Dominio {prod_domain} ya existe")

# Agregar localhost para desarrollo
localhost_domain, created = Domain.objects.get_or_create(
    domain='localhost',
    defaults={
        'client': client,
        'domain_type': 'development',
        'is_primary': False,
        'is_active': True,
        'is_verified': True
    }
)
if created:
    print("✅ Dominio localhost creado")

# Agregar 127.0.0.1 para desarrollo
local_ip, created = Domain.objects.get_or_create(
    domain='127.0.0.1',
    defaults={
        'client': client,
        'domain_type': 'development',
        'is_primary': False,
        'is_active': True,
        'is_verified': True
    }
)
if created:
    print("✅ Dominio 127.0.0.1 creado")

# Mostrar todos los dominios configurados
print("\n📋 Dominios configurados:")
for d in Domain.objects.all():
    print(f"   - {d.domain} → {d.client.name} (active={d.is_active})")

# Crear secciones si no existen
from apps.website.models import Section, Service

if not Section.objects.filter(client=client).exists():
    print("\n📝 Creando secciones...")
    Section.objects.create(
        client=client, section_type='hero',
        title='Bienvenido a Servelec Ingeniería',
        subtitle='Soluciones eléctricas profesionales',
        description='Expertos en instalaciones eléctricas.',
        order=10, is_active=True
    )
    Section.objects.create(
        client=client, section_type='about',
        title='Quiénes Somos', subtitle='Experiencia y calidad',
        description='Empresa dedicada a soluciones eléctricas.',
        order=20, is_active=True
    )
    Section.objects.create(
        client=client, section_type='contact',
        title='Contáctanos', subtitle='Estamos para ayudarte',
        order=30, is_active=True
    )
    print("✅ Secciones creadas")
else:
    print(f"✅ Ya existen {Section.objects.filter(client=client).count()} secciones")

# Crear servicios si no existen
if not Service.objects.filter(client=client).exists():
    print("\n🛠️  Creando servicios...")
    Service.objects.create(
        client=client, name='Instalaciones Eléctricas', icon='⚡',
        description='Instalaciones residenciales e industriales',
        price_text='Cotizar', order=10, is_active=True, is_featured=True
    )
    Service.objects.create(
        client=client, name='Mantención Preventiva', icon='🔧',
        description='Programas de mantención',
        price_text='Desde $50.000', order=20, is_active=True, is_featured=True
    )
    Service.objects.create(
        client=client, name='Emergencias 24/7', icon='🚨',
        description='Servicio de emergencias',
        price_text='Consultar', order=30, is_active=True, is_featured=False
    )
    print("✅ Servicios creados")
else:
    print(f"✅ Ya existen {Service.objects.filter(client=client).count()} servicios")

# Crear superusuario si no existe
if not User.objects.filter(is_superuser=True).exists():
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@servelec.cl')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123456')
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"\n✅ Superusuario '{username}' creado")
else:
    print("\n✅ Superusuario ya existe")

print("\n🎉 Setup completado!")
PYTHON_SCRIPT

echo ""
echo "=========================================="
echo "  ✅ BUILD COMPLETADO EXITOSAMENTE"
echo "=========================================="