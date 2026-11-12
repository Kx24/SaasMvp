"""
SEC-07 / BOLT-12: los logs no deben contener direcciones de email.

Los logs de Render se retienen y se pueden buscar: un email ahí es un dato
personal fuera de la base (Ley 21.719 art. 14 quinquies) y, en login/reset,
permite enumerar cuentas. Se loguea una referencia estable y no reversible
(`email_ref`) en su lugar.

Tres niveles:
  1. El helper `apps.core.logging_utils.email_ref`.
  2. Flujos reales que hoy logueaban el email (EmailService, reset y login).
  3. Guardia estática sobre todo `apps/`: ninguna llamada a logger interpola
     un nombre que sea un email (`email`, `to_email`, `user.email`, ...).
"""
import ast
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from apps.core.logging_utils import email_ref

EMAIL = 'titular.privado.7q@example.com'
EMAIL_RE = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')


def _joined(cm):
    return '\n'.join(cm.output)


class EmailRefHelperTests(TestCase):
    def test_does_not_contain_the_email(self):
        ref = email_ref(EMAIL)
        self.assertNotIn('@', ref)
        self.assertNotIn('titular', ref)

    def test_is_stable_and_case_insensitive(self):
        self.assertEqual(email_ref(EMAIL), email_ref(f'  {EMAIL.upper()} '))

    def test_distinguishes_different_emails(self):
        self.assertNotEqual(email_ref(EMAIL), email_ref('otra.persona@example.com'))

    def test_handles_empty_values(self):
        self.assertEqual(email_ref(None), 'email:-')
        self.assertEqual(email_ref(''), 'email:-')

    @override_settings(SECRET_KEY='otra-clave-distinta-para-el-test-de-sal-0123456789')
    def test_depends_on_secret_key(self):
        # Sin la sal, un hash plano de un email conocido se puede revertir por diccionario.
        with self.settings(SECRET_KEY=settings.SECRET_KEY):
            first = email_ref(EMAIL)
        with self.settings(SECRET_KEY='clave-completamente-diferente-9876543210-abcdefghij'):
            second = email_ref(EMAIL)
        self.assertNotEqual(first, second)


class EmailServiceLogsTests(TestCase):
    def _send(self, **overrides):
        from apps.orders.services.email_service import EmailService
        with self.settings(**overrides):
            return EmailService()._send_email(
                to_email=EMAIL, subject='Asunto', template_name='set_password',
                context={'user': None, 'set_password_url': 'https://x.test', 'is_reset': True},
            )

    def test_sent_email_log_has_no_address(self):
        with self.assertLogs('apps.orders.services.email_service', level='INFO') as cm:
            self.assertTrue(self._send(EMAIL_ASYNC=False))
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn(EMAIL, _joined(cm))
        self.assertIn(email_ref(EMAIL), _joined(cm))

    def test_queued_email_log_has_no_address(self):
        with self.assertLogs('apps.orders.services.email_service', level='INFO') as cm:
            self.assertTrue(self._send(EMAIL_ASYNC=True))
        self.assertNotIn(EMAIL, _joined(cm))


