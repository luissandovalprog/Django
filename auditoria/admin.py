"""
Configuración del Admin de Django para Auditoría
"""

from django.contrib import admin
from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'tabla_afectada', 'ip_usuario', 'fecha_accion')
    list_filter = ('accion', 'tabla_afectada', 'fecha_accion')
    search_fields = ('usuario__username', 'accion')
    readonly_fields = ('usuario', 'accion', 'tabla_afectada', 'registro_id_uuid', 'ip_usuario', 'fecha_accion')
    date_hierarchy = 'fecha_accion'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    