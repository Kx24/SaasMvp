"""
Management command para actualizar el dominio del cliente
"""
from django.core.management.base import BaseCommand
from apps.tenants.models import Client
import os


class Command(BaseCommand):
    help = 'Actualiza el dominio del cliente con el dominio real de Render'

    def handle(self, *args, **options):
        # Obtener dominio de Render desde variable de entorno
        render_domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
        
        if not render_domain:
            self.stdout.write(self.style.ERROR('❌ RENDER_EXTERNAL_HOSTNAME no configurado'))
            return
        
        # Obtener el primer cliente (o todos)
        clients = Client.objects.all()
        
        if not clients.exists():
            self.stdout.write(self.style.ERROR('❌ No hay clientes en la base de datos'))
            return
        
        for client in clients:
            old_domain = client.domain
            client.domain = render_domain
            client.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'✅ Cliente "{client.name}" actualizado'
            ))
            self.stdout.write(f'   Dominio anterior: {old_domain}')
            self.stdout.write(f'   Dominio nuevo: {client.domain}')