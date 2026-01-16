apps/
├── accounts/
│   ├── admin.py
│   ├── apps.py
│   ├── mixins.py
│   ├── models.py
│   └── migrations/
│
├── core/
│   ├── cloudinary_utils.py
│   ├── template_resolver.py
│   ├── managers.py
│   ├── models.py
│   └── apps.py
│
├── tenants/
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── managers.py
│   ├── middleware.py
│   ├── models.py
│   ├── signals.py
│   ├── template_loader.py
│   ├── urls.py
│   ├── views.py
│   ├── tests.py
│   │
│   ├── services/
│   │   └── email_dispatcher.py
│   │
│   ├── management/
│   │   └── commands/
│   │       ├── create_tenant.py
│   │       ├── provision_tenant.py
│   │       ├── setup_cloudinary_folders.py
│   │       ├── check_cloudinary.py
│   │       └── otros comandos
│   │
│   ├── templatetags/
│   │   └── tenant_tags.py
│   │
│   └── migrations/
│
├── website/
│   ├── admin.py
│   ├── auth_views.py
│   ├── auth_urls.py
│   ├── forms.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   │
│   ├── templatetags/
│   │   ├── website_tags.py
│   │   └── cloudinary_tags.py
│   │
│   └── migrations/
│
|__ __init__.py
|
├── templates/
│   ├── auth/
│   ├── components/
│   ├── dashboard/
│   │   ├── base.html
│   │   ├── contact.html
│   │   ├── edit_section.html
│   │   ├── index.html
│   │   ├── sections.html
│   │   ├── service_confirm_delete.html
│   │   ├── service_form-html
|   │   ├── services.html
│   ├── emails/
│   ├── errors/
│   ├── landing/
│   │   ├── home.html
│   ├── partials/
│   ├── tenants/
│   │   ├── _default/
│   │   |    ├── components/
│   │   |    |   ├── about.html
│   │   |    |   ├── contact.html
│   │   |    |   ├── footer.html
│   │   |    |   ├── hero.html
│   │   |    |   ├── navbar.html
│   │   |    |   ├── services.html
│   │   |    ├── dashboard/
│   │   |    ├── landing/
│   │   |    |   ├── home.html
│   │   |    ├── base.html
│   │   └── andesscale/
│   │   |    ├── components/
│   │   |    |   ├── about.html
│   │   |    |   ├── contact.html
│   │   |    |   ├── footer.html
│   │   |    |   ├── hero.html
│   │   |    |   ├── navbar.html
│   │   |    |   ├── services.html
│   │   |    ├── dashboard/
│   │   |    ├── landing/
│   │   |    |   ├── home.html
│   │   |    ├── base.html
│   │   ├── servelec-ingenieria/
│   │   |    ├── components/
│   │   |    |   ├── about.html
│   │   |    |   ├── contact.html
│   │   |    |   ├── footer.html
│   │   |    |   ├── hero.html
│   │   |    |   ├── navbar.html
│   │   |    |   ├── services.html
│   │   |    ├── dashboard/
│   │   |    ├── landing/
│   │   |    |   ├── home.html
│   │   |    ├── base.html
│   ├── base.html
│   ├── /
