"""
Vistas principales del sistema
CRUD de Madre, Parto y Recién Nacido
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Madre, Parto, RecienNacido, Correccion, Indicacion
from .forms import MadreForm, PartoForm, RecienNacidoForm, CorreccionForm, EpicrisisForm, IndicacionFormSet, PartogramaForm
from auditoria.models import LogAuditoria
from utils.crypto import crypto_service


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def dashboard(request):
    """
    Dashboard principal con estadísticas y filtrado
    """
    from datetime import date
    
    busqueda_query = request.GET.get('busqueda', '')

    # Lógica de filtrado base
    madres_qs = Madre.objects.all()
    partos_qs = Parto.objects.select_related('madre', 'usuario_registro').prefetch_related('recien_nacidos')

    # Lógica de permisos
    if not request.user.puede_ver_todos_partos:
        partos_qs = partos_qs.filter(usuario_registro=request.user)
        madres_qs = madres_qs.filter(partos__usuario_registro=request.user).distinct()

    # Lógica de búsqueda
    if busqueda_query:
        partos_qs = partos_qs.filter(
            Q(madre__rut_hash=crypto_service.hash_data(busqueda_query)) |
            Q(madre__nombre_hash=crypto_service.hash_data(busqueda_query)) |
            Q(madre__ficha_clinica_numero__icontains=busqueda_query) |
            Q(recien_nacidos__rut_provisorio__icontains=busqueda_query)
        ).distinct()

        madres_qs = madres_qs.filter(
            Q(rut_hash=crypto_service.hash_data(busqueda_query)) |
            Q(nombre_hash=crypto_service.hash_data(busqueda_query)) |
            Q(ficha_clinica_numero__icontains=busqueda_query)
        ).distinct()

    # Estadísticas
    total_madres = madres_qs.count()
    total_partos = partos_qs.count()

    mes_actual = datetime.now().replace(day=1)
    partos_mes = partos_qs.filter(fecha_parto__gte=mes_actual).count()

    # Partos hoy
    hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    hoy_fin = hoy_inicio + timedelta(days=1)
    partos_hoy = partos_qs.filter(fecha_parto__gte=hoy_inicio, fecha_parto__lt=hoy_fin).count()

    # Recién nacidos
    total_recien_nacidos = RecienNacido.objects.filter(parto__in=partos_qs).count()

    # Últimos partos con cálculo de días
    ultimos_partos = partos_qs.order_by('-fecha_parto')[:10]
    now = timezone.now()
    
    for p in ultimos_partos:
        p.madre.nombre_descifrado = p.madre.get_nombre()
        p.madre.rut_descifrado = p.madre.get_rut()
        
        # Calcular días de hospitalización
        diferencia = now - p.fecha_parto
        p.dias_hospitalizacion = diferencia.days
        
        # Determinar color del badge
        if p.dias_hospitalizacion <= 3:
            p.badge_color = 'badge-green'
        elif p.dias_hospitalizacion <= 7:
            p.badge_color = 'badge-yellow'
        else:
            p.badge_color = 'badge-red'

    # Madres sin parto - CORREGIDO: Calcular edad aquí
    madres_sin_parto = madres_qs.filter(partos__isnull=True)
    hoy = date.today()
    
    for m in madres_sin_parto:
        m.nombre_descifrado = m.get_nombre()
        # CALCULAR EDAD
        if m.fecha_nacimiento:
            edad = hoy.year - m.fecha_nacimiento.year
            # Ajustar si aún no ha cumplido años este año
            if (hoy.month, hoy.day) < (m.fecha_nacimiento.month, m.fecha_nacimiento.day):
                edad -= 1
            m.edad_calculada = edad
        else:
            m.edad_calculada = None

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
    """Listado de madres"""
    madres = Madre.objects.all().order_by('-fecha_registro')
    
    # Agregar nombres descifrados para el template
    for madre in madres:
        madre.nombre_descifrado = madre.get_nombre()
        madre.rut_descifrado = madre.get_rut()
    
    context = {'madres': madres}
    return render(request, 'core/madre_list.html', context)


@login_required
def madre_create(request):
    """Crear nueva madre"""
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
                detalles=f'Madre registrada - Ficha: {madre.ficha_clinica_id}, Nombre: {madre.get_nombre()}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Madre registrada exitosamente')
            return redirect('core:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = MadreForm()
    
    context = {'form': form, 'title': 'Admisión de Madre'}
    return render(request, 'core/madre_form.html', context)


@login_required
def madre_update(request, pk):
    """Actualizar madre existente"""
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
                detalles=f'Madre actualizada - Ficha: {madre.ficha_clinica_id}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Madre actualizada exitosamente')
            return redirect('core:madre_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = MadreForm(instance=madre)
    
    context = {'form': form, 'title': 'Editar Madre', 'madre': madre}
    return render(request, 'core/madre_form.html', context)


@login_required
def madre_detail(request, pk):
    """Detalle de madre"""
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
    """Listado de partos"""
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
    """Crear nuevo parto"""
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
                detalles=f'Parto registrado - Tipo: {parto.tipo_parto}, Fecha: {parto.fecha_parto}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Parto registrado exitosamente')
            return redirect('core:parto_detail', pk=parto.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PartoForm(user=request.user)
    
    context = {'form': form, 'title': 'Registrar Nuevo Parto'}
    return render(request, 'core/parto_form.html', context)


@login_required
def parto_update(request, pk):
    """Actualizar parto existente"""
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
                detalles=f'Parto actualizado - Tipo: {parto.tipo_parto}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Parto actualizado exitosamente')
            return redirect('core:parto_detail', pk=parto.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PartoForm(instance=parto, user=request.user)
    
    context = {'form': form, 'title': 'Editar Parto', 'parto': parto}
    return render(request, 'core/parto_form.html', context)


@login_required
def parto_detail(request, pk):
    """Detalle de parto con recién nacidos"""
    parto = get_object_or_404(Parto, pk=pk)
    
    # Verificar permisos
    if not request.user.puede_ver_todos_partos and parto.usuario_registro != request.user:
        messages.error(request, 'No tienes permiso para ver este registro')
        return redirect('core:parto_list')
    
    parto.madre.nombre_descifrado = parto.madre.get_nombre()
    parto.madre.rut_descifrado = parto.madre.get_rut()
    recien_nacidos = parto.recien_nacidos.all()
    correcciones = parto.correcciones.all().order_by('-fecha_correccion')
    
    context = {
        'parto': parto,
        'recien_nacidos': recien_nacidos,
        'correcciones': correcciones
    }
    return render(request, 'core/parto_detail.html', context)


# ============= VISTAS DE RECIÉN NACIDO =============

@login_required
def recien_nacido_create(request, parto_pk):
    """Crear nuevo recién nacido asociado a un parto"""
    parto = get_object_or_404(Parto, pk=parto_pk)
    
    if not request.user.puede_crear_partos:
        messages.error(request, 'No tienes permiso para registrar recién nacidos')
        return redirect('core:parto_detail', pk=parto_pk)
    
    # Verificar que el usuario pueda acceder a este parto
    if not request.user.puede_ver_todos_partos and parto.usuario_registro != request.user:
        messages.error(request, 'No tienes permiso para acceder a este parto')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = RecienNacidoForm(request.POST, user=request.user)
        if form.is_valid():
            recien_nacido = form.save(commit=False)
            recien_nacido.parto = parto
            recien_nacido.usuario_registro = request.user
            recien_nacido.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREATE_RECIEN_NACIDO',
                tabla_afectada='RecienNacido',
                registro_id=recien_nacido.id,
                detalles=f'RN registrado - Parto: {parto.id}, Peso: {recien_nacido.peso_gramos}g, APGAR: {recien_nacido.apgar_1_min}/{recien_nacido.apgar_5_min}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Recién nacido registrado exitosamente')
            return redirect('core:parto_detail', pk=parto_pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RecienNacidoForm(user=request.user, initial={'parto': parto})
        # Hacer que el campo parto esté deshabilitado
        form.fields['parto'].widget.attrs['disabled'] = True
    
    context = {'form': form, 'title': 'Registrar Recién Nacido', 'parto': parto}
    return render(request, 'core/recien_nacido_form.html', context)


@login_required
def recien_nacido_update(request, pk):
    """Actualizar recién nacido"""
    recien_nacido = get_object_or_404(RecienNacido, pk=pk)
    parto = recien_nacido.parto
    
    if not request.user.puede_editar_partos:
        messages.error(request, 'No tienes permiso para editar recién nacidos')
        return redirect('core:parto_detail', pk=parto.pk)
    
    # Verificar permisos sobre el parto
    if not request.user.puede_ver_todos_partos and parto.usuario_registro != request.user:
        messages.error(request, 'No tienes permiso para editar este registro')
        return redirect('core:dashboard')
    
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
                detalles=f'RN actualizado - ID: {recien_nacido.id}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Recién nacido actualizado exitosamente')
            return redirect('core:parto_detail', pk=parto.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RecienNacidoForm(instance=recien_nacido, user=request.user)
        form.fields['parto'].widget.attrs['disabled'] = True
    
    context = {'form': form, 'title': 'Editar Recién Nacido', 'recien_nacido': recien_nacido, 'parto': parto}
    return render(request, 'core/recien_nacido_form.html', context)


# ============= VISTAS DE CORRECCIÓN =============

@login_required
def anexar_correccion(request, pk):
    """Anexar corrección a un parto (solo médicos)"""
    parto = get_object_or_404(Parto, pk=pk)

    # Verificar permisos (solo médicos pueden anexar correcciones)
    if not request.user.puede_anexar_correccion:
        messages.error(request, 'No tiene permisos para anexar correcciones. Solo médicos pueden realizar esta acción.')
        return redirect('core:parto_detail', pk=parto.pk)

    if request.method == 'POST':
        form = CorreccionForm(request.POST)
        if form.is_valid():
            correccion = form.save(commit=False)
            correccion.usuario = request.user
            correccion.parto = parto
            correccion.save()

            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='ANEXAR_CORRECCION',
                tabla_afectada='Correccion',
                registro_id=correccion.id,
                detalles=f'Corrección anexada - Parto: {parto.id}, Campo: {correccion.campo_corregido}, Justificación: {correccion.justificacion[:100]}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Corrección anexada exitosamente. El registro original permanece intacto.')
            return redirect('core:parto_detail', pk=parto.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = CorreccionForm()

    context = {
        'form': form,
        'parto': parto,
        'madre': parto.madre,
        'title': 'Anexar Corrección de Registro'
    }
    return render(request, 'core/anexar_correccion_form.html', context)


# ============= VISTAS DE EPICRISIS =============

@login_required
def crear_epicrisis(request, pk):
    """Crear epicrisis e indicaciones (solo médicos)"""
    parto = get_object_or_404(Parto, pk=pk)

    # Verificar permisos (solo médicos pueden crear epicrisis)
    if not request.user.puede_anexar_correccion:  # Usamos el mismo permiso de médico
        messages.error(request, 'Solo los médicos pueden crear epicrisis.')
        return redirect('core:parto_detail', pk=parto.pk)

    if request.method == 'POST':
        form = EpicrisisForm(request.POST)
        formset = IndicacionFormSet(request.POST, instance=parto, prefix='indicaciones')

        if form.is_valid() and formset.is_valid():
            # Guardar datos de epicrisis en el JSONField
            parto.epicrisis_data = {
                'motivo_ingreso': form.cleaned_data.get('motivo_ingreso', ''),
                'resumen_evolucion': form.cleaned_data.get('resumen_evolucion', ''),
                'diagnostico_egreso': form.cleaned_data.get('diagnostico_egreso', ''),
                'condicion_egreso': form.cleaned_data.get('condicion_egreso', ''),
                'control_posterior': form.cleaned_data.get('control_posterior', ''),
                'indicaciones_alta': form.cleaned_data.get('indicaciones_alta', ''),
                'observaciones': form.cleaned_data.get('observaciones', ''),
                'medico_id': str(request.user.pk),
                'medico_nombre': request.user.nombre_completo,
                'fecha_creacion': timezone.now().isoformat()
            }
            parto.save()

            # Guardar el formset de indicaciones
            formset.save()

            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREAR_EPICRISIS',
                tabla_afectada='Parto',
                registro_id=parto.id,
                detalles=f"Epicrisis creada para parto {parto.id} - Madre: {parto.madre.get_nombre()}",
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Epicrisis e indicaciones guardadas exitosamente.')
            return redirect('core:parto_detail', pk=parto.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for form_errors in formset.errors:
                for field, errors in form_errors.items():
                    for error in errors:
                        messages.error(request, f'Indicación - {field}: {error}')
    else:
        # Cargar datos existentes si ya hay epicrisis
        initial_data = parto.epicrisis_data if parto.epicrisis_data else {}
        form = EpicrisisForm(initial=initial_data)
        formset = IndicacionFormSet(instance=parto, prefix='indicaciones')

    context = {
        'form': form,
        'formset': formset,
        'parto': parto,
        'madre': parto.madre,
        'title': 'Epicrisis e Indicaciones Médicas'
    }

@login_required
def registrar_parto_para_madre(request, madre_pk):
    """
    Registrar un nuevo parto para una madre específica (desde el dashboard)
    """
    madre = get_object_or_404(Madre, pk=madre_pk)
    
    # Verificar permisos
    if not request.user.puede_crear_partos:
        messages.error(request, 'No tienes permiso para registrar partos')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = PartoForm(request.POST, user=request.user)
        if form.is_valid():
            parto = form.save(commit=False)
            parto.madre = madre  # Asignar la madre automáticamente
            parto.usuario_registro = request.user  # Asignar el usuario
            parto.save()
            form.save_m2m()  # Guardar relaciones many-to-many si existen
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREATE_PARTO',
                tabla_afectada='Parto',
                registro_id=parto.id,
                detalles=f'Parto registrado para madre {madre.get_nombre()} - Tipo: {parto.tipo_parto}, Fecha: {parto.fecha_parto}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, f'Parto registrado exitosamente para {madre.get_nombre()}')
            return redirect('core:parto_detail', pk=parto.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Inicializar el formulario sin madre pre-seleccionada
        form = PartoForm(user=request.user)
    
    # Descifrar datos de la madre para mostrar en el template
    madre.nombre_descifrado = madre.get_nombre()
    madre.rut_descifrado = madre.get_rut()
    
    context = {
        'form': form,
        'title': 'Registrar Parto',
        'madre': madre  # Pasamos la madre al template
    }
    return render(request,'core/parto_form.html', context)

@login_required
def registrar_parto_completo(request, madre_pk):
    """
    Registrar parto y recién nacido en una sola vista
    VERSIÓN FINAL - Corrige el problema de usuario_registro
    """
    madre = get_object_or_404(Madre, pk=madre_pk)
    
    # Verificar permisos
    if not request.user.puede_crear_partos:
        messages.error(request, 'No tienes permiso para registrar partos')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        parto_form = PartoForm(request.POST, user=request.user)
        
        if parto_form.is_valid():
            # Paso 1: Guardar el parto
            parto = parto_form.save(commit=False)
            parto.madre = madre
            parto.usuario_registro = request.user
            parto.save()
            parto_form.save_m2m()
            
            # Paso 2: Preparar datos del RN con el ID del parto
            rn_data = request.POST.copy()
            rn_data['parto'] = str(parto.pk)
            
            # Paso 3: Crear formulario del RN
            rn_form = RecienNacidoForm(rn_data, user=request.user)
            
            if rn_form.is_valid():
                # Paso 4: Guardar RN
                recien_nacido = rn_form.save(commit=False)
                recien_nacido.parto = parto
                
                # CRÍTICO: Verificar que usuario_registro esté asignado
                if not hasattr(recien_nacido, 'usuario_registro') or recien_nacido.usuario_registro is None:
                    recien_nacido.usuario_registro = request.user
                
                try:
                    recien_nacido.save()
                    
                    # Registrar en auditoría
                    LogAuditoria.registrar(
                        usuario=request.user,
                        accion='CREATE_PARTO_COMPLETO',
                        tabla_afectada='Parto',
                        registro_id=parto.id,
                        detalles=f'Parto y RN registrados para {madre.get_nombre()} - Tipo: {parto.tipo_parto}, Peso RN: {recien_nacido.peso_gramos}g',
                        ip=get_client_ip(request)
                    )
                    
                    messages.success(request, f'Parto y recién nacido registrados exitosamente para {madre.get_nombre()}')
                    return redirect('core:parto_detail', pk=parto.pk)
                    
                except Exception as e:
                    # Rollback: eliminar el parto si el RN falla
                    parto.delete()
                    messages.error(request, f'Error al guardar recién nacido: {str(e)}')
            else:
                # Rollback: eliminar el parto si la validación del RN falla
                parto.delete()
                for field, errors in rn_form.errors.items():
                    for error in errors:
                        messages.error(request, f'Recién Nacido - {field}: {error}')
        else:
            # Mostrar errores del parto
            for field, errors in parto_form.errors.items():
                for error in errors:
                    messages.error(request, f'Parto - {field}: {error}')
        
        # Recrear formularios con datos POST para mostrar errores
        rn_form = RecienNacidoForm(request.POST, user=request.user)
    else:
        # GET request: formularios vacíos
        parto_form = PartoForm(user=request.user)
        rn_form = RecienNacidoForm(user=request.user)
    
    # Descifrar datos de la madre
    madre.nombre_descifrado = madre.get_nombre()
    madre.rut_descifrado = madre.get_rut()
    
    context = {
        'parto_form': parto_form,
        'rn_form': rn_form,
        'title': 'Registro de Parto',
        'madre': madre
    }
    return render(request, 'core/parto_completo_form.html', context)

@login_required
def partograma_list(request):
    """
    Vista de listado de partogramas (pantalla principal)
    Muestra todas las madres que tienen partos
    """
    if not request.user.puede_crear_partos:
        messages.error(request, 'No tiene permisos para acceder a partogramas')
        return redirect('core:dashboard')
    
    # Obtener búsqueda
    busqueda_query = request.GET.get('busqueda', '')
    
    # Lógica de permisos
    if request.user.puede_ver_todos_partos:
        madres_qs = Madre.objects.filter(partos__isnull=False).distinct()
    else:
        madres_qs = Madre.objects.filter(
            partos__usuario_registro=request.user
        ).distinct()
    
    # Aplicar búsqueda
    if busqueda_query:
        madres_qs = madres_qs.filter(
            Q(rut_hash=crypto_service.hash_data(busqueda_query)) |
            Q(nombre_hash=crypto_service.hash_data(busqueda_query)) |
            Q(ficha_clinica_numero__icontains=busqueda_query)
        )
    
    # Descifrar datos y agregar información de partos
    madres = []
    for madre in madres_qs:
        madre.nombre_descifrado = madre.get_nombre()
        madre.rut_descifrado = madre.get_rut()
        
        # Obtener el último parto de esta madre
        if request.user.puede_ver_todos_partos:
            ultimo_parto = madre.partos.order_by('-fecha_parto').first()
        else:
            ultimo_parto = madre.partos.filter(
                usuario_registro=request.user
            ).order_by('-fecha_parto').first()
        
        if ultimo_parto:
            madre.ultimo_parto = ultimo_parto
            madre.tiene_partograma = bool(ultimo_parto.partograma_data)
            madres.append(madre)
    
    context = {
        'madres': madres,
        'busqueda_query': busqueda_query,
    }
    
    return render(request, 'core/partograma_list.html', context)


@login_required
def partograma_create(request, parto_pk):
    """
    Vista para crear un nuevo partograma
    """
    parto = get_object_or_404(Parto, pk=parto_pk)
    
    # Verificar permisos
    if not request.user.puede_crear_partos:
        messages.error(request, 'No tiene permisos para crear partogramas')
        return redirect('core:parto_detail', pk=parto_pk)
    
    # Verificar acceso al parto
    if not request.user.puede_ver_todos_partos and parto.usuario_registro != request.user:
        messages.error(request, 'No tiene permiso para acceder a este parto')
        return redirect('core:dashboard')
    
    # Verificar si ya existe un partograma
    if parto.partograma_data:
        messages.warning(request, 'Este parto ya tiene un partograma. Use la opción de editar.')
        return redirect('core:partograma_update', parto_pk=parto_pk)
    
    if request.method == 'POST':
        form = PartogramaForm(request.POST)
        if form.is_valid():
            # Guardar datos en formato JSON
            parto.partograma_data = form.to_json()
            parto.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREATE_PARTOGRAMA',
                tabla_afectada='Parto',
                registro_id=parto.id,
                detalles=f'Partograma creado para parto {parto.id} - Madre: {parto.madre.get_nombre()}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Partograma registrado exitosamente')
            return redirect('core:parto_detail', pk=parto_pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PartogramaForm()
    
    # Descifrar datos de la madre
    parto.madre.nombre_descifrado = parto.madre.get_nombre()
    parto.madre.rut_descifrado = parto.madre.get_rut()
    
    context = {
        'form': form,
        'parto': parto,
        'title': 'Crear Partograma'
    }
    
    return render(request, 'core/partograma_form.html', context)


@login_required
def partograma_update(request, parto_pk):
    """
    Vista para editar un partograma existente
    """
    parto = get_object_or_404(Parto, pk=parto_pk)
    
    # Verificar permisos
    if not request.user.puede_editar_partos:
        messages.error(request, 'No tiene permisos para editar partogramas')
        return redirect('core:parto_detail', pk=parto_pk)
    
    # Verificar acceso al parto
    if not request.user.puede_ver_todos_partos and parto.usuario_registro != request.user:
        messages.error(request, 'No tiene permiso para acceder a este parto')
        return redirect('core:dashboard')
    
    # Verificar si existe un partograma
    if not parto.partograma_data:
        messages.warning(request, 'Este parto no tiene un partograma. Use la opción de crear.')
        return redirect('core:partograma_create', parto_pk=parto_pk)
    
    if request.method == 'POST':
        form = PartogramaForm(request.POST)
        if form.is_valid():
            # Actualizar datos en formato JSON
            parto.partograma_data = form.to_json()
            parto.save()
            
            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='UPDATE_PARTOGRAMA',
                tabla_afectada='Parto',
                registro_id=parto.id,
                detalles=f'Partograma actualizado para parto {parto.id}',
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Partograma actualizado exitosamente')
            return redirect('core:parto_detail', pk=parto_pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        # Cargar datos existentes
        initial_data = {}
        if parto.partograma_data:
            from datetime import datetime as dt
            partograma = parto.partograma_data
            
            # Convertir hora_inicio de string a objeto time
            if partograma.get('hora_inicio'):
                try:
                    hora = dt.strptime(partograma['hora_inicio'], '%H:%M').time()
                    initial_data['hora_inicio'] = hora
                except:
                    pass
            
            initial_data['dilatacion_cm'] = partograma.get('dilatacion_cm', '')
            initial_data['fcf_latidos'] = partograma.get('fcf_latidos', '')
            initial_data['contracciones'] = partograma.get('contracciones', '')
            initial_data['presion_arterial'] = partograma.get('presion_arterial', '')
            initial_data['observaciones_clinicas'] = partograma.get('observaciones_clinicas', '')
        
        form = PartogramaForm(initial=initial_data)
    
    # Descifrar datos de la madre
    parto.madre.nombre_descifrado = parto.madre.get_nombre()
    parto.madre.rut_descifrado = parto.madre.get_rut()
    
    context = {
        'form': form,
        'parto': parto,
        'title': 'Editar Partograma',
        'is_edit': True
    }
    
    return render(request, 'core/partograma_form.html', context)

@login_required
def epicrisis_list(request):
    """
    Vista de listado de epicrisis (pantalla principal)
    Muestra todas las madres que tienen partos
    """
    if not request.user.puede_crear_partos:
        messages.error(request, 'No tiene permisos para acceder a epicrisis')
        return redirect('core:dashboard')
    
    # Obtener búsqueda
    busqueda_query = request.GET.get('busqueda', '')
    
    # Lógica de permisos
    if request.user.puede_ver_todos_partos:
        madres_qs = Madre.objects.filter(partos__isnull=False).distinct()
    else:
        madres_qs = Madre.objects.filter(
            partos__usuario_registro=request.user
        ).distinct()
    
    # Aplicar búsqueda
    if busqueda_query:
        madres_qs = madres_qs.filter(
            Q(rut_hash=crypto_service.hash_data(busqueda_query)) |
            Q(nombre_hash=crypto_service.hash_data(busqueda_query)) |
            Q(ficha_clinica_numero__icontains=busqueda_query)
        )
    
    # Descifrar datos y agregar información de partos
    madres = []
    for madre in madres_qs:
        madre.nombre_descifrado = madre.get_nombre()
        madre.rut_descifrado = madre.get_rut()
        
        # Obtener el último parto de esta madre
        if request.user.puede_ver_todos_partos:
            ultimo_parto = madre.partos.order_by('-fecha_parto').first()
        else:
            ultimo_parto = madre.partos.filter(
                usuario_registro=request.user
            ).order_by('-fecha_parto').first()
        
        if ultimo_parto:
            madre.ultimo_parto = ultimo_parto
            madre.tiene_epicrisis = bool(ultimo_parto.epicrisis_data)
            madres.append(madre)
    
    context = {
        'madres': madres,
        'busqueda_query': busqueda_query,
    }
    
    return render(request, 'core/epicrisis_list.html', context)


@login_required
def crear_epicrisis(request, pk):
    """Crear epicrisis e indicaciones (solo médicos)"""
    parto = get_object_or_404(Parto, pk=pk)

    # Verificar permisos (solo médicos pueden crear epicrisis)
    if not request.user.puede_anexar_correccion:  # Usamos el mismo permiso de médico
        messages.error(request, 'Solo los médicos pueden crear epicrisis.')
        return redirect('core:parto_detail', pk=parto.pk)

    if request.method == 'POST':
        form = EpicrisisForm(request.POST)
        formset = IndicacionFormSet(request.POST, instance=parto, prefix='indicaciones')

        if form.is_valid() and formset.is_valid():
            # Guardar datos de epicrisis en el JSONField
            parto.epicrisis_data = {
                'motivo_ingreso': form.cleaned_data.get('motivo_ingreso', ''),
                'resumen_evolucion': form.cleaned_data.get('resumen_evolucion', ''),
                'diagnostico_egreso': form.cleaned_data.get('diagnostico_egreso', ''),
                'condicion_egreso': form.cleaned_data.get('condicion_egreso', ''),
                'control_posterior': form.cleaned_data.get('control_posterior', ''),
                'indicaciones_alta': form.cleaned_data.get('indicaciones_alta', ''),
                'observaciones': form.cleaned_data.get('observaciones', ''),
                'medico_id': str(request.user.pk),
                'medico_nombre': request.user.nombre_completo,
                'fecha_creacion': timezone.now().isoformat()
            }
            parto.save()

            # Guardar el formset de indicaciones
            formset.save()

            # Registrar en auditoría
            LogAuditoria.registrar(
                usuario=request.user,
                accion='CREAR_EPICRISIS',
                tabla_afectada='Parto',
                registro_id=parto.id,
                detalles=f"Epicrisis creada para parto {parto.id} - Madre: {parto.madre.get_nombre()}",
                ip=get_client_ip(request)
            )
            
            messages.success(request, 'Epicrisis e indicaciones guardadas exitosamente.')
            return redirect('core:epicrisis_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            for form_errors in formset.errors:
                for field, errors in form_errors.items():
                    for error in errors:
                        messages.error(request, f'Indicación - {field}: {error}')
    else:
        # Cargar datos existentes si ya hay epicrisis
        initial_data = parto.epicrisis_data if parto.epicrisis_data else {}
        form = EpicrisisForm(initial=initial_data)
        formset = IndicacionFormSet(instance=parto, prefix='indicaciones')

    # Descifrar datos de la madre
    parto.madre.nombre_descifrado = parto.madre.get_nombre()
    parto.madre.rut_descifrado = parto.madre.get_rut()

    context = {
        'form': form,
        'formset': formset,
        'parto': parto,
        'madre': parto.madre,
        'title': 'Epicrisis e Indicaciones Médicas'
    }

    return render(request, 'core/epicrisis_form.html', context)


@login_required
def ver_epicrisis(request, pk):
    """
    Vista de solo lectura de una epicrisis
    """
    parto = get_object_or_404(Parto, pk=pk)
    
    # Verificar permisos
    if not request.user.puede_ver_todos_partos and parto.usuario_registro != request.user:
        messages.error(request, 'No tiene permiso para ver este registro')
        return redirect('core:epicrisis_list')
    
    # Verificar que existe epicrisis
    if not parto.epicrisis_data:
        messages.warning(request, 'Este parto no tiene epicrisis registrada')
        return redirect('core:epicrisis_list')
    
    # Descifrar datos de la madre
    parto.madre.nombre_descifrado = parto.madre.get_nombre()
    parto.madre.rut_descifrado = parto.madre.get_rut()
    
    # Obtener indicaciones
    indicaciones = parto.indicaciones.all()
    
    context = {
        'parto': parto,
        'madre': parto.madre,
        'epicrisis': parto.epicrisis_data,
        'indicaciones': indicaciones,
    }
    
    return render(request, 'core/epicrisis_ver.html', context)