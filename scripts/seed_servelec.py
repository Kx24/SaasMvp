"""
Script para crear datos de prueba para Servelec Ingeniería.

Este script crea contenido completo para la landing page de Servelec:
- Secciones (Hero, About, Services, Contact)
- Servicios ofrecidos
- Testimonios de clientes

Uso:
    python manage.py shell
    exec(open('scripts/seed_servelec.py', encoding='utf-8').read())
"""

print("=" * 70)
print("SEED DATA - Servelec Ingeniería")
print("=" * 70)

from apps.tenants.models import Client
from apps.website.models import Section, Service, Testimonial

# ==================== OBTENER CLIENTE ====================
print("\n[1/4] Obteniendo cliente Servelec...")

try:
    servelec = Client.objects.get(domain='servelec-ingenieria.cl')
    print(f"OK Cliente encontrado: {servelec.company_name}")
except Client.DoesNotExist:
    print("ERROR: Cliente Servelec no existe")
    print("Crea el cliente desde /admin/tenants/client/ primero")
    exit()

# ==================== LIMPIAR DATOS EXISTENTES ====================
print("\n[2/4] Limpiando datos existentes de Servelec...")

# Borrar datos previos para evitar duplicados
Section.objects.filter(client=servelec).delete()
Service.objects.filter(client=servelec).delete()
Testimonial.objects.filter(client=servelec).delete()

print("OK Datos anteriores eliminados")

# ==================== CREAR SECCIONES ====================
print("\n[3/4] Creando secciones...")

# Sección Hero (Banner Principal)
hero = Section.objects.create(
    client=servelec,
    section_type='hero',
    title='Soluciones Eléctricas Profesionales',
    subtitle='Más de 20 años brindando servicios eléctricos de calidad en Chile',
    content='''
        <p>Especialistas en instalaciones eléctricas industriales, comerciales y 
        residenciales. Contamos con personal certificado y equipos de última generación.</p>
    ''',
    cta_text='Solicitar Cotización',
    cta_url='/contacto',
    is_active=True,
    order=0
)
print(f"  OK Hero creado: {hero.title}")

# Sección About (Sobre Nosotros)
about = Section.objects.create(
    client=servelec,
    section_type='about',
    title='Sobre Nosotros',
    subtitle='Experiencia y profesionalismo a tu servicio',
    content='''
        <p><strong>Servelec Ingeniería</strong> es una empresa chilena con más de 
        20 años de experiencia en el rubro eléctrico.</p>
        
        <p>Nos especializamos en:</p>
        <ul>
            <li>Instalaciones eléctricas industriales</li>
            <li>Proyectos eléctricos comerciales</li>
            <li>Mantención preventiva y correctiva</li>
            <li>Asesoría técnica especializada</li>
        </ul>
        
        <p>Nuestro equipo de profesionales certificados garantiza trabajos de 
        alta calidad cumpliendo todas las normativas vigentes.</p>
    ''',
    is_active=True,
    order=1
)
print(f"  OK About creado: {about.title}")

# Sección Services (Contenedor de servicios)
services_section = Section.objects.create(
    client=servelec,
    section_type='services',
    title='Nuestros Servicios',
    subtitle='Soluciones integrales para todas tus necesidades eléctricas',
    content='',
    is_active=True,
    order=2
)
print(f"  OK Services Section creada: {services_section.title}")

# Sección Contact
contact = Section.objects.create(
    client=servelec,
    section_type='contact',
    title='Contáctanos',
    subtitle='Estamos para servirte',
    content='''
        <p>¿Necesitas una cotización? ¿Tienes alguna consulta?</p>
        <p>Completa el formulario y te responderemos a la brevedad.</p>
    ''',
    is_active=True,
    order=3
)
print(f"  OK Contact creado: {contact.title}")

print(f"\nTotal secciones creadas: {Section.objects.filter(client=servelec).count()}")

# ==================== CREAR SERVICIOS ====================
print("\n[4/4] Creando servicios...")

# Servicio 1: Instalaciones Eléctricas
servicio1 = Service.objects.create(
    client=servelec,
    name='Instalaciones Eléctricas Industriales',
    description='''
        <p>Diseño, instalación y mantención de sistemas eléctricos para plantas 
        industriales y fábricas.</p>
        
        <ul>
            <li>Tableros eléctricos industriales</li>
            <li>Sistemas de iluminación LED</li>
            <li>Instalación de maquinaria</li>
            <li>Certificación SEC</li>
        </ul>
    ''',
    icon='fa-industry',
    price=500000.00,
    price_label='Desde',
    is_featured=True,
    is_active=True,
    order=0
)
print(f"  OK Servicio 1: {servicio1.name}")

