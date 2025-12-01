\# SaaS Landing MVP - Multi-Tenant



Sistema multi-tenant para crear landing pages autoadministrables.



\## Stack

\- Django 5.2.6

\- PostgreSQL (prod) / SQLite (dev)

\- Tailwind CSS

\- Cloudinary

\- Render



\## Setup Local

```bash

\# Crear virtualenv

python -m venv env

env\\Scripts\\activate



\# Instalar dependencias

pip install -r requirements.txt



\# Configurar .env

cp .env.example .env



\# Migrar

python manage.py migrate



\# Crear superuser

python manage.py createsuperuser



\# Correr

python manage.py runserver

```



\## Estructura



\- `apps/tenants/` - Multi-tenancy core

\- `apps/website/` - Landing pages CMS

\- `apps/accounts/` - User management

\- `apps/core/` - Shared utilities



\## Roadmap



\- \[x] Card #1: Setup inicial

\- \[x] Card #2: Estructura del proyecto

\- \[ ] Card #3: Modelos multi-tenant

\- \[ ] Card #4: Middleware

\- \[ ] Card #5: Testing inicial

