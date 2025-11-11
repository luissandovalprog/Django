"""
Comando de Django para inicializar la base de datos con roles GRANULARES
Crea roles y un usuario administrador inicial
"""

from django.core.management.base import BaseCommand
from accounts.models import Rol, Usuario
from django.db import transaction


class Command(BaseCommand):
    help = 'Inicializa la base de datos con roles GRANULARES y usuario administrador'
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Iniciando configuración de la base de datos con RBAC GRANULAR...'))
        
        try:
            with transaction.atomic():
                # ===== ROL: MATRONA CLÍNICA =====
                self.stdout.write('Creando/Actualizando rol: Matrona Clínica...')
                matrona_rol, created = Rol.objects.update_or_create(
                    nombre='Matrona Clínica',
                    defaults={
                        'descripcion': 'Puede crear y modificar partogramas, admisiones de madres, ver dashboard clínico',
                        # Admisiones
                        'puede_crear_admision_madre': True,
                        'puede_editar_admision_madre': False,  # No puede editar
                        # Dashboard
                        'puede_ver_dashboard_clinico': True,
                        'puede_ver_lista_administrativa_madres': False,
                        # Partos
                        'puede_crear_parto': True,
                        'puede_editar_parto': True,
                        'puede_ver_todos_partos': False,  # Solo su turno
                        # Partogramas
                        'puede_crear_editar_partograma': True,
                        # Epicrisis
                        'puede_crear_editar_epicrisis': False,
                        # Reportes y Admin
                        'puede_generar_reportes_rem': False,
                        'puede_ver_auditoria': False,
                        'puede_gestionar_usuarios': False,
                        'puede_eliminar_registros': False,
                        'puede_anexar_correccion': False,
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'  {"Creado" if created else "Actualizado"}: {matrona_rol.nombre}'))
                
                # ===== ROL: MÉDICO =====
                self.stdout.write('Creando/Actualizando rol: Médico...')
                medico_rol, created = Rol.objects.update_or_create(
                    nombre='Médico',
                    defaults={
                        'descripcion': 'Puede crear/editar epicrisis, generar reportes REM, anexar correcciones',
                        # Admisiones
                        'puede_crear_admision_madre': False,
                        'puede_editar_admision_madre': False,
                        # Dashboard
                        'puede_ver_dashboard_clinico': True,
                        'puede_ver_lista_administrativa_madres': False,
                        # Partos
                        'puede_crear_parto': False,
                        'puede_editar_parto': False,
                        'puede_ver_todos_partos': True,  # Ve todos
                        # Partogramas
                        'puede_crear_editar_partograma': False,
                        # Epicrisis
                        'puede_crear_editar_epicrisis': True,
                        # Reportes y Admin
                        'puede_generar_reportes_rem': True,
                        'puede_ver_auditoria': False,
                        'puede_gestionar_usuarios': False,
                        'puede_eliminar_registros': False,
                        'puede_anexar_correccion': True,
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'  {"Creado" if created else "Actualizado"}: {medico_rol.nombre}'))
                
                # ===== ROL: ENFERMERA =====
                self.stdout.write('Creando/Actualizando rol: Enfermera...')
                enfermera_rol, created = Rol.objects.update_or_create(
                    nombre='Enfermera',
                    defaults={
                        'descripcion': 'Similar a Matrona pero solo puede ver/editar partogramas, no crear admisiones',
                        # Admisiones
                        'puede_crear_admision_madre': False,
                        'puede_editar_admision_madre': False,
                        # Dashboard
                        'puede_ver_dashboard_clinico': True,
                        'puede_ver_lista_administrativa_madres': False,
                        # Partos
                        'puede_crear_parto': False,
                        'puede_editar_parto': False,
                        'puede_ver_todos_partos': False,  # Solo su turno
                        # Partogramas
                        'puede_crear_editar_partograma': True,
                        # Epicrisis
                        'puede_crear_editar_epicrisis': False,
                        # Reportes y Admin
                        'puede_generar_reportes_rem': False,
                        'puede_ver_auditoria': False,
                        'puede_gestionar_usuarios': False,
                        'puede_eliminar_registros': False,
                        'puede_anexar_correccion': False,
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'  {"Creado" if created else "Actualizado"}: {enfermera_rol.nombre}'))
                
                # ===== ROL: ADMINISTRATIVO =====
                self.stdout.write('Creando/Actualizando rol: Administrativo...')
                admin_rol, created = Rol.objects.update_or_create(
                    nombre='Administrativo',
                    defaults={
                        'descripcion': 'Crea/edita admisiones de madres, ve dashboard administrativo (solo datos demográficos)',
                        # Admisiones
                        'puede_crear_admision_madre': True,
                        'puede_editar_admision_madre': True,
                        # Dashboard
                        'puede_ver_dashboard_clinico': False,  # NO ve dashboard clínico
                        'puede_ver_lista_administrativa_madres': True,  # Ve tabla administrativa
                        # Partos
                        'puede_crear_parto': False,
                        'puede_editar_parto': False,
                        'puede_ver_todos_partos': False,
                        # Partogramas
                        'puede_crear_editar_partograma': False,
                        # Epicrisis
                        'puede_crear_editar_epicrisis': False,
                        # Reportes y Admin
                        'puede_generar_reportes_rem': False,
                        'puede_ver_auditoria': False,
                        'puede_gestionar_usuarios': False,
                        'puede_eliminar_registros': False,
                        'puede_anexar_correccion': False,
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'  {"Creado" if created else "Actualizado"}: {admin_rol.nombre}'))
                
                # ===== ROL: ADMIN SISTEMA =====
                self.stdout.write('Creando/Actualizando rol: Admin Sistema...')
                admin_sistema_rol, created = Rol.objects.update_or_create(
                    nombre='Admin Sistema',
                    defaults={
                        'descripcion': 'Acceso total a Gestión de Usuarios y Auditoría. NO accede a datos clínicos',
                        # Admisiones
                        'puede_crear_admision_madre': False,
                        'puede_editar_admision_madre': False,
                        # Dashboard
                        'puede_ver_dashboard_clinico': False,  # NO ve datos clínicos
                        'puede_ver_lista_administrativa_madres': False,  # NO ve datos de pacientes
                        # Partos
                        'puede_crear_parto': False,
                        'puede_editar_parto': False,
                        'puede_ver_todos_partos': False,
                        # Partogramas
                        'puede_crear_editar_partograma': False,
                        # Epicrisis
                        'puede_crear_editar_epicrisis': False,
                        # Reportes y Admin
                        'puede_generar_reportes_rem': False,
                        'puede_ver_auditoria': True,  # Acceso total a auditoría
                        'puede_gestionar_usuarios': True,  # Acceso total a gestión usuarios
                        'puede_eliminar_registros': False,
                        'puede_anexar_correccion': False,
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'  {"Creado" if created else "Actualizado"}: {admin_sistema_rol.nombre}'))
                
                # ===== ROL: SUPERVISOR =====
                self.stdout.write('Creando/Actualizando rol: Supervisor...')
                supervisor_rol, created = Rol.objects.update_or_create(
                    nombre='Supervisor',
                    defaults={
                        'descripcion': 'Acceso completo a TODAS las funcionalidades (clínicas y administrativas)',
                        # Admisiones
                        'puede_crear_admision_madre': True,
                        'puede_editar_admision_madre': True,
                        # Dashboard
                        'puede_ver_dashboard_clinico': True,
                        'puede_ver_lista_administrativa_madres': True,
                        # Partos
                        'puede_crear_parto': True,
                        'puede_editar_parto': True,
                        'puede_ver_todos_partos': True,
                        # Partogramas
                        'puede_crear_editar_partograma': True,
                        # Epicrisis
                        'puede_crear_editar_epicrisis': True,
                        # Reportes y Admin
                        'puede_generar_reportes_rem': True,
                        'puede_ver_auditoria': True,
                        'puede_gestionar_usuarios': True,
                        'puede_eliminar_registros': True,
                        'puede_anexar_correccion': True,
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'  {"Creado" if created else "Actualizado"}: {supervisor_rol.nombre}'))
                
                # ===== CREAR USUARIOS DE EJEMPLO =====
                self.stdout.write('\n' + '='*80)
                self.stdout.write('Creando usuarios de ejemplo...')
                
                # Usuario Supervisor
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
                    self.stdout.write(self.style.SUCCESS('  ✓ Usuario supervisor creado'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ Usuario supervisor ya existe'))
                
                # Usuario Matrona
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
                    self.stdout.write(self.style.SUCCESS('  ✓ Usuario matrona1 creado'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ Usuario matrona1 ya existe'))
                
                # Usuario Médico
                if not Usuario.objects.filter(username='medico1').exists():
                    usuario_medico = Usuario.objects.create_user(
                        username='medico1',
                        email='medico1@hospital.cl',
                        password='Hospital2025',
                        nombre_completo='Dr. Médico de Ejemplo',
                        rut='33333333-3',
                        rol=medico_rol,
                        activo=True
                    )
                    self.stdout.write(self.style.SUCCESS('  ✓ Usuario medico1 creado'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ Usuario medico1 ya existe'))
                
                # Usuario Administrativo
                if not Usuario.objects.filter(username='administrativo1').exists():
                    usuario_admin = Usuario.objects.create_user(
                        username='administrativo1',
                        email='administrativo1@hospital.cl',
                        password='Hospital2025',
                        nombre_completo='Administrativo de Ejemplo',
                        rut='44444444-4',
                        rol=admin_rol,
                        activo=True
                    )
                    self.stdout.write(self.style.SUCCESS('  ✓ Usuario administrativo1 creado'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ Usuario administrativo1 ya existe'))
                
                # Usuario Admin Sistema
                if not Usuario.objects.filter(username='adminsistema').exists():
                    usuario_admin_sistema = Usuario.objects.create_user(
                        username='adminsistema',
                        email='adminsistema@hospital.cl',
                        password='Hospital2025',
                        nombre_completo='Administrador del Sistema',
                        rut='55555555-5',
                        rol=admin_sistema_rol,
                        activo=True,
                        is_staff=True
                    )
                    self.stdout.write(self.style.SUCCESS('  ✓ Usuario adminsistema creado'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠ Usuario adminsistema ya existe'))
                
                # ===== RESUMEN =====
                self.stdout.write('\n' + '='*80)
                self.stdout.write(self.style.SUCCESS('¡Base de datos inicializada correctamente con RBAC GRANULAR!'))
                self.stdout.write('\n' + self.style.WARNING('CREDENCIALES DE ACCESO:'))
                self.stdout.write(self.style.SUCCESS('  Supervisor      → usuario: supervisor       / contraseña: Hospital2025'))
                self.stdout.write(self.style.SUCCESS('  Matrona         → usuario: matrona1         / contraseña: Hospital2025'))
                self.stdout.write(self.style.SUCCESS('  Médico          → usuario: medico1          / contraseña: Hospital2025'))
                self.stdout.write(self.style.SUCCESS('  Administrativo  → usuario: administrativo1  / contraseña: Hospital2025'))
                self.stdout.write(self.style.SUCCESS('  Admin Sistema   → usuario: adminsistema     / contraseña: Hospital2025'))
                self.stdout.write('='*80 + '\n')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error durante la inicialización: {str(e)}'))
            raise e