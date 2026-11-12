|__ apps/
|   ├── accounts/
|   │   ├── admin.py
|   │   ├── apps.py
|   │   ├── mixins.py
|   │   ├── models.py
|   │   └── migrations/
|   │
|   ├── core/
|   │   ├── cloudinary_utils.py
|   │   ├── template_resolver.py
|   │   ├── managers.py
|   │   ├── models.py
|   │   └── apps.py
|   │
|   ├── tenants/
|   │   ├── admin.py
|   │   ├── apps.py
|   │   ├── context_processors.py
|   │   ├── managers.py
|   │   ├── middleware.py
|   │   ├── models.py
|   │   ├── signals.py
|   │   ├── template_loader.py
|   │   ├── urls.py
|   │   ├── views.py
|   │   ├── tests.py
|   │   │
|   │   ├── services/
|   │   │   └── email_dispatcher.py
|   │   │
|   │   ├── management/
|   │   │   └── commands/
|   │   │       ├── create_tenant.py
|   │   │       ├── provision_tenant.py
|   │   │       ├── setup_cloudinary_folders.py
|   │   │       ├── check_cloudinary.py
|   │   │       └── otros comandos│   
|   │   │       ├── setup_dev_env.py
|   │   │       └── update_domain.py
|   │   │
|   │   ├── templatetags/
|   │   │   └── tenant_tags.py
|   │   │
|   │   └── migrations/
|   │
|   ├── website/
|   │   ├── admin.py
|   │   ├── auth_views.py
|   │   ├── auth_urls.py
|   │   ├── forms.py
|   │   ├── models.py
|   │   ├── views.py
|   │   ├── urls.py
|   │   │
|   │   ├── templatetags/
|   │   │   ├── website_tags.py
|   │   │   └── cloudinary_tags.py
|   │   │
|   |__ migrations/
|   │
|   |__ __init__.py
| 
├── config/
├── docs/
├── env/
├── media/
├── scripts/
├── static/
├── staticfiles/
├── templates/
|    │   ├── auth/
|    │   ├── components/
|    │   ├── dashboard/
|    │   │   ├── base.html
|    │   │   ├── contact.html
|    │   │   ├── edit_section.html
|    │   │   ├── index.html
|    │   │   ├── sections.html
|    │   │   ├── service_confirm_delete.html
|    │   │   ├── service_form-html
|    |   │   ├── services.html
|    │   ├── emails/
|    │   ├── errors/
|    │   ├── landing/
|    │   │   ├── home.html
|    │   ├── marketing/
|    │   │   |    ├── components/
|    │   │   |    |   ├── about.html
|    │   │   |    |   ├── contact.html
|    │   │   |    |   ├── footer.html
|    │   │   |    |   ├── hero.html
|    │   │   |    |   ├── navbar.html
|    │   │   |    |   ├── services.html
|    │   │   |    ├── landing/
|    │   │   |    |   ├── home.html
|    │   │   |    ├── base.html
|    │   ├── partials/
|    │   ├── tenants/
|    │   │   |    ├── admin/
|    │   │   |    |   ├── onboarding.html
|    │   │   |    |   ├── tenant_list.html
|    │   ├── themes/
|    │   │   ├── _default/
|    │   │   |    ├── components/
|    │   │   |    |   ├── about.html
|    │   │   |    |   ├── contact.html
|    │   │   |    |   ├── footer.html
|    │   │   |    |   ├── hero.html
|    │   │   |    |   ├── navbar.html
|    │   │   |    |   ├── services.html
|    │   │   |    ├── landing/
|    │   │   |    |   ├── home.html
|    │   │   |    ├── base.html
|    │   │   └── electricidad/
|    │   │   |    ├── components/
|    │   │   |    |   ├── about.html
|    │   │   |    |   ├── contact.html
|    │   │   |    |   ├── footer.html
|    │   │   |    |   ├── hero.html
|    │   │   |    |   ├── navbar.html
|    │   │   |    |   ├── services.html
|    │   │   |    ├── landing/
|    │   │   |    |   ├── home.html
|    │   │   |    ├── base.html
|    │___|____base.html
|
|___templates_library


orders/
├── __init__.py
├── apps.py
├── models.py              # Plan, Order, PaymentLog
├── admin.py               # Admin para gestión
├── views.py               # Vistas de checkout (placeholder)
├── urls.py                # URLs de checkout
├── urls_webhooks.py       # URLs de webhooks
├── signals.py             # Signals de logging
├── services/
│   ├── __init__.py
│   ├── order_processor.py      # Lógica de procesamiento
│   └── mercadopago_service.py  # Integración MP (placeholder Card A2)
├── management/
│   └── commands/
│       └── setup_plans.py      # Comando para crear planes
├── migrations/
│   └── __init__.py
└── templates/
    └── orders/
        ├── checkout.html           # Página de checkout
        ├── checkout_success.html   # Confirmación de pago
        └── checkout_error.html     # Error de pago