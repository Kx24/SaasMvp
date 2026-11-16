"""
BOLT-37 (CONS-11, parte 2): MercadoPagoService sin red.

El SDK `mercadopago.SDK` se sustituye por un MagicMock: ningún test llega a
la API real de Mercado Pago.
"""
import hashlib
import hmac
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from apps.orders.services.mercadopago_service import (
    MercadoPagoError,
    MercadoPagoService,
)

MP_SETTINGS = dict(
    MP_ACCESS_TOKEN='test-token',
    MP_PUBLIC_KEY='pub',
    MP_WEBHOOK_SECRET='shh',
    DEBUG=False,
)


def _service():
    with patch('apps.orders.services.mercadopago_service.mercadopago.SDK') as sdk_cls:
        service = MercadoPagoService()
    service.sdk = sdk_cls.return_value
    return service


def _pay(service, **kwargs):
    params = dict(token='tok', amount=10000, email='a@b.cl', description='Plan')
    params.update(kwargs)
    return service.process_payment(**params)


@override_settings(**MP_SETTINGS)
class InitTests(SimpleTestCase):
    def test_sin_access_token_lanza_config_error(self):
        with override_settings(MP_ACCESS_TOKEN=''):
            with self.assertRaises(MercadoPagoError) as ctx:
                MercadoPagoService()
        self.assertEqual(ctx.exception.code, 'CONFIG_ERROR')

    def test_init_guarda_config_y_crea_sdk(self):
        with patch('apps.orders.services.mercadopago_service.mercadopago.SDK') as sdk_cls:
            service = MercadoPagoService()
        sdk_cls.assert_called_once_with('test-token')
        self.assertEqual(service.public_key, 'pub')
        self.assertEqual(service.webhook_secret, 'shh')


