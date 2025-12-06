"""
Modelos de la aplicación Accounts
Sistema de autenticación con RBAC GRANULAR
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _

class Rol(models.Model):
    """
    Modelo de Roles para sistema RBAC GRANULAR
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
    # ===== PERMISOS GRANULARES =====
    
    # Admisiones de Madres
    puede_crear_admision_madre = models.BooleanField(default=False)
    puede_editar_admision_madre = models.BooleanField(default=False)
    
    # Dashboard y Visualización
    puede_ver_lista_administrativa_madres = models.BooleanField(default=False)
    puede_ver_dashboard_clinico = models.BooleanField(default=False)
    
    # Partos
    puede_crear_parto = models.BooleanField(default=False)
    puede_editar_parto = models.BooleanField(default=False)
    puede_ver_todos_partos = models.BooleanField(
        default=False, 
        help_text="Si no está marcado, solo ve sus propios registros"
    )
    
    # Partogramas
    puede_crear_editar_partograma = models.BooleanField(default=False)
    
    # Epicrisis
    puede_crear_editar_epicrisis = models.BooleanField(default=False)
    
    # Reportes REM
    puede_generar_reportes_rem = models.BooleanField(default=False)
    
    # Auditoría y Gestión
    puede_ver_auditoria = models.BooleanField(default=False)
    puede_gestionar_usuarios = models.BooleanField(default=False)
    
    # Eliminación (Solo Supervisor)
    puede_eliminar_registros = models.BooleanField(default=False)
    
    # Anexar correcciones (Solo Médicos)
    puede_anexar_correccion = models.BooleanField(
        default=False, 
        help_text="Permiso para anexar correcciones (ej. Médico)"
    )
    
    class Meta:
        db_table = 'Rol'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    """
    Manager personalizado para el modelo Usuario
    """
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('El usuario debe tener un nombre de usuario')
        if not email:
            raise ValueError('El usuario debe tener un email')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('activo', True)
        
        return self.create_user(username, email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado con RBAC GRANULAR
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = models.CharField(max_length=255, unique=True, verbose_name='RUT')
    nombre_completo = models.TextField(verbose_name='Nombre Completo')
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True, verbose_name='Nombre de Usuario')
    
    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        related_name='usuarios',
        verbose_name='Rol',
        null=True
    )
    
    activo = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    require_2fa = models.BooleanField(default=False, verbose_name='Requiere 2FA', help_text='Si está activado, el usuario debe usar autenticación de dos factores')
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'nombre_completo', 'rut']
    
    class Meta:
        db_table = 'Usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.nombre_completo} ({self.username})"
    
    def has_perm(self, perm, obj=None):
        """Verifica permisos personalizados basados en rol"""
        if self.is_superuser:
            return True
        return super().has_perm(perm, obj)
    
    def has_module_perms(self, app_label):
        """Permisos de módulo"""
        if self.is_superuser:
            return True
        return super().has_module_perms(app_label)
    
    # ===== PROPIEDADES DE PERMISOS GRANULARES =====
    
    @property
    def puede_crear_admision_madre(self):
        if self.is_superuser:
            return True
        return self.rol.puede_crear_admision_madre if self.rol else False
    
    @property
    def puede_editar_admision_madre(self):
        if self.is_superuser:
            return True
        return self.rol.puede_editar_admision_madre if self.rol else False
    
    @property
    def puede_ver_lista_administrativa_madres(self):
        if self.is_superuser:
            return False  # Admin Sistema NO ve datos clínicos
        return self.rol.puede_ver_lista_administrativa_madres if self.rol else False
    
    @property
    def puede_ver_dashboard_clinico(self):
        if self.is_superuser:
            return False  # Admin Sistema NO ve datos clínicos
        return self.rol.puede_ver_dashboard_clinico if self.rol else False
    
    @property
    def puede_crear_parto(self):
        if self.is_superuser:
            return True
        return self.rol.puede_crear_parto if self.rol else False
    
    @property
    def puede_editar_parto(self):
        if self.is_superuser:
            return True
        return self.rol.puede_editar_parto if self.rol else False
    
    @property
    def puede_ver_todos_partos(self):
        if self.is_superuser:
            return True
        return self.rol.puede_ver_todos_partos if self.rol else False
    
    @property
    def puede_crear_editar_partograma(self):
        if self.is_superuser:
            return True
        return self.rol.puede_crear_editar_partograma if self.rol else False
    
    @property
    def puede_crear_editar_epicrisis(self):
        if self.is_superuser:
            return True
        return self.rol.puede_crear_editar_epicrisis if self.rol else False
    
    @property
    def puede_generar_reportes_rem(self):
        if self.is_superuser:
            return True
        return self.rol.puede_generar_reportes_rem if self.rol else False
    
    @property
    def puede_ver_auditoria(self):
        if self.is_superuser:
            return True
        return self.rol.puede_ver_auditoria if self.rol else False
    
    @property
    def puede_gestionar_usuarios(self):
        if self.is_superuser:
            return True
        return self.rol.puede_gestionar_usuarios if self.rol else False
    
    @property
    def puede_eliminar_registros(self):
        if self.is_superuser:
            return True
        return self.rol.puede_eliminar_registros if self.rol else False
    
    @property
    def puede_anexar_correccion(self):
        if self.is_superuser:
            return True
        return self.rol.puede_anexar_correccion if self.rol else False
    
    # ===== PROPIEDADES LEGACY (mantener compatibilidad) =====
    
    @property
    def puede_crear_partos(self):
        """Alias para compatibilidad"""
        return self.puede_crear_parto
    
    @property
    def puede_editar_partos(self):
        """Alias para compatibilidad"""
        return self.puede_editar_parto
    
    @property
    def puede_generar_reportes(self):
        """Alias para compatibilidad"""
        return self.puede_generar_reportes_rem