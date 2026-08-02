# apps/accounts/management/commands/audit_tenant_emails.py
"""
Audita que cada usuario de tenant tenga email válido y único por tenant.
Uso: python manage.py audit_tenant_emails --settings=config.settings.production
"""
from collections import defaultdict
from django.core.management.base import BaseCommand
from apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = "Detecta usuarios sin email o con email duplicado dentro de un mismo tenant."

    def handle(self, *args, **options):
        profiles = UserProfile.objects.select_related('user', 'client').all()

        by_tenant = defaultdict(list)
        for p in profiles:
            by_tenant[p.client_id].append(p)

        problems = 0
        for client_id, plist in by_tenant.items():
            client_name = plist[0].client.slug if plist[0].client else f"client#{client_id}"
            seen = defaultdict(list)

            for p in plist:
                email = (p.user.email or '').lower().strip()
                if not email:
                    problems += 1
                    self.stdout.write(self.style.ERROR(
                        f"[{client_name}] SIN EMAIL → user='{p.user.username}' (id={p.user_id})"
                    ))
                    continue
                seen[email].append(p.user.username)

            for email, usernames in seen.items():
                if len(usernames) > 1:
                    problems += 1
                    self.stdout.write(self.style.ERROR(
                        f"[{client_name}] EMAIL DUPLICADO '{email}' → {', '.join(usernames)}"
                    ))

        if problems == 0:
            self.stdout.write(self.style.SUCCESS("OK — todos los usuarios tienen email único por tenant."))
        else:
            self.stdout.write(self.style.WARNING(f"\n{problems} problema(s) a resolver antes del cutover."))