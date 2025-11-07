"""
Vistas de autenticación
"""

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from auditoria.models import LogAuditoria
from .models import Usuario
from .forms import CustomUsuarioCreationForm, CustomUsuarioChangeForm


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def login_view(request):
    """
    Vista de login
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                if user.activo:
                    login(request, user)
                    
                    # Registrar login en auditoría
                    LogAuditoria.registrar(
                        usuario=user,
                        accion='LOGIN',
                        detalles=f'Inicio de sesión exitoso - Rol: {user.rol.nombre if user.rol else "Sin rol"}',
                        ip=get_client_ip(request)
                    )
                    
                    messages.success(request, f'Bienvenido, {user.nombre_completo}')
                    
                    # Redirigir según el parámetro 'next' o al dashboard
                    next_url = request.GET.get('next', 'core:dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Su cuenta está desactivada. Contacte al administrador.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
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


def es_admin_sistema(user):
    """Verifica si el usuario es administrador del sistema"""
    return user.is_authenticated and (user.is_superuser or user.puede_gestionar_usuarios)


@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def gestion_usuarios(request):
    """
    Vista de gestión de usuarios (solo para administradores)
    """
    usuarios = Usuario.objects.select_related('rol').all().order_by('nombre_completo')
    context = {'usuarios': usuarios}
    return render(request, 'accounts/gestion_usuarios.html', context)


@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def crear_usuario(request):
    """
    Vista para crear nuevo usuario
    """
    if request.method == 'POST':
        form = CustomUsuarioCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREAR_USUARIO',
                tabla_afectada='Usuario',
                registro_id=user.id,
                detalles=f"Usuario creado: {user.username} - Rol: {user.rol.nombre if user.rol else 'Sin rol'}",
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Usuario {user.username} creado exitosamente.')
            return redirect('accounts:gestion_usuarios')
    else:
        form = CustomUsuarioCreationForm()

    context = {'form': form, 'title': 'Crear Nuevo Usuario'}
    return render(request, 'accounts/usuario_form.html', context)


@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def editar_usuario(request, pk):
    """
    Vista para editar usuario existente
    """
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        form = CustomUsuarioChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            user = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='MODIFICAR_USUARIO',
                tabla_afectada='Usuario',
                registro_id=user.id,
                detalles=f"Usuario modificado: {user.username} - Rol: {user.rol.nombre if user.rol else 'Sin rol'}",
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Usuario {user.username} actualizado exitosamente.')
            return redirect('accounts:gestion_usuarios')
    else:
        form = CustomUsuarioChangeForm(instance=usuario)

    context = {'form': form, 'title': 'Editar Usuario', 'usuario': usuario}
    return render(request, 'accounts/usuario_form.html', context)