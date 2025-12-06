# accounts/urls.py
"""
URLs de la aplicación accounts
"""

from django.urls import path
from . import views
from . import views_2fa


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

    # ===== RUTAS 2FA =====
    path('2fa/menu/', views_2fa.menu_2fa, name='menu_2fa'),
    path('2fa/configurar/', views_2fa.configurar_2fa, name='configurar_2fa'),
    path('2fa/verificar/', views_2fa.verificar_2fa, name='verificar_2fa'),
    path('2fa/desactivar/', views_2fa.desactivar_2fa, name='desactivar_2fa'),
    path('2fa/codigos/', views_2fa.ver_codigos_recuperacion, name='ver_codigos_recuperacion'),
    path('2fa/codigos/', views_2fa.ver_codigos_recuperacion, name='codigos_recuperacion'),  # Alias
    path('2fa/regenerar/', views_2fa.regenerar_codigos_recuperacion, name='regenerar_codigos_recuperacion'),
]