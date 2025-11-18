# accounts/views.py
"""
Vistas de autenticación y gestión de usuarios
"""

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from auditoria.models import LogAuditoria
from .models import Usuario, Rol
from .forms import CustomUsuarioCreationForm, CustomUsuarioChangeForm, RolForm

def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def login_view(request):
    """Vista de login con redirección por rol"""
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
                    
                    # Registrar login
                    LogAuditoria.registrar(
                        usuario=user,
                        accion='LOGIN',
                        detalles=f'Inicio de sesión exitoso - Rol: {user.rol.nombre if user.rol else "Sin rol"}',
                        ip=get_client_ip(request)
                    )
                    
                    messages.success(request, f'Bienvenido, {user.nombre_completo}')
                    
                    # ===== REDIRECCIÓN POR ROL =====
                    if user.rol and user.rol.nombre == 'Admin Sistema':
                        return redirect('auditoria:historial_auditoria')
                    elif user.rol and user.rol.nombre == 'Administrativo':
                        return redirect('core:dashboard')  # Dashboard con tabla administrativa
                    else:
                        # Matrona, Médico, Enfermera, Supervisor
                        return redirect('core:dashboard')
                else:
                    messages.error(request, 'Su cuenta está desactivada.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Vista de logout"""
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

@login_required
@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def rol_list(request):
    """Listado de roles - SOLO Admin Sistema y Supervisor"""
    roles = Rol.objects.all().order_by('nombre')
    
    # Contar usuarios por rol
    for rol in roles:
        rol.total_usuarios = Usuario.objects.filter(rol=rol).count()
    
    context = {
        'roles': roles,
        'total_roles': roles.count(),
    }
    return render(request, 'accounts/rol_list.html', context)


@login_required
@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def rol_create(request):
    """Crear nuevo rol"""
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            rol = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREAR_ROL',
                tabla_afectada='Rol',
                registro_id=rol.id,
                detalles=f"Rol creado: {rol.nombre} - {rol.descripcion}",
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Rol "{rol.nombre}" creado exitosamente.')
            return redirect('accounts:rol_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f'{form.fields.get(field, {}).label or field}: {error}')
    else:
        form = RolForm()
    
    context = {
        'form': form,
        'title': 'Nuevo Rol',
        'is_new': True
    }
    return render(request, 'accounts/rol_form.html', context)


@login_required
@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def rol_update(request, pk):
    """Editar rol existente"""
    rol = get_object_or_404(Rol, pk=pk)
    
    # Advertencia si el rol tiene usuarios asignados
    usuarios_asignados = Usuario.objects.filter(rol=rol).count()
    
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            rol = form.save()
            
            # Registrar en auditoría
            cambios = ', '.join(form.changed_data) if form.changed_data else 'sin cambios'
            LogAuditoria.registrar(
                usuario=request.user,
                accion='MODIFICAR_ROL',
                tabla_afectada='Rol',
                registro_id=rol.id,
                detalles=f"Rol modificado: {rol.nombre} - Campos: {cambios} - Usuarios afectados: {usuarios_asignados}",
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Rol "{rol.nombre}" actualizado exitosamente.')
            if usuarios_asignados > 0:
                messages.warning(
                    request, 
                    f'Los cambios afectarán a {usuarios_asignados} usuario(s) con este rol.'
                )
            return redirect('accounts:rol_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f'{form.fields.get(field, {}).label or field}: {error}')
    else:
        form = RolForm(instance=rol)
    
    context = {
        'form': form,
        'title': 'Editar Rol',
        'rol': rol,
        'is_new': False,
        'usuarios_asignados': usuarios_asignados
    }
    return render(request, 'accounts/rol_form.html', context)

@login_required
def gestion_usuarios(request):
    """Gestión de usuarios - SOLO Admin Sistema y Supervisor"""
    if not request.user.puede_gestionar_usuarios:
        messages.error(request, 'No tiene permisos para gestionar usuarios.')
        return redirect('core:dashboard')
    """
    Vista de gestión de usuarios (solo para administradores)
    Versión mejorada con estadísticas
    """
    usuarios = Usuario.objects.select_related('rol').all().order_by('nombre_completo')
    
    # Calcular estadísticas
    usuarios_activos = usuarios.filter(activo=True).count()
    usuarios_inactivos = usuarios.filter(activo=False).count()
    total_roles = usuarios.values('rol').distinct().count()
    
    context = {
        'usuarios': usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_inactivos': usuarios_inactivos,
        'total_roles': total_roles,
    }
    return render(request, 'accounts/gestion_usuarios.html', context)


@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def crear_usuario(request):
    """Vista para crear nuevo usuario"""
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
                detalles=f"Usuario creado: {user.username} - Nombre: {user.nombre_completo} - Rol: {user.rol.nombre if user.rol else 'Sin rol'}",
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Usuario {user.username} creado exitosamente.')
            return redirect('accounts:gestion_usuarios')
        else:
            # Mostrar errores específicos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = CustomUsuarioCreationForm()

    context = {
        'form': form,
        'title': 'Nuevo Usuario',
        'is_new': True
    }
    return render(request, 'accounts/usuario_form.html', context)


@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def editar_usuario(request, pk):
    """Vista para editar usuario existente"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    # No permitir editar superusuarios excepto por otro superusuario
    if usuario.is_superuser and not request.user.is_superuser:
        messages.error(request, 'No tiene permisos para editar este usuario')
        return redirect('accounts:gestion_usuarios')
    
    if request.method == 'POST':
        form = CustomUsuarioChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            user = form.save()
            
            # Registrar en auditoría
            cambios = []
            if 'nueva_password' in form.cleaned_data and form.cleaned_data['nueva_password']:
                cambios.append('contraseña actualizada')
            if form.has_changed():
                cambios.append(f"campos modificados: {', '.join(form.changed_data)}")
            
            LogAuditoria.registrar(
                usuario=request.user,
                accion='MODIFICAR_USUARIO',
                tabla_afectada='Usuario',
                registro_id=user.id,
                detalles=f"Usuario modificado: {user.username} - {' - '.join(cambios) if cambios else 'sin cambios'}",
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Usuario {user.username} actualizado exitosamente.')
            return redirect('accounts:gestion_usuarios')
        else:
            # Mostrar errores específicos
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f'{form.fields.get(field, {}).label or field}: {error}')
    else:
        form = CustomUsuarioChangeForm(instance=usuario)

    context = {
        'form': form,
        'title': 'Editar Usuario',
        'usuario': usuario,
        'is_new': False
    }
    return render(request, 'accounts/usuario_form.html', context)


@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def desactivar_usuario(request, pk):
    """Desactiva un usuario (no lo elimina, solo marca como inactivo)"""
    if request.method != 'POST':
        return redirect('accounts:gestion_usuarios')
    
    usuario = get_object_or_404(Usuario, pk=pk)
    
    # No permitir desactivar superusuarios
    if usuario.is_superuser:
        messages.error(request, 'No se puede desactivar un superusuario')
        return redirect('accounts:gestion_usuarios')
    
    # No permitir auto-desactivación
    if usuario == request.user:
        messages.error(request, 'No puede desactivar su propia cuenta')
        return redirect('accounts:gestion_usuarios')
    
    # Desactivar usuario
    usuario.activo = False
    usuario.save()
    
    # Registrar en auditoría
    LogAuditoria.registrar(
        usuario=request.user,
        accion='DESACTIVAR_USUARIO',
        tabla_afectada='Usuario',
        registro_id=usuario.id,
        detalles=f"Usuario desactivado: {usuario.username} ({usuario.nombre_completo})",
        ip=get_client_ip(request)
    )
    
    messages.success(request, f'Usuario {usuario.username} desactivado exitosamente')
    return redirect('accounts:gestion_usuarios')