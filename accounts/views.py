"""
Vistas de autenticación
"""

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from auditoria.models import LogAuditoria
from django.contrib.auth.decorators import user_passes_test
from .models import Usuario
from .forms import CustomUsuarioCreationForm, CustomUsuarioChangeForm

def login_view(request):
    """
    Vista de login
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Registrar login en auditoría
            LogAuditoria.registrar(
                usuario=user,
                accion='LOGIN',
                detalles='Inicio de sesión exitoso',
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Bienvenido, {user.nombre_completo}')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    Vista de logout
    """
    user = request.user
    
    # Registrar logout en auditoría
    LogAuditoria.registrar(
        usuario=user,
        accion='LOGOUT',
        detalles='Cierre de sesión',
        ip=get_client_ip(request)
    )
    
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente')
    return redirect('accounts:login')


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def es_admin_sistema(user):
    return user.is_authenticated and user.puede_gestionar_usuarios

@user_passes_test(es_admin_sistema)
def gestion_usuarios(request):
    usuarios = Usuario.objects.all().order_by('nombre_completo')
    context = {'usuarios': usuarios}
    return render(request, 'accounts/gestion_usuarios.html', context)

@user_passes_test(es_admin_sistema)
def crear_usuario(request):
    if request.method == 'POST':
        form = CustomUsuarioCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            LogAuditoria.registrar(request.user, 'CREAR_USUARIO', 'Usuario', user.id, f"Creado usuario {user.username}")
            messages.success(request, f'Usuario {user.username} creado.')
            return redirect('accounts:gestion_usuarios')
    else:
        form = CustomUsuarioCreationForm()

    context = {'form': form, 'title': 'Crear Nuevo Usuario'}
    return render(request, 'accounts/usuario_form.html', context)

@user_passes_test(es_admin_sistema)
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = CustomUsuarioChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            user = form.save()
            LogAuditoria.registrar(request.user, 'MODIFICAR_USUARIO', 'Usuario', user.id, f"Editado usuario {user.username}")
            messages.success(request, f'Usuario {user.username} actualizado.')
            return redirect('accounts:gestion_usuarios')
    else:
        form = CustomUsuarioChangeForm(instance=usuario)

    context = {'form': form, 'title': 'Editar Usuario'}
    return render(request, 'accounts/usuario_form.html', context)