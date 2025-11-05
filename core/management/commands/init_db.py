"""
Comando de Django para inicializar la base de datos con datos de prueba
Crea roles y un usuario administrador inicial
"""

from django.core.management.base import BaseCommand
from accounts.models import Rol, Usuario
from django.db import transaction


class Command(BaseCommand):
    help = 'Inicializa la base de datos con roles y usuario administrador'
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando configuración de la base de datos...'))
        
        try:
            with transaction.atomic():
                # Crear roles
                self.stdout.write('Creando roles...')
                
                # Rol: Matrona Clínica
                matrona_rol, created = Rol.objects.get_or_create(
                    nombre='Matrona Clínica',
                    defaults={
                        'descripcion': 'Puede crear y modificar registros de partos de su turno',
                        'puede_crear_partos': True,
                        'puede_editar_partos': True,
                        'puede_eliminar_partos': False,
                        'puede_ver_todos_partos': False,
                        'puede_generar_reportes': False,
                        'puede_gestionar_usuarios': False,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Rol creado: {matrona_rol.nombre}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  Rol ya existe: {matrona_rol.nombre}'))
                
                # Rol: Supervisor/Jefe de Área
                supervisor_rol, created = Rol.objects.get_or_create(
                    nombre='Supervisor',
                    defaults={
                        'descripcion': 'Acceso completo a todos los datos y generación de reportes',
                        'puede_crear_partos': True,
                        'puede_editar_partos': True,
                        'puede_eliminar_partos': True,
                        'puede_ver_todos_partos': True,
                        'puede_generar_reportes': True,
                        'puede_gestionar_usuarios': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  Rol creado: {supervisor_rol.nombre}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  Rol ya existe: {supervisor_rol.nombre}'))
                
                # Crear usuario supervisor inicial
                self.stdout.write('\nCreando usuario supervisor inicial...')
                
                if not Usuario.objects.filter(username='supervisor').exists():
                    usuario_supervisor = Usuario.objects.create_user(
                        username='supervisor',
                        email='supervisor@hospital.cl',
                        password='Hospital2025',
                        nombre_completo='Supervisor del Sistema',
                        rut='11111111-1',
                        rol=supervisor_rol,
                        activo=True,
                        is_staff=True
                    )
                    self.stdout.write(self.style.SUCCESS('  Usuario supervisor creado exitosamente'))
                    self.stdout.write(self.style.SUCCESS('  Usuario: supervisor'))
                    self.stdout.write(self.style.SUCCESS('  Contraseña: Hospital2025'))
                else:
                    self.stdout.write(self.style.WARNING('  Usuario supervisor ya existe'))
                
                # Crear usuario matrona de ejemplo
                self.stdout.write('\nCreando usuario matrona de ejemplo...')
                
                if not Usuario.objects.filter(username='matrona1').exists():
                    usuario_matrona = Usuario.objects.create_user(
                        username='matrona1',
                        email='matrona1@hospital.cl',
                        password='Hospital2025',
                        nombre_completo='Matrona de Ejemplo',
                        rut='22222222-2',
                        rol=matrona_rol,
                        activo=True
                    )
                    self.stdout.write(self.style.SUCCESS('  Usuario matrona creado exitosamente'))
                    self.stdout.write(self.style.SUCCESS('  Usuario: matrona1'))
                    self.stdout.write(self.style.SUCCESS('  Contraseña: Hospital2025'))
                else:
                    self.stdout.write(self.style.WARNING('  Usuario matrona ya existe'))
                
                self.stdout.write(self.style.SUCCESS('\n¡Base de datos inicializada correctamente!'))
                self.stdout.write(self.style.SUCCESS('\nCredenciales de acceso:'))
                self.stdout.write(self.style.SUCCESS('  Supervisor - Usuario: supervisor / Contraseña: Hospital2025'))
                self.stdout.write(self.style.SUCCESS('  Matrona - Usuario: matrona1 / Contraseña: Hospital2025'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la inicialización: {str(e)}'))
            raise e
