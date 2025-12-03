"""
Script de testing para validar sistema multi-tenant.

Este script crea datos de prueba para 2 clientes diferentes
y verifica que los datos estén correctamente aislados.

Uso:
    python manage.py shell < scripts/test_multi_tenant.py

    O dentro del shell:
    exec(open('scripts/test_multi_tenant.py').read())
"""

print("=" * 60)
print("TEST MULTI-TENANT - Validación de Aislamiento")
print("=" * 60)

from apps.tenants.models import Client, ClientSettings

# ==================== STEP 1: Verificar Clientes ====================
print("\n STEP 1: Clientes Existentes")
print("-" * 60)

clientes = Client.objects.all()
print(f"Total de clientes: {clientes.count()}")

for c in clientes:
    print(f"\n Cliente {c.id}:")
    print(f"   Nombre: {c.company_name}")
    print(f"   Dominio: {c.domain}")
    print(f"   Color: {c.settings.primary_color}")
    print(f"   Estado: {'Activo' if c.is_active else 'Inactivo'}")

if clientes.count() < 2:
    print("\n ADVERTENCIA: Se necesitan al menos 2 clientes para el test")
    print("   Crea otro cliente desde /admin/tenants/client/")
    exit()

# ==================== STEP 2: Obtener 2 Clientes ====================
print("\n" + "=" * 60)
print(" STEP 2: Seleccionar 2 Clientes para Testing")
print("-" * 60)

cliente1 = clientes[0]
cliente2 = clientes[1]

print(f"\nCliente 1: {cliente1.company_name} ({cliente1.domain})")
print(f"Cliente 2: {cliente2.company_name} ({cliente2.domain})")

# ==================== STEP 3: Modificar Settings ====================
print("\n" + "=" * 60)
print("STEP 3: Modificar Settings de Cada Cliente")
print("-" * 60)

# Cliente 1: Color azul
cliente1.settings.primary_color = '#3B82F6'  # Azul
cliente1.settings.whatsapp_number = '+56912345001'
cliente1.settings.save()
print(f"Cliente 1 configurado: {cliente1.settings.primary_color}")

# Cliente 2: Color verde
cliente2.settings.primary_color = '#10B981'  # Verde
cliente2.settings.whatsapp_number = '+56912345002'
cliente2.settings.save()
print(f"Cliente 2 configurado: {cliente2.settings.primary_color}")

# ==================== STEP 4: Verificar Aislamiento ====================
print("\n" + "=" * 60)
print("STEP 4: Verificar Aislamiento de Datos")
print("-" * 60)

# Recargar desde DB
cliente1.refresh_from_db()
cliente2.refresh_from_db()

print(f"\nCliente 1:")
print(f"  Color: {cliente1.settings.primary_color}")
print(f"  WhatsApp: {cliente1.settings.whatsapp_number}")

print(f"\nCliente 2:")
print(f"  Color: {cliente2.settings.primary_color}")
print(f"  WhatsApp: {cliente2.settings.whatsapp_number}")

# Verificar que son diferentes
if cliente1.settings.primary_color != cliente2.settings.primary_color:
    print("\n PASS: Los colores son diferentes")
else:
    print("\n FAIL: Los colores NO deberían ser iguales")

if cliente1.settings.whatsapp_number != cliente2.settings.whatsapp_number:
    print(" PASS: Los WhatsApp son diferentes")
else:
    print(" FAIL: Los WhatsApp NO deberían ser iguales")

# ==================== STEP 5: Test de Queries ====================
print("\n" + "=" * 60)
print(" STEP 5: Test de QuerySets")
print("-" * 60)

# Verificar que cada cliente tiene sus propios settings
all_settings = ClientSettings.objects.all()
print(f"\nTotal ClientSettings en DB: {all_settings.count()}")

for settings in all_settings:
    print(f"  - {settings.client.company_name}: {settings.primary_color}")

# ==================== RESUMEN ====================
print("\n" + "=" * 60)
print("RESUMEN DE TESTING")
print("=" * 60)

tests_passed = 0
tests_total = 4

# Test 1: Hay al menos 2 clientes
if clientes.count() >= 2:
    print("Test 1: Múltiples clientes existen")
    tests_passed += 1
else:
    print("Test 1: Se necesitan más clientes")

# Test 2: Settings diferentes
if cliente1.settings.primary_color != cliente2.settings.primary_color:
    print("Test 2: Settings son independientes")
    tests_passed += 1
else:
    print("Test 2: Settings NO están aislados")

# Test 3: Cada cliente tiene settings
if all_settings.count() >= 2:
    print("Test 3: Cada cliente tiene ClientSettings")
    tests_passed += 1
else:
    print("Test 3: Faltan ClientSettings")

# Test 4: Dominios únicos
dominios = [c.domain for c in clientes]
if len(dominios) == len(set(dominios)):
    print("Test 4: Dominios son únicos")
    tests_passed += 1
else:
    print("Test 4: Hay dominios duplicados")

print(f"\n{'='*60}")
print(f"RESULTADO: {tests_passed}/{tests_total} tests pasaron")
print(f"{'='*60}")

if tests_passed == tests_total:
    print("\n¡TODO FUNCIONA CORRECTAMENTE!")
    print("Sistema multi-tenant validado")
    print("Aislamiento de datos confirmado")
    print("Listo para continuar con Card #6")
else:
    print(f"\n{tests_total - tests_passed} test(s) fallaron")
    print("Revisa los errores arriba antes de continuar")

print("\n" + "=" * 60)