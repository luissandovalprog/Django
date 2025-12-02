# auditoria/urls.py
"""
URLs de la aplicación auditoría
"""

from django.urls import path
from . import views

app_name = 'auditoria'

urlpatterns = [
    # Vista principal
    path('historial/', views.historial_auditoria, name='historial_auditoria'),
    
    # Exportación
    path('exportar-json/', views.exportar_auditoria_json, name='exportar_json'),
    
    # Estadísticas
    path('estadisticas/', views.estadisticas_auditoria, name='estadisticas'),
    
    # Detalle de log
    path('log/<uuid:log_id>/', views.detalle_log, name='detalle_log'),
    
    # Búsqueda por registro
    path('registro/<str:tabla>/<uuid:registro_id>/', views.buscar_por_registro, name='buscar_por_registro'),
    
    # API JSON para gráficos
    path('api/estadisticas/', views.api_estadisticas_json, name='api_estadisticas'),



    path('debug-ip/', debug_headers_view, name='debug_ip'),
]