# Servicio 2: Proyectos Eléctricos
servicio2 = Service.objects.create(
    client=servelec,
    name='Proyectos Eléctricos Comerciales',
    description='''
        <p>Ejecución de proyectos eléctricos para edificios comerciales, oficinas 
        y locales comerciales.</p>
        
        <ul>
            <li>Diseño de proyectos eléctricos</li>
            <li>Instalaciones completas</li>
            <li>Sistemas de emergencia</li>
            <li>Climatización y control</li>
        </ul>
    ''',
    icon='fa-building',
    price=800000.00,
    price_label='Desde',
    is_featured=True,
    is_active=True,
    order=1
)
print(f"  OK Servicio 2: {servicio2.name}")

# Servicio 3: Mantención
servicio3 = Service.objects.create(
    client=servelec,
    name='Mantención Preventiva y Correctiva',
    description='''
        <p>Servicio de mantención programada para garantizar el correcto 
        funcionamiento de tus instalaciones eléctricas.</p>
        
        <ul>
            <li>Inspección termográfica</li>
            <li>Medición de aislación</li>
            <li>Limpieza de tableros</li>
            <li>Informes técnicos detallados</li>
        </ul>
    ''',
    icon='fa-tools',
    price=250000.00,
    price_label='Desde',
    is_featured=False,
    is_active=True,
    order=2
)
print(f"  OK Servicio 3: {servicio3.name}")

# Servicio 4: Asesoría
servicio4 = Service.objects.create(
    client=servelec,
    name='Asesoría Técnica Especializada',
    description='''
        <p>Consultoría y asesoría técnica en proyectos eléctricos de cualquier 
        envergadura.</p>
        
        <ul>
            <li>Análisis de consumos eléctricos</li>
            <li>Optimización energética</li>
            <li>Cumplimiento normativo</li>
            <li>Capacitación de personal</li>
        </ul>
    ''',
    icon='fa-lightbulb',
    price=150000.00,
    price_label='Por hora',
    is_featured=False,
    is_active=True,
    order=3
)
print(f"  OK Servicio 4: {servicio4.name}")

print(f"\nTotal servicios creados: {Service.objects.filter(client=servelec).count()}")

# ==================== CREAR TESTIMONIOS ====================
print("\nCreando testimonios...")

# Testimonio 1
testimonio1 = Testimonial.objects.create(
    client=servelec,
    client_name='Juan Pérez Soto',
    client_role='Gerente de Operaciones, Industrias XYZ',
    testimonial='''
        Excelente servicio. El equipo de Servelec instaló todo el sistema eléctrico 
        de nuestra nueva planta en tiempo récord y con la más alta calidad. 
        Muy profesionales y comprometidos.
    ''',
    rating=5,
    is_active=True,
    is_featured=True
)
print(f"  OK Testimonio 1: {testimonio1.client_name}")

# Testimonio 2
testimonio2 = Testimonial.objects.create(
    client=servelec,
    client_name='María González',
    client_role='Administradora, Edificio Los Pinos',
    testimonial='''
        Llevamos 3 años con el servicio de mantención de Servelec y estamos 
        muy conformes. Siempre puntuales, ordenados y con informes detallados. 
        Los recomiendo al 100%.
    ''',
    rating=5,
    is_active=True,
    is_featured=True
)
print(f"  OK Testimonio 2: {testimonio2.client_name}")

# Testimonio 3
testimonio3 = Testimonial.objects.create(
    client=servelec,
    client_name='Carlos Muñoz',
    client_role='Jefe de Mantención, Mall Plaza Sur',
    testimonial='''
        Profesionales de primer nivel. Solucionaron un problema crítico en 
        nuestro sistema eléctrico en tiempo récord. Muy agradecidos por su 
        rápida respuesta y eficiencia.
    ''',
    rating=5,
    is_active=True,
    is_featured=False
)
print(f"  OK Testimonio 3: {testimonio3.client_name}")

print(f"\nTotal testimonios creados: {Testimonial.objects.filter(client=servelec).count()}")

# ==================== RESUMEN ====================
print("\n" + "=" * 70)
print("RESUMEN - Servelec Ingeniería")
print("=" * 70)

print(f"\nSecciones: {Section.objects.filter(client=servelec).count()}")
for section in Section.objects.filter(client=servelec):
    print(f"  - {section.get_section_type_display()}: {section.title}")

print(f"\nServicios: {Service.objects.filter(client=servelec).count()}")
for service in Service.objects.filter(client=servelec):
    featured = "⭐" if service.is_featured else "  "
    print(f"  {featured} {service.name}")

print(f"\nTestimonios: {Testimonial.objects.filter(client=servelec).count()}")
for testimonial in Testimonial.objects.filter(client=servelec):
    print(f"  - {testimonial.client_name} ({testimonial.rating}⭐)")

print("\n" + "=" * 70)
print("OK SEED COMPLETADO PARA SERVELEC")
print("=" * 70)