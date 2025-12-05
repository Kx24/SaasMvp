"""
Script para crear datos de prueba para FernandoIngeniería.

Crea contenido para portafolio/servicios profesionales.

Uso:
    python manage.py shell
    exec(open('scripts/seed_fernando.py', encoding='utf-8').read())
"""

print("=" * 70)
print("SEED DATA - FernandoIngeniería")
print("=" * 70)

from apps.tenants.models import Client
from apps.website.models import Section, Service, Testimonial

# ==================== OBTENER CLIENTE ====================
print("\n[1/4] Obteniendo cliente Fernando...")

try:
    # Intentar obtener por nombre (ajusta si es necesario)
    fernando = Client.objects.filter(
        company_name__icontains='Fernando'
    ).first()
    
    if not fernando:
        # Si no existe, buscar el segundo cliente
        fernando = Client.objects.all()[1]
    
    print(f"OK Cliente encontrado: {fernando.company_name}")
except Exception as e:
    print(f"ERROR: No se pudo obtener el cliente: {e}")
    exit()

# ==================== LIMPIAR DATOS EXISTENTES ====================
print("\n[2/4] Limpiando datos existentes de Fernando...")

Section.objects.filter(client=fernando).delete()
Service.objects.filter(client=fernando).delete()
Testimonial.objects.filter(client=fernando).delete()

print("OK Datos anteriores eliminados")

# ==================== CREAR SECCIONES ====================
print("\n[3/4] Creando secciones...")

# Sección Hero
hero = Section.objects.create(
    client=fernando,
    section_type='hero',
    title='Desarrollo Web & Consultoría Digital',
    subtitle='Transformo ideas en soluciones digitales innovadoras',
    content='''
        <p>Especialista en desarrollo web full-stack y consultoría tecnológica 
        para empresas que buscan innovar.</p>
    ''',
    cta_text='Ver Portafolio',
    cta_url='#portfolio',
    is_active=True,
    order=0
)
print(f"  OK Hero creado: {hero.title}")

# Sección About
about = Section.objects.create(
    client=fernando,
    section_type='about',
    title='Sobre Mí',
    subtitle='Ingeniero en TI con pasión por la tecnología',
    content='''
        <p>Soy <strong>Fernando</strong>, ingeniero especializado en desarrollo 
        web y soluciones digitales.</p>
        
        <p>Con más de 5 años de experiencia, ayudo a empresas a:</p>
        <ul>
            <li>Digitalizar sus procesos</li>
            <li>Crear presencia web profesional</li>
            <li>Optimizar sus sistemas existentes</li>
            <li>Implementar soluciones a medida</li>
        </ul>
        
        <p>Trabajo con tecnologías modernas: Python, Django, React, y más.</p>
    ''',
    is_active=True,
    order=1
)
print(f"  OK About creado: {about.title}")

# Sección Services
services_section = Section.objects.create(
    client=fernando,
    section_type='services',
    title='Servicios',
    subtitle='Soluciones tecnológicas adaptadas a tus necesidades',
    content='',
    is_active=True,
    order=2
)
print(f"  OK Services Section creada")

# Sección Portfolio
portfolio = Section.objects.create(
    client=fernando,
    section_type='portfolio',
    title='Proyectos Destacados',
    subtitle='Algunos de mis trabajos recientes',
    content='''
        <p>He trabajado en diversos proyectos para diferentes industrias, 
        desde e-commerce hasta sistemas de gestión empresarial.</p>
    ''',
    is_active=True,
    order=3
)
print(f"  OK Portfolio creado")

# Sección Contact
contact = Section.objects.create(
    client=fernando,
    section_type='contact',
    title='Trabajemos Juntos',
    subtitle='¿Tienes un proyecto en mente?',
    content='''
        <p>Cuéntame sobre tu proyecto y veamos cómo puedo ayudarte a 
        hacerlo realidad.</p>
    ''',
    is_active=True,
    order=4
)
print(f"  OK Contact creado")

print(f"\nTotal secciones creadas: {Section.objects.filter(client=fernando).count()}")

# ==================== CREAR SERVICIOS ====================
print("\n[4/4] Creando servicios...")