class AccountsViewsLogsTests(TestCase):
    """`apps/accounts/views.py`: reset de contraseña (alcanzable) y login (§0.4: no se elimina)."""

    HOST = 'logpii.test'

    @classmethod
    def setUpTestData(cls):
        from apps.tenants.models import Client, Domain
        tenant = Client.objects.create(name='Log PII', slug='log-pii', contact_email='c@logpii.test')
        Domain.objects.create(client=tenant, domain=cls.HOST, domain_type='custom',
                              is_primary=True, is_active=True, is_verified=True)
        cls.user = User.objects.create_user(username='titular7q', email=EMAIL, password='Clave-Correcta-123')

    def _login_request(self, email, password):
        from apps.accounts.views import login_view
        request = RequestFactory().post('/auth/login/', {'email': email, 'password': password})
        SessionMiddleware(lambda r: None).process_request(request)
        request.session.save()
        request.user = type('Anon', (), {'is_authenticated': False})()
        setattr(request, '_messages', FallbackStorage(request))
        response = login_view(request)
        return response, [m.message for m in request._messages]

    def test_reset_for_existing_email_logs_no_address(self):
        with self.assertLogs('apps.accounts.views', level='INFO') as cm:
            response = self.client.post(reverse('accounts:forgot_password'), {'email': EMAIL}, HTTP_HOST=self.HOST)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(EMAIL, _joined(cm))

    def test_reset_for_unknown_email_logs_no_address(self):
        unknown = 'no.existe.7q@example.com'
        with self.assertLogs('apps.accounts.views', level='INFO') as cm:
            response = self.client.post(reverse('accounts:forgot_password'), {'email': unknown}, HTTP_HOST=self.HOST)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(unknown, _joined(cm))

    def test_failed_login_logs_no_address(self):
        with self.assertLogs('apps.accounts.views', level='INFO') as cm:
            self._login_request(EMAIL, 'incorrecta')
        self.assertNotIn(EMAIL, _joined(cm))

    def test_wrong_password_and_unknown_email_are_indistinguishable(self):
        with self.assertLogs('apps.accounts.views', level='INFO') as cm_wrong:
            _, msgs_wrong = self._login_request(EMAIL, 'incorrecta')
        with self.assertLogs('apps.accounts.views', level='INFO') as cm_unknown:
            _, msgs_unknown = self._login_request('no.existe.7q@example.com', 'incorrecta')
        self.assertEqual(msgs_wrong, msgs_unknown)
        # Mismo nivel y mismo texto salvo la referencia opaca del email.
        strip = lambda out: [re.sub(r'email:[0-9a-f]+', 'email:X', line) for line in out]  # noqa: E731
        self.assertEqual(strip(cm_wrong.output), strip(cm_unknown.output))


# Nombres que, interpolados en un log, son un email.
_EMAIL_NAMES = {'email', 'to_email', 'buyer_email', 'contact_email', 'notify_email'}


def _expr_is_email(node):
    """True si la expresión interpolada es un email crudo (no envuelto en email_ref)."""
    if isinstance(node, ast.Name):
        return node.id in _EMAIL_NAMES
    if isinstance(node, ast.Attribute):
        return node.attr in _EMAIL_NAMES or node.attr == 'email'
    return False


def _logger_calls_with_email(tree):
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)):
            continue
        if call.func.attr not in {'debug', 'info', 'warning', 'error', 'exception', 'critical'}:
            continue
        owner = call.func.value
        if not (isinstance(owner, ast.Name) and owner.id == 'logger'):
            continue
        for arg in call.args:
            for node in ast.walk(arg):
                if isinstance(node, ast.FormattedValue) and _expr_is_email(node.value):
                    yield call.lineno


class NoEmailInLoggerCallsGuardTest(TestCase):
    def test_no_logger_call_interpolates_an_email(self):
        apps_dir = Path(settings.BASE_DIR) / 'apps'
        offenders = []
        for path in apps_dir.rglob('*.py'):
            rel = path.relative_to(settings.BASE_DIR).as_posix()
            if '/tests' in rel or '/migrations/' in rel:
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'))
            offenders += [f'{rel}:{line}' for line in _logger_calls_with_email(tree)]
        self.assertEqual(offenders, [], 'Llamadas a logger que interpolan un email crudo; usar email_ref()')

    def test_no_logger_call_has_a_literal_email(self):
        apps_dir = Path(settings.BASE_DIR) / 'apps'
        for path in apps_dir.rglob('*.py'):
            rel = path.relative_to(settings.BASE_DIR).as_posix()
            if '/tests' in rel or '/migrations/' in rel:
                continue
            for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                if 'logger.' in line and EMAIL_RE.search(line):
                    self.fail(f'{rel}:{lineno} loguea un email literal')
