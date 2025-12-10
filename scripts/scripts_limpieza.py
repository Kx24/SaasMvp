import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.tenants.models import Client

# Eliminar DB
if os.path.exists('db.sqlite3'):
    os.remove('db.sqlite3')
    print("✅ Base de datos eliminada")

# Eliminar migraciones
migration_files = [
    'apps/website/migrations/0001_initial.py',
    'apps/website/migrations/0002_*.py',
]

for pattern in migration_files:
    import glob
    for file in glob.glob(pattern):
        os.remove(file)
        print(f"✅ {file} eliminado")

print("\nAhora ejecuta:")
print("1. python manage.py migrate")
print("2. python manage.py makemigrations")
print("3. python manage.py migrate")
print("4. python manage.py createsuperuser")