"""
URLs de la aplicación reportes
"""

from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.reporte_menu, name='menu'),
    path('rem-bs22/', views.generar_rem_bs22, name='rem_bs22'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
]
