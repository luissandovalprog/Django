"""
Vistas de autenticación
"""

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from auditoria.models import LogAuditoria


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