# Servicio 1: Desarrollo Web
servicio1 = Service.objects.create(
    client=fernando,
    name='Desarrollo Web Full-Stack',
    description='''
        <p>Creación de aplicaciones web completas desde cero.</p>
        
        <ul>
            <li>Frontend moderno con React/Vue</li>
            <li>Backend robusto con Django/Node.js</li>
            <li>Base de datos optimizada</li>
            <li>Deploy en cloud (AWS, Render, Vercel)</li>
        </ul>
    ''',
    icon='fa-code',
    price=1500000.00,
    price_label='Desde',
    is_featured=True,
    is_active=True,
    order=0
)
print(f"  OK Servicio 1: {servicio1.name}")

# Servicio 2: Landing Pages
servicio2 = Service.objects.create(
    client=fernando,
    name='Landing Pages Profesionales',
    description='''
        <p>Páginas web autoadministrables para tu negocio.</p>
        
        <ul>
            <li>Diseño moderno y responsive</li>
            <li>SEO optimizado</li>
            <li>Panel de administración</li>
            <li>Formularios de contacto</li>
        </ul>
    ''',
    icon='fa-laptop',
    price=600000.00,
    price_label='Desde',
    is_featured=True,
    is_active=True,
    order=1
)
print(f"  OK Servicio 2: {servicio2.name}")

# Servicio 3: Consultoría
servicio3 = Service.objects.create(
    client=fernando,
    name='Consultoría Tecnológica',
    description='''
        <p>Asesoría para optimizar tus procesos digitales.</p>
        
        <ul>
            <li>Auditoría de sistemas existentes</li>
            <li>Recomendaciones de arquitectura</li>
            <li>Plan de digitalización</li>
            <li>Capacitación de equipos</li>
        </ul>
    ''',
    icon='fa-lightbulb',
    price=80000.00,
    price_label='Por hora',
    is_featured=False,
    is_active=True,
    order=2
)
print(f"  OK Servicio 3: {servicio3.name}")

print(f"\nTotal servicios creados: {Service.objects.filter(client=fernando).count()}")

# ==================== CREAR TESTIMONIOS ====================
print("\nCreando testimonios...")

# Testimonio 1
testimonio1 = Testimonial.objects.create(
    client=fernando,
    client_name='Ana López',
    client_role='CEO, StartupXYZ',
    testimonial='''
        Fernando desarrolló nuestra plataforma web y superó todas nuestras 
        expectativas. Muy profesional, creativo y siempre disponible. 
        Altamente recomendado.
    ''',
    rating=5,
    is_active=True,
    is_featured=True
)
print(f"  OK Testimonio 1: {testimonio1.client_name}")

# Testimonio 2
testimonio2 = Testimonial.objects.create(
    client=fernando,
    client_name='Roberto Silva',
    client_role='Gerente General, Comercial ABC',
    testimonial='''
        Excelente trabajo en nuestra landing page. El sitio quedó impecable, 
        moderno y muy fácil de administrar. Gran profesional.
    ''',
    rating=5,
    is_active=True,
    is_featured=True
)
print(f"  OK Testimonio 2: {testimonio2.client_name}")

print(f"\nTotal testimonios creados: {Testimonial.objects.filter(client=fernando).count()}")

# ==================== RESUMEN ====================
print("\n" + "=" * 70)
print("RESUMEN - FernandoIngeniería")
print("=" * 70)

print(f"\nSecciones: {Section.objects.filter(client=fernando).count()}")
for section in Section.objects.filter(client=fernando):
    print(f"  - {section.get_section_type_display()}: {section.title}")

print(f"\nServicios: {Service.objects.filter(client=fernando).count()}")
for service in Service.objects.filter(client=fernando):
    featured = "⭐" if service.is_featured else "  "
    print(f"  {featured} {service.name}")

print(f"\nTestimonios: {Testimonial.objects.filter(client=fernando).count()}")
for testimonial in Testimonial.objects.filter(client=fernando):
    print(f"  - {testimonial.client_name} ({testimonial.rating}⭐)")

print("\n" + "=" * 70)
print("OK SEED COMPLETADO PARA FERNANDO")
print("=" * 70)