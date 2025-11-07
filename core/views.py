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
from .forms import CorreccionForm
from .models import Correccion
from .forms import EpicrisisForm, IndicacionFormSet
from utils.crypto import crypto_service
from django.utils import timezone

@login_required
def dashboard(request):
    """
    Dashboard principal con estadísticas y filtrado (migrado de React)
    """
    busqueda_query = request.GET.get('busqueda', '')

    # Lógica de filtrado base (React: perteneceATurno)
    madres_qs = Madre.objects.all()
    partos_qs = Parto.objects.select_related('madre', 'usuario_registro')

    # Lógica de permisos de React
    if not request.user.puede_ver_todos_partos:
        # Filtra partos y madres por el usuario (Matrona/Enfermera por turno)
        # NOTA: El modelo Django actual filtra por 'usuario_registro'. 
        # El modelo React filtra por 'turno'. 
        # Asumiremos 'usuario_registro' como la lógica de negocio final.
        partos_qs = partos_qs.filter(usuario_registro=request.user)
        madres_qs = madres_qs.filter(partos__usuario_registro=request.user).distinct()

    # Lógica de búsqueda (React: busqueda)
    if busqueda_query:
        partos_qs = partos_qs.filter(
            Q(madre__rut_hash=crypto_service.hash_data(busqueda_query)) | # Asumiendo búsqueda por RUT hasheado
            Q(madre__nombre_hash=crypto_service.hash_data(busqueda_query)) | # Asumiendo búsqueda por Nombre hasheado
            Q(recien_nacidos__rut_provisorio__icontains=busqueda_query)
        ).distinct()

        madres_qs = madres_qs.filter(
            Q(rut_hash=crypto_service.hash_data(busqueda_query)) |
            Q(nombre_hash=crypto_service.hash_data(busqueda_query)) |
            Q(ficha_clinica_id__icontains=busqueda_query)
        ).distinct()

    # Lógica de estadísticas (React: useMemo)
    total_madres = madres_qs.count()
    total_partos = partos_qs.count()

    mes_actual = datetime.now().replace(day=1)
    partos_mes = partos_qs.filter(fecha_parto__gte=mes_actual).count()

    # Lógica de "Partos Hoy" (React: partosHoy)
    hoy_inicio = datetime.now().replace(hour=0, minute=0, second=0)
    hoy_fin = hoy_inicio + timedelta(days=1)
    partos_hoy = partos_qs.filter(fecha_parto__gte=hoy_inicio, fecha_parto__lt=hoy_fin).count()

    # Lógica de "Recién Nacidos"
    total_recien_nacidos = RecienNacido.objects.filter(parto__in=partos_qs).count()

    # Lógica de "Últimos partos" (React: partosRecientes)
    ultimos_partos = partos_qs.order_by('-fecha_parto')[:10]
    for p in ultimos_partos:
        p.madre.nombre_descifrado = p.madre.get_nombre()

    # Lógica de "Madres sin parto" (React)
    madres_sin_parto = madres_qs.filter(partos__isnull=True)
    for m in madres_sin_parto:
        m.nombre_descifrado = m.get_nombre()

    context = {
        'total_madres': total_madres,
        'total_partos': total_partos,
        'total_recien_nacidos': total_recien_nacidos,
        'partos_mes': partos_mes,
        'partos_hoy': partos_hoy,
        'ultimos_partos': ultimos_partos,
        'madres_sin_parto': madres_sin_parto,
        'busqueda_query': busqueda_query,
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

@login_required
def anexar_correccion(request, pk):
    parto = get_object_or_404(Parto, pk=pk)

    # Lógica de Permisos (de React: tienePermiso('anexarCorreccion'))
    # Asumimos que "Médico" es el rol. Ajustar según tu modelo `Rol`.
    if not request.user.rol.nombre == 'Médico':
        messages.error(request, 'No tiene permisos para anexar correcciones.')
        return redirect('core:parto_detail', pk=parto.pk)

    if request.method == 'POST':
        form = CorreccionForm(request.POST)
        if form.is_valid():
            correccion = form.save(commit=False)
            correccion.usuario = request.user
            correccion.parto = parto
            correccion.save()

            LogAuditoria.registrar(
                usuario=request.user,
                accion='ANEXAR_CORRECCION',
                tabla_afectada='Correccion',
                registro_id=correccion.id,
                detalles=f'Corrección en Parto {parto.id}: {correccion.campo_corregido} | Justificación: {correccion.justificacion}'
            )
            messages.success(request, 'Corrección anexada exitosamente.')
            return redirect('core:parto_detail', pk=parto.pk)
    else:
        form = CorreccionForm()

    context = {
        'form': form,
        'parto': parto,
        'madre': parto.madre,
        'title': 'Anexar Corrección de Registro'
    }
    return render(request, 'core/anexar_correccion_form.html', context)

@login_required
def crear_epicrisis(request, pk):
    parto = get_object_or_404(Parto, pk=pk)

    # Permiso (de React: tienePermiso('crearEpicrisis'))
    if not request.user.rol.nombre == 'Médico':
        messages.error(request, 'Solo los médicos pueden crear epicrisis.')
        return redirect('core:parto_detail', pk=parto.pk)

    if request.method == 'POST':
        form = EpicrisisForm(request.POST)
        formset = IndicacionFormSet(request.POST, instance=parto, prefix='indicaciones')

        if form.is_valid() and formset.is_valid():
            # Guardar datos de epicrisis en el JSONField
            parto.epicrisis_data = {
                'motivo_ingreso': form.cleaned_data.get('motivo_ingreso'),
                'resumen_evolucion': form.cleaned_data.get('resumen_evolucion'),
                'diagnostico_egreso': form.cleaned_data.get('diagnostico_egreso'),
                'condicion_egreso': form.cleaned_data.get('condicion_egreso'),
                'control_posterior': form.cleaned_data.get('control_posterior'),
                'indicaciones_alta': form.cleaned_data.get('indicaciones_alta'),
                'observaciones': form.cleaned_data.get('observaciones'),
                'medico_id': request.user.pk,
                'medico_nombre': request.user.nombre_completo,
                'fecha_creacion': timezone.now().isoformat()
            }
            parto.save()

            # Guardar el formset de indicaciones
            formset.save()

            LogAuditoria.registrar(request.user, 'CREAR_EPICRISIS', 'Parto', parto.id, f"Epicrisis creada para {parto.madre.get_nombre()}")
            messages.success(request, 'Epicrisis guardada exitosamente.')
            return redirect('core:parto_detail', pk=parto.pk)
    else:
        form = EpicrisisForm(initial=parto.epicrisis_data or {})
        formset = IndicacionFormSet(instance=parto, prefix='indicaciones')

    context = {
        'form': form,
        'formset': formset,
        'parto': parto,
        'madre': parto.madre,
        'title': 'Epicrisis e Indicaciones Médicas'
    }
    return render(request, 'core/epicrisis_form.html', context)