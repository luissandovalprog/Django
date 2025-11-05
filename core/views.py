"""
Vistas principales del sistema
CRUD de Madre, Parto y Recién Nacido
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from datetime import datetime, timedelta
from .models import Madre, Parto, RecienNacido
from .forms import MadreForm, PartoForm, RecienNacidoForm
from auditoria.models import LogAuditoria


@login_required
def dashboard(request):
    """
    Dashboard principal con estadísticas
    """
    # Estadísticas generales
    total_madres = Madre.objects.count()
    total_partos = Parto.objects.count()
    total_recien_nacidos = RecienNacido.objects.count()
    
    # Partos del mes actual
    mes_actual = datetime.now().replace(day=1)
    partos_mes = Parto.objects.filter(fecha_parto__gte=mes_actual).count()
    
    # Últimos partos (limitado según permiso del usuario)
    if request.user.puede_ver_todos_partos:
        ultimos_partos = Parto.objects.all()[:10]
    else:
        ultimos_partos = Parto.objects.filter(usuario_registro=request.user)[:10]
    
    context = {
        'total_madres': total_madres,
        'total_partos': total_partos,
        'total_recien_nacidos': total_recien_nacidos,
        'partos_mes': partos_mes,
        'ultimos_partos': ultimos_partos,
    }
    
    return render(request, 'core/dashboard.html', context)


# ============= VISTAS DE MADRE =============

@login_required
def madre_list(request):
    """
    Listado de madres
    """
    madres = Madre.objects.all().order_by('-fecha_registro')
    
    # Agregar nombres descifrados para el template
    for madre in madres:
        madre.nombre_descifrado = madre.get_nombre()
        madre.rut_descifrado = madre.get_rut()
    
    context = {'madres': madres}
    return render(request, 'core/madre_list.html', context)


@login_required
def madre_create(request):
    """
    Crear nueva madre
    """
    if request.method == 'POST':
        form = MadreForm(request.POST)
        if form.is_valid():
            madre = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREATE_MADRE',
                tabla_afectada='Madre',
                registro_id=madre.id,
                detalles=f'Creada madre con ficha {madre.ficha_clinica_id}'
            )
            
            messages.success(request, 'Madre registrada exitosamente')
            return redirect('core:madre_list')
    else:
        form = MadreForm()
    
    context = {'form': form, 'title': 'Registrar Nueva Madre'}
    return render(request, 'core/madre_form.html', context)


@login_required
def madre_update(request, pk):
    """
    Actualizar madre existente
    """
    madre = get_object_or_404(Madre, pk=pk)
    
    if request.method == 'POST':
        form = MadreForm(request.POST, instance=madre)
        if form.is_valid():
            madre = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='UPDATE_MADRE',
                tabla_afectada='Madre',
                registro_id=madre.id,
                detalles=f'Actualizada madre con ficha {madre.ficha_clinica_id}'
            )
            
            messages.success(request, 'Madre actualizada exitosamente')
            return redirect('core:madre_list')
    else:
        form = MadreForm(instance=madre)
    
    context = {'form': form, 'title': 'Editar Madre', 'madre': madre}
    return render(request, 'core/madre_form.html', context)


@login_required
def madre_detail(request, pk):
    """
    Detalle de madre
    """
    madre = get_object_or_404(Madre, pk=pk)
    madre.nombre_descifrado = madre.get_nombre()
    madre.rut_descifrado = madre.get_rut()
    madre.telefono_descifrado = madre.get_telefono()
    
    # Obtener partos asociados
    partos = madre.partos.all()
    
    context = {'madre': madre, 'partos': partos}
    return render(request, 'core/madre_detail.html', context)


# ============= VISTAS DE PARTO =============

@login_required
def parto_list(request):
    """
    Listado de partos
    """
    if request.user.puede_ver_todos_partos:
        partos = Parto.objects.all()
    else:
        partos = Parto.objects.filter(usuario_registro=request.user)
    
    partos = partos.select_related('madre', 'usuario_registro').order_by('-fecha_parto')
    
    # Agregar nombres descifrados
    for parto in partos:
        parto.madre.nombre_descifrado = parto.madre.get_nombre()
    
    context = {'partos': partos}
    return render(request, 'core/parto_list.html', context)


@login_required
def parto_create(request):
    """
    Crear nuevo parto
    """
    if not request.user.puede_crear_partos:
        messages.error(request, 'No tienes permiso para crear registros de parto')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = PartoForm(request.POST, user=request.user)
        if form.is_valid():
            parto = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREATE_PARTO',
                tabla_afectada='Parto',
                registro_id=parto.id,
                detalles=f'Creado parto {parto.tipo_parto} - {parto.fecha_parto}'
            )
            
            messages.success(request, 'Parto registrado exitosamente')
            return redirect('core:parto_list')
    else:
        form = PartoForm(user=request.user)
    
    context = {'form': form, 'title': 'Registrar Nuevo Parto'}
    return render(request, 'core/parto_form.html', context)


@login_required
def parto_update(request, pk):
    """
    Actualizar parto existente
    """
    parto = get_object_or_404(Parto, pk=pk)
    
    # Verificar permisos
    if not request.user.puede_editar_partos:
        messages.error(request, 'No tienes permiso para editar registros de parto')
        return redirect('core:parto_list')
    
    # Si no es supervisor, solo puede editar sus propios registros
    if not request.user.puede_ver_todos_partos and parto.usuario_registro != request.user:
        messages.error(request, 'Solo puedes editar tus propios registros')
        return redirect('core:parto_list')
    
    if request.method == 'POST':
        form = PartoForm(request.POST, instance=parto, user=request.user)
        if form.is_valid():
            parto = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='UPDATE_PARTO',
                tabla_afectada='Parto',
                registro_id=parto.id,
                detalles=f'Actualizado parto {parto.tipo_parto}'
            )
            
            messages.success(request, 'Parto actualizado exitosamente')
            return redirect('core:parto_list')
    else:
        form = PartoForm(instance=parto, user=request.user)
    
    context = {'form': form, 'title': 'Editar Parto', 'parto': parto}
    return render(request, 'core/parto_form.html', context)


@login_required
def parto_detail(request, pk):
    """
    Detalle de parto con recién nacidos
    """
    parto = get_object_or_404(Parto, pk=pk)
    
    # Verificar permisos
    if not request.user.puede_ver_todos_partos and parto.usuario_registro != request.user:
        messages.error(request, 'No tienes permiso para ver este registro')
        return redirect('core:parto_list')
    
    parto.madre.nombre_descifrado = parto.madre.get_nombre()
    recien_nacidos = parto.recien_nacidos.all()
    
    context = {'parto': parto, 'recien_nacidos': recien_nacidos}
    return render(request, 'core/parto_detail.html', context)


# ============= VISTAS DE RECIÉN NACIDO =============

@login_required
def recien_nacido_create(request, parto_pk):
    """
    Crear nuevo recién nacido asociado a un parto
    """
    parto = get_object_or_404(Parto, pk=parto_pk)
    
    if not request.user.puede_crear_partos:
        messages.error(request, 'No tienes permiso para registrar recién nacidos')
        return redirect('core:parto_detail', pk=parto_pk)
    
    if request.method == 'POST':
        form = RecienNacidoForm(request.POST, user=request.user)
        if form.is_valid():
            recien_nacido = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREATE_RECIEN_NACIDO',
                tabla_afectada='RecienNacido',
                registro_id=recien_nacido.id,
                detalles=f'Registrado RN del parto {parto.id}'
            )
            
            messages.success(request, 'Recién nacido registrado exitosamente')
            return redirect('core:parto_detail', pk=parto_pk)
    else:
        form = RecienNacidoForm(user=request.user, initial={'parto': parto})
        # Hacer que el campo parto esté deshabilitado
        form.fields['parto'].widget.attrs['readonly'] = True
    
    context = {'form': form, 'title': 'Registrar Recién Nacido', 'parto': parto}
    return render(request, 'core/recien_nacido_form.html', context)


@login_required
def recien_nacido_update(request, pk):
    """
    Actualizar recién nacido
    """
    recien_nacido = get_object_or_404(RecienNacido, pk=pk)
    
    if not request.user.puede_editar_partos:
        messages.error(request, 'No tienes permiso para editar recién nacidos')
        return redirect('core:parto_detail', pk=recien_nacido.parto.pk)
    
    if request.method == 'POST':
        form = RecienNacidoForm(request.POST, instance=recien_nacido, user=request.user)
        if form.is_valid():
            recien_nacido = form.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='UPDATE_RECIEN_NACIDO',
                tabla_afectada='RecienNacido',
                registro_id=recien_nacido.id,
                detalles=f'Actualizado RN {recien_nacido.id}'
            )
            
            messages.success(request, 'Recién nacido actualizado exitosamente')
            return redirect('core:parto_detail', pk=recien_nacido.parto.pk)
    else:
        form = RecienNacidoForm(instance=recien_nacido, user=request.user)
        form.fields['parto'].widget.attrs['readonly'] = True
    
    context = {'form': form, 'title': 'Editar Recién Nacido', 'recien_nacido': recien_nacido}
    return render(request, 'core/recien_nacido_form.html', context)
