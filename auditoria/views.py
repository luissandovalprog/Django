# auditoria/views.py
"""
Vistas de Auditoría
Sistema de logs cifrados con filtrado avanzado
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from django.utils import timezone
from .models import LogAuditoria
from accounts.models import Usuario
import json


def get_client_ip(request):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def es_admin_sistema(user):
    """Verifica si el usuario es administrador del sistema"""
    return user.is_authenticated and (user.is_superuser or user.puede_gestionar_usuarios)


@login_required
def historial_auditoria(request):
    """Vista de auditoría - SOLO Admin Sistema y Supervisor"""
    if not request.user.puede_ver_auditoria:
        messages.error(request, 'No tiene permisos para acceder a la auditoría.')
        return redirect('core:dashboard')
    """
    Vista principal de auditoría con filtros avanzados
    """
    # Obtener parámetros de filtrado
    busqueda_query = request.GET.get('busqueda', '')
    accion_filtro = request.GET.get('accion', 'todas')
    usuario_filtro = request.GET.get('usuario', 'todos')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    # Query base
    logs = LogAuditoria.objects.select_related('usuario', 'usuario__rol').all()

    # Aplicar filtro de búsqueda general
    if busqueda_query:
        logs = logs.filter(
            Q(usuario__username__icontains=busqueda_query) |
            Q(usuario__nombre_completo__icontains=busqueda_query) |
            Q(accion__icontains=busqueda_query) |
            Q(ip_usuario__icontains=busqueda_query) |
            Q(tabla_afectada__icontains=busqueda_query)
        )

    # Filtro por acción
    if accion_filtro != 'todas':
        logs = logs.filter(accion=accion_filtro)

    # Filtro por usuario
    if usuario_filtro != 'todos':
        logs = logs.filter(usuario__username=usuario_filtro)

    # Filtro por rango de fechas
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            logs = logs.filter(fecha_accion__gte=fecha_desde_dt)
        except ValueError:
            messages.error(request, 'Formato de fecha desde inválido')

    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            # Agregar 1 día para incluir todo el día
            fecha_hasta_dt = fecha_hasta_dt + timedelta(days=1)
            logs = logs.filter(fecha_accion__lt=fecha_hasta_dt)
        except ValueError:
            messages.error(request, 'Formato de fecha hasta inválido')

    # Ordenar por fecha descendente
    logs = logs.order_by('-fecha_accion')

    # Paginación dinámica
    total_filtrados = logs.count()
    try:
        limit = int(request.GET.get('limit', 10))  # Por defecto 10 registros
        limit = min(limit, 500)  # Máximo 500 por rendimiento
        limit = max(limit, 10)   # Mínimo 10
    except (ValueError, TypeError):
        limit = 10
    
    logs = logs[:limit]

    # Descifrar detalles para mostrar
    for log in logs:
        log.detalles_descifrados = log.get_detalles()

    # Obtener estadísticas
    total_eventos = LogAuditoria.objects.count()
    
    # Usuarios activos (última semana)
    hace_una_semana = timezone.now() - timedelta(days=7)
    usuarios_activos = LogAuditoria.objects.filter(
        fecha_accion__gte=hace_una_semana
    ).values('usuario').distinct().count()

    # Eventos hoy
    hoy_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    eventos_hoy = LogAuditoria.objects.filter(fecha_accion__gte=hoy_inicio).count()

    # Acciones únicas
    acciones_unicas = LogAuditoria.objects.values_list('accion', flat=True).distinct().order_by('accion')

    # Usuarios únicos
    usuarios_unicos = Usuario.objects.filter(
        logs_auditoria__isnull=False
    ).distinct().order_by('nombre_completo')

    # Top 10 acciones más frecuentes
    acciones_frecuentes = LogAuditoria.objects.values('accion').annotate(
        total=Count('id')
    ).order_by('-total')[:10]

    context = {
        'logs': logs,
        'total_eventos': total_eventos,
        'total_filtrados': total_filtrados,
        'usuarios_activos': usuarios_activos,
        'eventos_hoy': eventos_hoy,
        'acciones_unicas': acciones_unicas,
        'usuarios_unicos': usuarios_unicos,
        'acciones_frecuentes': acciones_frecuentes,
        'busqueda': busqueda_query,
        'accion_filtro': accion_filtro,
        'usuario_filtro': usuario_filtro,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'limit': limit,  # Para la paginación en la plantilla
    }

    return render(request, 'auditoria/historial.html', context)


@login_required
@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def exportar_auditoria_json(request):
    """
    Exporta los logs de auditoría filtrados a JSON
    """
    # Obtener los mismos filtros que historial_auditoria
    busqueda_query = request.GET.get('busqueda', '')
    accion_filtro = request.GET.get('accion', 'todas')
    usuario_filtro = request.GET.get('usuario', 'todos')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    # Query base
    logs = LogAuditoria.objects.select_related('usuario', 'usuario__rol').all()

    # Aplicar los mismos filtros
    if busqueda_query:
        logs = logs.filter(
            Q(usuario__username__icontains=busqueda_query) |
            Q(usuario__nombre_completo__icontains=busqueda_query) |
            Q(accion__icontains=busqueda_query) |
            Q(ip_usuario__icontains=busqueda_query) |
            Q(tabla_afectada__icontains=busqueda_query)
        )

    if accion_filtro != 'todas':
        logs = logs.filter(accion=accion_filtro)

    if usuario_filtro != 'todos':
        logs = logs.filter(usuario__username=usuario_filtro)

    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            logs = logs.filter(fecha_accion__gte=fecha_desde_dt)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_dt = fecha_hasta_dt + timedelta(days=1)
            logs = logs.filter(fecha_accion__lt=fecha_hasta_dt)
        except ValueError:
            pass

    # Ordenar y limitar
    logs = logs.order_by('-fecha_accion')[:500]

    # Construir datos para JSON
    datos_exportacion = []
    for log in logs:
        datos_exportacion.append({
            'id': str(log.id),
            'fecha_accion': log.fecha_accion.strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': {
                'username': log.usuario.username,
                'nombre_completo': log.usuario.nombre_completo,
                'rol': log.usuario.rol.nombre if log.usuario.rol else 'Sin rol'
            },
            'accion': log.accion,
            'tabla_afectada': log.tabla_afectada or '',
            'registro_id': str(log.registro_id_uuid) if log.registro_id_uuid else '',
            'detalles': log.get_detalles() or '',
            'ip_usuario': log.ip_usuario or '',
        })

    # Registrar exportación
    LogAuditoria.registrar(
        usuario=request.user,
        accion='EXPORTAR_JSON',
        detalles=f'Exportados {len(datos_exportacion)} registros de auditoría',
        ip=get_client_ip(request)
    )

    # Crear respuesta JSON
    response = HttpResponse(
        json.dumps(datos_exportacion, indent=2, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )
    
    fecha_actual = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="auditoria_{fecha_actual}.json"'
    
    return response


@login_required
@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def estadisticas_auditoria(request):
    """
    Vista con estadísticas avanzadas de auditoría
    """
    # Estadísticas por usuario
    stats_por_usuario = LogAuditoria.objects.values(
        'usuario__username',
        'usuario__nombre_completo'
    ).annotate(
        total_acciones=Count('id')
    ).order_by('-total_acciones')[:10]

    # Estadísticas por acción
    stats_por_accion = LogAuditoria.objects.values('accion').annotate(
        total=Count('id')
    ).order_by('-total')[:10]

    # Actividad por día (últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    actividad_diaria = LogAuditoria.objects.filter(
        fecha_accion__gte=hace_30_dias
    ).extra(
        select={'dia': 'DATE(fecha_accion)'}
    ).values('dia').annotate(
        total=Count('id')
    ).order_by('dia')

    # Acciones por hora del día
    actividad_horaria = LogAuditoria.objects.filter(
        fecha_accion__gte=hace_30_dias
    ).extra(
        select={'hora': 'EXTRACT(HOUR FROM fecha_accion)'}
    ).values('hora').annotate(
        total=Count('id')
    ).order_by('hora')

    # Tablas más modificadas
    tablas_modificadas = LogAuditoria.objects.exclude(
        tabla_afectada__isnull=True
    ).exclude(
        tabla_afectada=''
    ).values('tabla_afectada').annotate(
        total=Count('id')
    ).order_by('-total')[:10]

    context = {
        'stats_por_usuario': stats_por_usuario,
        'stats_por_accion': stats_por_accion,
        'actividad_diaria': list(actividad_diaria),
        'actividad_horaria': list(actividad_horaria),
        'tablas_modificadas': tablas_modificadas,
    }

    return render(request, 'auditoria/estadisticas.html', context)


@login_required
@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def detalle_log(request, log_id):
    """
    Vista de detalle de un log específico
    """
    log = get_object_or_404(LogAuditoria, pk=log_id)
    log.detalles_descifrados = log.get_detalles()

    # Obtener logs relacionados (mismo usuario, misma hora aproximada)
    logs_relacionados = LogAuditoria.objects.filter(
        usuario=log.usuario,
        fecha_accion__gte=log.fecha_accion - timedelta(minutes=5),
        fecha_accion__lte=log.fecha_accion + timedelta(minutes=5)
    ).exclude(pk=log.pk).order_by('fecha_accion')[:10]

    for log_rel in logs_relacionados:
        log_rel.detalles_descifrados = log_rel.get_detalles()

    context = {
        'log': log,
        'logs_relacionados': logs_relacionados,
    }

    return render(request, 'auditoria/detalle_log.html', context)


@login_required
@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def buscar_por_registro(request, tabla, registro_id):
    """
    Busca todos los logs relacionados con un registro específico
    """
    logs = LogAuditoria.objects.filter(
        tabla_afectada=tabla,
        registro_id_uuid=registro_id
    ).select_related('usuario', 'usuario__rol').order_by('-fecha_accion')

    for log in logs:
        log.detalles_descifrados = log.get_detalles()

    context = {
        'logs': logs,
        'tabla': tabla,
        'registro_id': registro_id,
    }

    return render(request, 'auditoria/logs_por_registro.html', context)


@login_required
@user_passes_test(es_admin_sistema, login_url='core:dashboard')
def api_estadisticas_json(request):
    """
    API JSON para estadísticas (para gráficos en frontend)
    """
    tipo = request.GET.get('tipo', 'actividad_diaria')
    
    if tipo == 'actividad_diaria':
        hace_30_dias = timezone.now() - timedelta(days=30)
        datos = LogAuditoria.objects.filter(
            fecha_accion__gte=hace_30_dias
        ).extra(
            select={'dia': 'DATE(fecha_accion)'}
        ).values('dia').annotate(
            total=Count('id')
        ).order_by('dia')
        
        return JsonResponse({
            'labels': [d['dia'].strftime('%Y-%m-%d') for d in datos],
            'data': [d['total'] for d in datos]
        })
    
    elif tipo == 'acciones_frecuentes':
        datos = LogAuditoria.objects.values('accion').annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        return JsonResponse({
            'labels': [d['accion'] for d in datos],
            'data': [d['total'] for d in datos]
        })
    
    elif tipo == 'usuarios_activos':
        hace_7_dias = timezone.now() - timedelta(days=7)
        datos = LogAuditoria.objects.filter(
            fecha_accion__gte=hace_7_dias
        ).values(
            'usuario__username',
            'usuario__nombre_completo'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        return JsonResponse({
            'labels': [d['usuario__nombre_completo'] for d in datos],
            'data': [d['total'] for d in datos]
        })
    
    return JsonResponse({'error': 'Tipo no válido'}, status=400)