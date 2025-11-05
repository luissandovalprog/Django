"""
Configuración del Admin de Django para Accounts
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Rol, Usuario


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'puede_crear_partos', 'puede_generar_reportes')
    search_fields = ('nombre',)
    list_filter = ('puede_crear_partos', 'puede_generar_reportes')


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'nombre_completo', 'rol', 'activo')
    list_filter = ('activo', 'is_staff', 'rol')
    search_fields = ('username', 'email', 'nombre_completo')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('nombre_completo', 'rut', 'email')}),
        ('Permisos', {'fields': ('rol', 'activo', 'is_staff', 'is_superuser')}),
        ('Fechas Importantes', {'fields': ('last_login', 'fecha_creacion', 'fecha_modificacion')}),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_modificacion', 'last_login')
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nombre_completo', 'rut', 'rol', 'password1', 'password2'),
        }),
    )
