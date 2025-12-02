"""
Tests para TenantMiddleware.

Los signals crean automáticamente ClientSettings, por lo que
no debemos crearlos manualmente en setUp.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from .models import Client, ClientSettings
from .middleware import TenantMiddleware


class TenantMiddlewareTestCase(TestCase):
    """Tests para el middleware multi-tenant."""
    
    def setUp(self):
        """
        Configuración inicial para cada test.
        
        IMPORTANTE: No creamos ClientSettings manualmente porque
        el signal post_save lo hace automáticamente.
        """
        # Crear cliente de prueba
        # El signal creará automáticamente sus ClientSettings
        self.client_obj = Client.objects.create(
            name='Test Client',
            domain='test.com',
            company_name='Test Company',
            contact_email='test@test.com',
            contact_phone='+56900000000',
            is_active=True
        )
        
        # Verificar que el signal creó los settings
        # Esto es solo para confirmar que funcionó
        self.assertTrue(
            hasattr(self.client_obj, 'settings'),
            "El signal debería haber creado ClientSettings automáticamente"
        )
        
        # Factory para crear requests simulados
        self.factory = RequestFactory()
        
        # Crear middleware con función dummy
        def dummy_view(request):
            """Vista dummy que no hace nada."""
            return None
        
        self.middleware = TenantMiddleware(dummy_view)
    
    def test_middleware_injects_client(self):
        """
        Test que el middleware inyecta request.client correctamente.
        
        Simula un request a 'test.com' y verifica que:
        1. request.client existe
        2. request.client tiene el dominio correcto
        """
        # Simular request HTTP
        request = self.factory.get('/', HTTP_HOST='test.com')
        request.user = AnonymousUser()
        
        # Ejecutar middleware
        self.middleware(request)
        
        # Verificaciones
        self.assertTrue(
            hasattr(request, 'client'),
            "El middleware debería inyectar request.client"
        )
        self.assertEqual(
            request.client.domain,
            'test.com',
            "El cliente debería tener el dominio correcto"
        )
        self.assertEqual(
            request.client.company_name,
            'Test Company',
            "El nombre de la empresa debería coincidir"
        )
    
    def test_localhost_uses_first_client(self):
        """
        Test que localhost usa el primer cliente activo.
        
        En desarrollo, cuando accedes vía localhost,
        el middleware debe usar el primer cliente activo.
        """
        # Simular request a localhost
        request = self.factory.get('/', HTTP_HOST='localhost')
        request.user = AnonymousUser()
        
        # Ejecutar middleware
        self.middleware(request)
        
        # Verificaciones
        self.assertTrue(
            hasattr(request, 'client'),
            "El middleware debería inyectar un cliente para localhost"
        )
        self.assertIsNotNone(
            request.client,
            "El cliente no debería ser None"
        )
        self.assertTrue(
            request.client.is_active,
            "El cliente debería estar activo"
        )
    
    def test_inactive_client_returns_error(self):
        """
        Test que cliente inactivo no se usa.
        
        Si un cliente está marcado como inactivo (is_active=False),
        el middleware debería retornar un error 404.
        """
        # Desactivar el cliente
        self.client_obj.is_active = False
        self.client_obj.save()
        
        # Simular request
        request = self.factory.get('/', HTTP_HOST='test.com')
        request.user = AnonymousUser()
        
        # Ejecutar middleware
        response = self.middleware(request)
        
        # Verificaciones
        self.assertIsNotNone(
            response,
            "El middleware debería retornar una respuesta de error"
        )
        self.assertEqual(
            response.status_code,
            404,
            "El código de estado debería ser 404 (Not Found)"
        )
    
    def test_nonexistent_domain_returns_404(self):
        """
        Test que dominio inexistente retorna 404.
        
        Si el dominio no existe en la base de datos,
        el middleware debe retornar error 404.
        """
        # Simular request a dominio inexistente
        request = self.factory.get('/', HTTP_HOST='dominio-inexistente.com')
        request.user = AnonymousUser()
        
        # Ejecutar middleware
        response = self.middleware(request)
        
        # Verificaciones
        self.assertIsNotNone(
            response,
            "El middleware debería retornar una respuesta de error"
        )
        self.assertEqual(
            response.status_code,
            404,
            "Dominio inexistente debería retornar 404"
        )
    
    def test_client_settings_exist(self):
        """
        Test que ClientSettings se crean automáticamente.
        
        Verifica que el signal post_save funciona correctamente
        y crea ClientSettings cuando se crea un Client.
        """
        # El cliente ya fue creado en setUp
        # Verificar que tiene settings
        self.assertTrue(
            hasattr(self.client_obj, 'settings'),
            "El cliente debería tener settings"
        )
        
        # Verificar valores por defecto
        self.assertEqual(
            self.client_obj.settings.primary_color,
            '#3B82F6',
            "El color primario por defecto debería ser azul Tailwind"
        )
        self.assertEqual(
            self.client_obj.settings.secondary_color,
            '#1E40AF',
            "El color secundario por defecto debería ser azul oscuro"
        )


class ClientModelTestCase(TestCase):
    """Tests para el modelo Client."""
    
    def test_client_creation(self):
        """
        Test creación básica de cliente.
        """
        client = Client.objects.create(
            name='Test Company',
            domain='testcompany.com',
            company_name='Test Company Inc',
            contact_email='info@testcompany.com',
            contact_phone='+56912345678'
        )
        
        # Verificaciones básicas
        self.assertEqual(client.domain, 'testcompany.com')
        self.assertTrue(client.is_active)
        self.assertFalse(client.setup_completed)
        
        # Verificar que slug se genera automáticamente
        self.assertEqual(client.slug, 'test-company')
    
    def test_client_settings_autocreated(self):
        """
        Test que ClientSettings se crea automáticamente via signal.
        """
        client = Client.objects.create(
            name='Another Test',
            domain='anothertest.com',
            company_name='Another Test Inc',
            contact_email='test@test.com',
            contact_phone='+56900000000'
        )
        
        # Verificar que settings existe
        self.assertTrue(hasattr(client, 'settings'))
        
        # Verificar que es una instancia de ClientSettings
        self.assertIsInstance(client.settings, ClientSettings)
    
    def test_client_str_representation(self):
        """
        Test representación en string del cliente.
        """
        client = Client.objects.create(
            name='String Test',
            domain='stringtest.com',
            company_name='String Test Company',
            contact_email='test@test.com',
            contact_phone='+56900000000'
        )
        
        expected = "String Test Company (stringtest.com)"
        self.assertEqual(str(client), expected)