"""
Management command para probar el aislamiento multi-tenant.

Uso:
    python manage.py test_isolation
    python manage.py test_isolation --clean  (limpia y recrea datos)
"""

from django.core.management.base import BaseCommand
from apps.tenants.models import Client
from apps.website.models import Section, Service, ContactSubmission


class Command(BaseCommand):
    help = 'Prueba el aislamiento de datos multi-tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Limpiar datos existentes antes de crear',
        )

    def handle(self, *args, **options):
        """Ejecutar tests de aislamiento"""

        SUCCESS = self.style.SUCCESS
        WARNING = self.style.WARNING
        ERROR = self.style.ERROR
        HEADER = self.style.HTTP_INFO

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(HEADER("TESTING DE AISLAMIENTO MULTI-TENANT"))
        self.stdout.write("=" * 60 + "\n")

        # Limpieza si se solicita (solo los clientes de prueba de este comando)
        if options['clean']:
            self.stdout.write(WARNING("Limpiando datos existentes..."))
            Section.objects.filter(client__slug__in=['isolation-test-1', 'isolation-test-2']).delete()
            Service.objects.filter(client__slug__in=['isolation-test-1', 'isolation-test-2']).delete()
            ContactSubmission.objects.filter(client__slug__in=['isolation-test-1', 'isolation-test-2']).delete()
            self.stdout.write(SUCCESS("Datos limpiados\n"))

        # Configurar clientes
        self.stdout.write(HEADER("CONFIGURANDO CLIENTES"))
        self.stdout.write("-" * 60)

        client1, _ = Client.objects.get_or_create(
            slug='isolation-test-1',
            defaults={'name': 'Isolation Test 1', 'is_active': True}
        )
        self.stdout.write(f"Cliente 1: {client1.name} ({client1.slug})")

        client2, created = Client.objects.get_or_create(
            slug='isolation-test-2',
            defaults={'name': 'Isolation Test 2', 'is_active': True}
        )
        if created:
            client2.settings.company_name = "Isolation Test 2 Inc."
            client2.settings.save()

        self.stdout.write(f"Cliente 2: {client2.name} ({client2.slug})")
        self.stdout.write(f"Total clientes: {Client.objects.count()}\n")

        # Crear contenido solo si se limpiaron datos
        if options['clean']:
            self._create_test_data(client1, client2)

        # Ejecutar tests
        self._run_tests(client1, client2)

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(SUCCESS("TODAS LAS PRUEBAS COMPLETADAS"))
        self.stdout.write("=" * 60 + "\n")

    def _create_test_data(self, client1, client2):
        """Crear datos de prueba para ambos clientes"""
        SUCCESS = self.style.SUCCESS
        HEADER = self.style.HTTP_INFO

        # Cliente 1
        self.stdout.write(HEADER("\nCREANDO CONTENIDO PARA CLIENTE 1"))
        self.stdout.write("-" * 60)

        Section._current_client = client1
        Service._current_client = client1

        Section.objects.create(
            client=client1, section_type='hero',
            title='Mi Empresa - Soluciones Profesionales',
            subtitle='Expertos en soluciones empresariales',
            is_active=True
        )
        Section.objects.create(
            client=client1, section_type='about',
            title='Sobre Nosotros', is_active=True
        )

        Service.objects.create(
            client=client1, name='Consultoria Empresarial',
            description='Asesoria estrategica', icon='star',
            is_active=True, is_featured=True
        )
        Service.objects.create(
            client=client1, name='Desarrollo de Software',
            description='Soluciones tecnologicas', icon='cog',
            is_active=True
        )

        self.stdout.write(SUCCESS(
            f"Secciones: {Section.objects.for_client(client1).count()}, "
            f"Servicios: {Service.objects.for_client(client1).count()}"
        ))

        # Cliente 2
        self.stdout.write(HEADER("\nCREANDO CONTENIDO PARA CLIENTE 2"))
        self.stdout.write("-" * 60)

        Section._current_client = client2
        Service._current_client = client2

        Section.objects.create(
            client=client2, section_type='hero',
            title='Test Company - Testing Services', is_active=True
        )
        Section.objects.create(
            client=client2, section_type='about',
            title='About Test Company', is_active=True
        )
        Section.objects.create(
            client=client2, section_type='features',
            title='Our Features', is_active=True
        )

        Service.objects.create(
            client=client2, name='QA Testing',
            description='Quality assurance', icon='check',
            is_active=True, is_featured=True
        )
        Service.objects.create(
            client=client2, name='Automation Testing',
            description='Automated tests', icon='robot', is_active=True
        )
        Service.objects.create(
            client=client2, name='Performance Testing',
            description='Load testing', icon='bolt', is_active=True
        )

        self.stdout.write(SUCCESS(
            f"Secciones: {Section.objects.for_client(client2).count()}, "
            f"Servicios: {Service.objects.for_client(client2).count()}"
        ))

    def _run_tests(self, client1, client2):
        """Ejecutar batería de tests de aislamiento"""
        SUCCESS = self.style.SUCCESS
        ERROR = self.style.ERROR
        HEADER = self.style.HTTP_INFO

        self.stdout.write(HEADER("\nPRUEBAS DE AISLAMIENTO"))
        self.stdout.write("-" * 60)

        # Test 1: Conteo por cliente vía for_client() (bypassea el filtro de
        # _current_client, útil para verificar que cada cliente tiene lo suyo).
        # Nota: TenantAwareManager.get_queryset() SIEMPRE filtra por
        # `_current_client` (o devuelve vacío si no hay ninguno seteado) --
        # no existe una vía "sin filtrar" vía `objects`, por eso no se compara
        # contra un total global "de toda la DB".
        c1_sections = Section.objects.for_client(client1).count()
        c1_services = Service.objects.for_client(client1).count()
        c2_sections = Section.objects.for_client(client2).count()
        c2_services = Service.objects.for_client(client2).count()

        self.stdout.write(f"\nPor Cliente:")
        self.stdout.write(f"  Cliente 1: {c1_sections} secciones, {c1_services} servicios")
        self.stdout.write(f"  Cliente 2: {c2_sections} secciones, {c2_services} servicios")

        if c1_sections > 0 and c2_sections > 0:
            self.stdout.write(SUCCESS("  OK: ambos clientes tienen secciones propias"))
        else:
            self.stdout.write(ERROR("  FAIL: algún cliente quedó sin secciones (¿corriste con --clean?)"))

        if c1_services > 0 and c2_services > 0:
            self.stdout.write(SUCCESS("  OK: ambos clientes tienen servicios propios"))
        else:
            self.stdout.write(ERROR("  FAIL: algún cliente quedó sin servicios (¿corriste con --clean?)"))

        # Test 3: Tenant Aware Manager
        Section._current_client = client1
        count1 = Section.objects.count()
        Section._current_client = client2
        count2 = Section.objects.count()

        self.stdout.write(f"\nTenant Aware Manager:")
        self.stdout.write(f"  Contexto Cliente 1: {count1} secciones")
        self.stdout.write(f"  Contexto Cliente 2: {count2} secciones")

        if count1 == c1_sections and count2 == c2_sections:
            self.stdout.write(SUCCESS("  OK: manager filtra correctamente"))
        else:
            self.stdout.write(ERROR("  FAIL: manager NO filtra correctamente"))

        # Test 4: Acceso cruzado
        service2 = Service.objects.for_client(client2).first()
        if service2:
            Service._current_client = client1
            try:
                Service.objects.get(id=service2.id)
                self.stdout.write(ERROR("\nFAIL: Cliente 1 puede ver datos del Cliente 2"))
            except Service.DoesNotExist:
                self.stdout.write(SUCCESS("\nOK: Cliente 1 NO puede ver datos del Cliente 2"))

        # Test 5: Auto-generación de slugs
        self.stdout.write(f"\nSlugs auto-generados (Cliente 1):")
        for s in Service.objects.for_client(client1):
            self.stdout.write(f"  '{s.name}' -> '{s.slug}'")

        # Verificar slugs únicos
        slugs = list(Service.objects.for_client(client1).values_list('slug', flat=True))
        if len(slugs) == len(set(slugs)):
            self.stdout.write(SUCCESS("  OK: todos los slugs son únicos"))
        else:
            self.stdout.write(ERROR("  FAIL: hay slugs duplicados"))