@override_settings(**MP_SETTINGS)
class ProcessPaymentTests(SimpleTestCase):
    def test_validaciones_de_entrada(self):
        service = _service()
        for kwargs, code in (
            (dict(token=''), 'INVALID_TOKEN'),
            (dict(amount=0), 'INVALID_AMOUNT'),
            (dict(amount=-5), 'INVALID_AMOUNT'),
            (dict(email=''), 'INVALID_EMAIL'),
        ):
            with self.assertRaises(MercadoPagoError) as ctx:
                _pay(service, **kwargs)
            self.assertEqual(ctx.exception.code, code)
        service.sdk.payment.assert_not_called()

    def test_pago_aprobado(self):
        service = _service()
        service.sdk.payment.return_value.create.return_value = {
            'status': 201,
            'response': {
                'id': 999, 'status': 'approved', 'status_detail': 'accredited',
                'payment_method_id': 'visa', 'payment_type_id': 'credit_card',
            },
        }
        result = _pay(
            service, payment_method_id='visa', external_reference='ORD-1',
            payer_name='Ana Maria Perez', installments=3,
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['payment_id'], '999')
        self.assertEqual(result['status'], 'approved')
        self.assertEqual(result['message'], '¡Pago aprobado!')
        self.assertEqual(result['payment_method_id'], 'visa')
        payload = service.sdk.payment.return_value.create.call_args[0][0]
        self.assertEqual(payload['transaction_amount'], 10000.0)
        self.assertEqual(payload['installments'], 3)
        self.assertEqual(payload['payment_method_id'], 'visa')
        self.assertEqual(payload['external_reference'], 'ORD-1')
        self.assertEqual(payload['payer']['first_name'], 'Ana')
        self.assertEqual(payload['payer']['last_name'], 'Maria Perez')

    def test_payer_name_de_una_palabra_no_define_apellido(self):
        service = _service()
        service.sdk.payment.return_value.create.return_value = {
            'status': 201, 'response': {'id': 1, 'status': 'approved'},
        }
        _pay(service, payer_name='Ana')
        payer = service.sdk.payment.return_value.create.call_args[0][0]['payer']
        self.assertEqual(payer['first_name'], 'Ana')
        self.assertNotIn('last_name', payer)

    def test_idempotency_key_se_pasa_como_request_options(self):
        service = _service()
        service.sdk.payment.return_value.create.return_value = {
            'status': 200, 'response': {'id': 1, 'status': 'approved'},
        }
        _pay(service, idempotency_key='key-1')
        args = service.sdk.payment.return_value.create.call_args[0]
        self.assertEqual(args[1], {'idempotency_key': 'key-1'})

    def test_pago_rechazado_usa_mensaje_de_rechazo(self):
        cases = {
            'cc_rejected_insufficient_amount': 'Fondos insuficientes',
            'cc_rejected_bad_filled_security_code': 'Código de seguridad incorrecto',
            'cc_rejected_call_for_authorize': 'Debes autorizar el pago con tu banco',
            'detalle_desconocido': 'Pago rechazado. Intenta con otra tarjeta.',
        }
        for detail, message in cases.items():
            service = _service()
            service.sdk.payment.return_value.create.return_value = {
                'status': 201,
                'response': {'id': 5, 'status': 'rejected', 'status_detail': detail},
            }
            result = _pay(service)
            self.assertFalse(result['success'])
            self.assertEqual(result['status'], 'rejected')
            self.assertEqual(result['status_detail'], detail)
            self.assertEqual(result['message'], message)

    def test_pago_pendiente(self):
        service = _service()
        service.sdk.payment.return_value.create.return_value = {
            'status': 201,
            'response': {'id': 7, 'status': 'pending', 'status_detail': 'pending_contingency'},
        }
        result = _pay(service)
        self.assertFalse(result['success'])
        self.assertEqual(result['status'], 'pending')
        self.assertEqual(result['message'], 'Pago pendiente de confirmación')

    def test_respuesta_de_error_del_sdk_lanza_mercadopago_error(self):
        service = _service()
        service.sdk.payment.return_value.create.return_value = {
            'status': 400,
            'response': {'message': 'invalid token', 'cause': [{'code': 1}]},
        }
        with self.assertRaises(MercadoPagoError) as ctx:
            _pay(service)
        # Bug destapado por BOLT-37: el except referenciaba
        # `mercadopago.exceptions` (no existe en el SDK) y esta rama
        # terminaba en AttributeError en vez de MercadoPagoError.
        self.assertEqual(ctx.exception.code, '400')
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(ctx.exception.message, 'invalid token')
        self.assertEqual(ctx.exception.details, {'cause': [{'code': 1}]})

    def test_excepcion_de_red_lanza_mercadopago_error(self):
        service = _service()
        service.sdk.payment.return_value.create.side_effect = ConnectionError('sin red')
        with self.assertRaises(MercadoPagoError) as ctx:
            _pay(service)
        self.assertEqual(ctx.exception.code, 'UNEXPECTED_ERROR')
        self.assertIn('sin red', ctx.exception.message)


@override_settings(**MP_SETTINGS)
class GetPaymentTests(SimpleTestCase):
    def test_sin_id_devuelve_none_sin_llamar_al_sdk(self):
        service = _service()
        self.assertIsNone(service.get_payment(''))
        service.sdk.payment.assert_not_called()

    def test_encontrado(self):
        service = _service()
        service.sdk.payment.return_value.get.return_value = {
            'status': 200,
            'response': {
                'id': 42, 'status': 'approved', 'status_detail': 'accredited',
                'transaction_amount': 10000, 'payer': {'email': 'a@b.cl'},
                'external_reference': 'ORD-1',
            },
        }
        data = service.get_payment('42')
        self.assertEqual(data['payment_id'], '42')
        self.assertEqual(data['status'], 'approved')
        self.assertEqual(data['amount'], 10000)
        self.assertEqual(data['email'], 'a@b.cl')
        self.assertEqual(data['external_reference'], 'ORD-1')

    def test_no_encontrado(self):
        service = _service()
        service.sdk.payment.return_value.get.return_value = {
            'status': 404, 'response': {'message': 'not found'},
        }
        self.assertIsNone(service.get_payment('42'))

    def test_excepcion_devuelve_none(self):
        service = _service()
        service.sdk.payment.return_value.get.side_effect = TimeoutError('t/o')
        self.assertIsNone(service.get_payment('42'))


