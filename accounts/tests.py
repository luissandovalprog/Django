from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Usuario, Rol

class SeguridadVistasTest(TestCase):
    def setUp(self):
        # Crear roles
        self.rol_admin = Rol.objects.create(
            nombre='Admin Sistema', 
            puede_gestionar_usuarios=True,
            puede_ver_dashboard_clinico=False # NO DEBE VER CLÍNICA
        )
        self.rol_matrona = Rol.objects.create(
            nombre='Matrona', 
            puede_ver_dashboard_clinico=True
        )
        
        # Crear usuarios (¡IMPORTANTE: Agregar RUTs únicos!)
        self.usuario_admin = Usuario.objects.create_user(
            username='admin_test', 
            email='admin@test.cl', 
            password='password123', 
            rol=self.rol_admin,
            rut='11111111-1',  # <--- Agregado RUT único
            nombre_completo='Admin Test'
        )
        self.usuario_matrona = Usuario.objects.create_user(
            username='matrona_test', 
            email='matrona@test.cl', 
            password='password123', 
            rol=self.rol_matrona,
            rut='22222222-2',  # <--- Agregado RUT único
            nombre_completo='Matrona Test'
        )

    def test_segregacion_roles(self):
        """Prueba que el Admin NO pueda ver el dashboard clínico"""
        client = Client()
        client.login(username='admin_test', password='password123')
        
        response = client.get(reverse('core:dashboard'))
        
        # Verificar que NO se renderiza la tabla clínica
        # El status code será 200, pero el contenido HTML no debe tener la tabla clínica
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Recién Nacidos Hospitalizados")
        
    def test_acceso_correcto(self):
        """Prueba que la Matrona SÍ vea el dashboard"""
        client = Client()
        client.login(username='matrona_test', password='password123')
        
        response = client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recién Nacidos Hospitalizados")