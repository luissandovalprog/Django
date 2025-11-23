from django.test import TestCase
from core.models import Madre
from utils.crypto import crypto_service

class MadreModelTest(TestCase):
    def test_encriptacion_datos_sensibles(self):
        """Verifica que los datos se guarden encriptados en la BD"""
        rut_real = "12.345.678-9"
        nombre_real = "Maria Perez"
        
        madre = Madre.objects.create(
            fecha_nacimiento="1990-01-01",
            nacionalidad="Chilena"
        )
        # Usamos los setters que implementaste
        madre.set_rut(rut_real)
        madre.set_nombre(nombre_real)
        madre.save()
        
        # Recuperar desde la BD "cruda"
        madre_bd = Madre.objects.get(pk=madre.pk)
        
        # 1. Verificar que en BD NO esté el texto plano (Seguridad)
        self.assertNotEqual(madre_bd.rut_encrypted, rut_real)
        self.assertNotEqual(madre_bd.nombre_encrypted, nombre_real)
        
        # 2. Verificar que al desencriptar obtengamos el valor original (Integridad)
        self.assertEqual(madre_bd.get_rut(), rut_real)
        self.assertEqual(madre_bd.get_nombre(), nombre_real)