@override_settings(**MP_SETTINGS)
class RefundTests(SimpleTestCase):
    def test_reembolso_total_no_envia_monto(self):
        service = _service()
        service.sdk.refund.return_value.create.return_value = {
            'status': 201, 'response': {'id': 3, 'status': 'approved', 'amount': 10000},
        }
        result = service.refund_payment('42')
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_id'], '3')
        service.sdk.refund.return_value.create.assert_called_once_with('42', {})

    def test_reembolso_parcial_envia_monto(self):
        service = _service()
        service.sdk.refund.return_value.create.return_value = {
            'status': 201, 'response': {'id': 4, 'status': 'approved', 'amount': 2500},
        }
        result = service.refund_payment('42', amount=2500)
        self.assertTrue(result['success'])
        self.assertEqual(result['amount'], 2500)
        service.sdk.refund.return_value.create.assert_called_once_with(
            '42', {'amount': 2500.0},
        )

    def test_reembolso_rechazado_por_api(self):
        service = _service()
        service.sdk.refund.return_value.create.return_value = {
            'status': 400, 'response': {'message': 'ya reembolsado'},
        }
        result = service.refund_payment('42')
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'ya reembolsado')

    def test_reembolso_con_excepcion(self):
        service = _service()
        service.sdk.refund.return_value.create.side_effect = ConnectionError('caída')
        result = service.refund_payment('42')
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], 'caída')


@override_settings(**MP_SETTINGS)
class WebhookSignatureTests(SimpleTestCase):
    def _request(self, signature=None, request_id='req-1', data_id='42'):
        headers = {'HTTP_X_REQUEST_ID': request_id}
        if signature is not None:
            headers['HTTP_X_SIGNATURE'] = signature
        return RequestFactory().post(f'/webhook/?data.id={data_id}', **headers)

    def _sign(self, ts='1700', request_id='req-1', data_id='42', secret='shh'):
        manifest = f'id:{data_id};request-id:{request_id};ts:{ts};'
        return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()

    def test_firma_valida(self):
        service = _service()
        header = f'ts=1700,v1={self._sign()}'
        self.assertTrue(service.validate_webhook_signature(self._request(header)))

    def test_firma_invalida(self):
        service = _service()
        header = f'ts=1700,v1={self._sign(secret="otro")}'
        self.assertFalse(service.validate_webhook_signature(self._request(header)))

    def test_sin_cabecera(self):
        service = _service()
        self.assertFalse(service.validate_webhook_signature(self._request()))

    def test_formato_invalido(self):
        service = _service()
        for header in ('ts=1700', 'basura', 'ts=,v1='):
            self.assertFalse(service.validate_webhook_signature(self._request(header)))

    def test_sin_secreto_fuera_de_debug_rechaza(self):
        with override_settings(MP_WEBHOOK_SECRET='', DEBUG=False):
            service = _service()
            self.assertFalse(service.validate_webhook_signature(self._request()))

    def test_sin_secreto_en_debug_acepta(self):
        with override_settings(MP_WEBHOOK_SECRET='', DEBUG=True):
            service = _service()
            self.assertTrue(service.validate_webhook_signature(self._request()))


@override_settings(**MP_SETTINGS)
class MessagesAndMethodsTests(SimpleTestCase):
    def test_status_messages(self):
        service = _service()
        self.assertEqual(service._get_status_message('cancelled', ''), 'Pago cancelado')
        self.assertEqual(service._get_status_message('refunded', ''), 'Pago reembolsado')
        self.assertEqual(
            service._get_status_message('rejected', 'cc_rejected_card_disabled'),
            'Tarjeta deshabilitada',
        )
        self.assertEqual(service._get_status_message('x', ''), 'Estado: x')

    def test_get_payment_methods(self):
        service = _service()
        service.sdk.payment_methods.return_value.list_all.return_value = {
            'status': 200, 'response': [{'id': 'visa'}],
        }
        self.assertEqual(service.get_payment_methods(), [{'id': 'visa'}])

    def test_get_payment_methods_error_o_excepcion(self):
        service = _service()
        service.sdk.payment_methods.return_value.list_all.return_value = {'status': 500}
        self.assertEqual(service.get_payment_methods(), [])
        service.sdk.payment_methods.return_value.list_all.side_effect = ConnectionError()
        self.assertEqual(service.get_payment_methods(), [])
