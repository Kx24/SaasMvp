from apps.tenants.models import Client
#------------------ Crear Cliente ------------------#
# Cliente 2 ya existe (default - Servelec)
client2 = Client.objects.get(slug='test-company')
print(f"Cliente 2: {client2.name}")

# Crear Cliente 3
client3 = Client.objects.create(
    name="Servelec",
    slug="Servelec-Ingenieria-3",
    domain="wwww.servelec-ingenieria.cl",
    is_active=True
)
print(f"Cliente 3 creado: {client3.name}")

# Verificar que existen ambos
print(f"\nTotal clientes: {Client.objects.count()}")


#------------------ Crear Contenido cliente 1 ------------------#

from apps.website.models import Section, Service, Testimonial

client1 = Client.objects.get(slug='SaasPrueba')

# IMPORTANTE: Simular que estamos en el contexto del Cliente 1
Section._current_client = client1
Service._current_client = client1
Testimonial._current_client = client1

# Crear secciones para Cliente 1
hero1 = Section.objects.create(
    client=client1,
    key='hero',
    title='SaaS - Soluciones Informaticas',
    content='Expertos en todo tipo de soluciones SaaS',
    is_active=True
)

about1 = Section.objects.create(
    client=client1,
    key='about',
    title='Sobre Saas',
    content='Más de 10 años de experiencia',
    is_active=True
)

# Crear servicios para Cliente 1
service1_1 = Service.objects.create(
    client=client1,
    name='Páginas web',
    description='Diseño e implementaciones',
    icon='desktop_computer',
    is_active=True,
    order=1
)

service1_2 = Service.objects.create(
    client=client1,
    name='Servicios en la nube',
    description='Arquitectura y despliegue',
    icon='nube',
    is_active=True,
    order=2
)

# Crear testimonial para Cliente 1
testimonial1 = Testimonial.objects.create(
    client=client1,
    client_name='Juan Pérez',
    company='Industrias ABC',
    content='Excelente servicio, muy profesionales',
    rating=5,
    is_active=True
)

print(f" Cliente 1 - Secciones: {Section.objects.filter(client=client1).count()}")
print(f" Cliente 1 - Servicios: {Service.objects.filter(client=client1).count()}")
print(f" Cliente 1 - Testimonios: {Testimonial.objects.filter(client=client1).count()}")