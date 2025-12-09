from django.core.management.base import BaseCommand
from apps.tenants.models import Client

class Command(BaseCommand):
    help = 'Crea cliente para desarrollo en localhost'

    def handle(self, *args, **options):
        client, created = Client.objects.get_or_create(
            domain="127.0.0.1:8000",
            defaults={
                'name': 'Servelec Ingeniería',
                'is_active': True
            }
        )
        
        if created:
            # Configurar settings
            client.settings.primary_color = "#2563eb"
            client.settings.secondary_color = "#1e40af"
            client.settings.company_name = "Servelec Ingeniería"
            client.settings.contact_email = "contacto@servelec.cl"
            client.settings.contact_phone = "+56 9 1234 5678"
            client.settings.save()
            
            self.stdout.write(
                self.style.SUCCESS(f' Cliente creado: {client.name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f' Cliente ya existe: {client.name}')
            )