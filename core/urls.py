# core/urls.py
"""
URLs de la aplicación core
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Madre URLs
    path('madre/', views.madre_list, name='madre_list'),
    path('madre/crear/', views.madre_create, name='madre_create'),
    path('madre/<uuid:pk>/', views.madre_detail, name='madre_detail'),
    path('madre/<uuid:pk>/editar/', views.madre_update, name='madre_update'),
    
    # Parto URLs
    path('parto/', views.parto_list, name='parto_list'),
    path('parto/crear/', views.parto_create, name='parto_create'),
    path('parto/<uuid:pk>/', views.parto_detail, name='parto_detail'),
    path('parto/<uuid:pk>/editar/', views.parto_update, name='parto_update'),
    
    # Nueva ruta: Registrar parto para una madre específica
    path('madre/<uuid:madre_pk>/registrar-parto/', views.registrar_parto_para_madre, name='registrar_parto_para_madre'),
    
    # Nueva ruta: Registrar parto completo (parto + RN) para una madre específica
    path('madre/<uuid:madre_pk>/registrar-parto-completo/', views.registrar_parto_completo, name='registrar_parto_completo'),
    
    # Recién Nacido URLs
    path('parto/<uuid:parto_pk>/recien-nacido/crear/', views.recien_nacido_create, name='recien_nacido_create'),
    path('recien-nacido/<uuid:pk>/editar/', views.recien_nacido_update, name='recien_nacido_update'),

    # Corrección URLs
    path('parto/<uuid:pk>/corregir/', views.anexar_correccion, name='anexar_correccion'),

    # Epicrisis URLs - NUEVAS RUTAS
    path('epicrisis/', views.epicrisis_list, name='epicrisis_list'),
    path('parto/<uuid:pk>/epicrisis/crear/', views.crear_epicrisis, name='crear_epicrisis'),
    path('parto/<uuid:pk>/epicrisis/ver/', views.ver_epicrisis, name='ver_epicrisis'),
    
    # Partograma URLs
    path('partogramas/', views.partograma_list, name='partograma_list'),
    path('parto/<uuid:parto_pk>/partograma/crear/', views.partograma_create, name='partograma_create'),
    path('parto/<uuid:parto_pk>/partograma/editar/', views.partograma_update, name='partograma_update'),
]