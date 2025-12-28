"""
Script de migración de datos: Domain model

Este script debe ejecutarse DESPUÉS de aplicar la migración que crea el modelo Domain.

Uso:
    python manage.py shell < scripts/migrate_domains.py
    
O ejecutar en el shell:
    python manage.py shell
    >>> exec(open('scripts/migrate_domains.py').read())
"""

from apps.tenants.models import Client, Domain

def migrate_domains():
    """
    Migra el campo 'domain' de Client al nuevo modelo Domain.
    """
    print("🔄 Iniciando migración de dominios...")
    
    clients_with_domain = Client.objects.exclude(domain__isnull=True).exclude(domain='')
    migrated = 0
    skipped = 0
    
    for client in clients_with_domain:
        old_domain = getattr(client, 'domain', None)
        
        if not old_domain:
            continue
        
        # Verificar si ya existe
        if Domain.objects.filter(domain=old_domain).exists():
            print(f"  ⏭️  Saltando {old_domain} (ya existe)")
            skipped += 1
            continue
        
        # Crear nuevo Domain
        domain = Domain.objects.create(
            client=client,
            domain=old_domain,
            is_primary=True,
            is_active=True,
            is_verified=True,
        )
        
        print(f"  ✅ Migrado: {old_domain} → Cliente: {client.name}")
        migrated += 1
    
    print(f"\n📊 Resumen:")
    print(f"   Migrados: {migrated}")
    print(f"   Saltados: {skipped}")
    print(f"   Total clientes: {Client.objects.count()}")
    print(f"   Total dominios: {Domain.objects.count()}")
    
    return migrated, skipped


if __name__ == '__main__' or True:  # True para ejecutar en shell
    migrate_domains()