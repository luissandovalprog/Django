"""
URLs del sistema de notificaciones
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Endpoint para obtener conteo (usado en el badge)
    path('api/conteo/', views.obtener_conteo_notificaciones, name='api_conteo'),
    
    # Endpoint para obtener lista (usado en el dropdown)
    path('api/lista/', views.obtener_lista_notificaciones, name='api_lista'),
    
    # Endpoint para marcar como leída
    path('api/marcar-leida/', views.marcar_notificacion_leida, name='api_marcar_leida'),
    
    # Endpoint para marcar todas como leídas
    path('api/marcar-todas-leidas/', views.marcar_todas_leidas, name='api_marcar_todas_leidas'),
    
    # Endpoint para eliminar notificación
    path('api/eliminar/', views.eliminar_notificacion, name='api_eliminar'),
    
    # Vista de detalle de notificación
    path('<uuid:pk>/', views.notification_detail, name='notification_detail'),
]