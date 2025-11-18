# accounts/urls.py
"""
URLs de la aplicación accounts
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('gestion/', views.gestion_usuarios, name='gestion_usuarios'),
    path('gestion/crear/', views.crear_usuario, name='crear_usuario'),
    path('gestion/<uuid:pk>/editar/', views.editar_usuario, name='editar_usuario'),
    path('gestion/<uuid:pk>/desactivar/', views.desactivar_usuario, name='desactivar_usuario'),

    # Gestión de Roles
    path('roles/', views.rol_list, name='rol_list'),
    path('roles/crear/', views.rol_create, name='rol_create'),
    path('roles/<uuid:pk>/editar/', views.rol_update, name='rol_update'),
]