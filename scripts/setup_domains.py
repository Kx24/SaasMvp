# -*- coding: utf-8 -*-
"""
Script para crear dominios iniciales - Compatible Windows
Ejecutar: python manage.py shell
Luego: exec(open('scripts/setup_domains.py', encoding='utf-8').read())
"""

from apps.tenants.models import Client, Domain
from django.conf import settings

def setup_domains():
    base_domain = getattr(settings, 'BASE_DOMAIN', 'localhost')
    
    print("Verificando dominios de clientes...")
    print("-" * 50)
    
    created = 0
    existing = 0
    
    for client in Client.objects.all():
        if client.domains.exists():
            domains = list(client.domains.values_list('domain', flat=True))
            print(f"[OK] {client.name}: {', '.join(domains)}")
            existing += 1
        else:
            subdomain = f"{client.slug}.{base_domain}"
            
            if Domain.objects.filter(domain=subdomain).exists():
                print(f"[SKIP] {client.name}: {subdomain} ya asignado a otro")
                continue
            
            Domain.objects.create(
                client=client,
                domain=subdomain,
                domain_type='subdomain',
                is_primary=True,
                is_active=True,
                is_verified=True,
            )
            print(f"[NEW] {client.name}: {subdomain}")
            created += 1
    
    print("-" * 50)
    print(f"Resumen: {existing} existentes, {created} creados")
    print(f"Total dominios: {Domain.objects.count()}")

setup_domains()
