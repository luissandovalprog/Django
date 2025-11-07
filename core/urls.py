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
    
    # Recién Nacido URLs
    path('parto/<uuid:parto_pk>/recien-nacido/crear/', views.recien_nacido_create, name='recien_nacido_create'),
    path('recien-nacido/<uuid:pk>/editar/', views.recien_nacido_update, name='recien_nacido_update'),

    # Corrección URLs
    path('parto/<uuid:pk>/corregir/', views.anexar_correccion, name='anexar_correccion'),

    # Epicrisis URLs
    path('parto/<uuid:pk>/epicrisis/', views.crear_epicrisis, name='crear_epicrisis'),
]
