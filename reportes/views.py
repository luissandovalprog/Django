"""
Vistas de Reportes
Generación de REM BS22 y exportación a Excel
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from core.models import Parto, RecienNacido, Madre
from auditoria.models import LogAuditoria
import csv
from django.http import HttpResponse
from django.template.loader import render_to_string
from utils.pdf_utils import render_to_pdf


@login_required
def reporte_menu(request):
    """
    Menú principal de reportes
    """
    if not request.user.puede_generar_reportes:
        messages.error(request, 'No tienes permiso para acceder a los reportes')
        return redirect('core:dashboard')
    
    return render(request, 'reportes/menu.html')


@login_required
def generar_rem_bs22(request):
    """
    Genera el Reporte REM BS22: Atenciones de Obstetricia y Ginecología
    """
    if not request.user.puede_generar_reportes:
        messages.error(request, 'No tienes permiso para generar reportes')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            messages.error(request, 'Debe seleccionar ambas fechas')
            return render(request, 'reportes/rem_bs22_form.html')
        
        # Convertir fechas
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')
            return render(request, 'reportes/rem_bs22_form.html')
        
        # Filtrar partos en el rango de fechas
        partos = Parto.objects.filter(
            fecha_parto__gte=fecha_inicio,
            fecha_parto__lte=fecha_fin
        ).select_related('madre').prefetch_related('recien_nacidos')
        
        # Calcular estadísticas para REM BS22
        estadisticas = calcular_estadisticas_rem_bs22(partos)
        
        # Registrar generación de reporte
        LogAuditoria.registrar(
            usuario=request.user,
            accion='GENERAR_REPORTE_REM_BS22',
            detalles=f'Periodo: {fecha_inicio.date()} a {fecha_fin.date()}'
        )
        
        context = {
            'estadisticas': estadisticas,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_partos': partos.count()
        }
        
        return render(request, 'reportes/rem_bs22_resultado.html', context)
    
    return render(request, 'reportes/rem_bs22_form.html')


def calcular_estadisticas_rem_bs22(partos):
    """
    Calcula las estadísticas necesarias para el reporte REM BS22
    Según Manual REM Serie BS
    """
    estadisticas = {
        # Tipos de parto
        'eutocicos': 0,
        'cesareas_electivas': 0,
        'cesareas_urgencia': 0,
        'forceps': 0,
        'ventosa': 0,
        
        # Anestesia
        'epidural': 0,
        'raquidea': 0,
        'general': 0,
        'sin_anestesia': 0,
        
        # Recién nacidos
        'rn_vivos': 0,
        'rn_muertos': 0,
        'rn_masculinos': 0,
        'rn_femeninos': 0,
        
        # Peso
        'rn_bajo_peso': 0,  # < 2500g
        'rn_peso_normal': 0,  # 2500-3999g
        'rn_sobre_peso': 0,  # >= 4000g
        
        # APGAR
        'apgar_bajo': 0,  # < 7 a los 5 min
        'apgar_normal': 0,  # >= 7 a los 5 min
        
        # Edad gestacional
        'pretermino': 0,  # < 37 semanas
        'termino': 0,  # 37-41 semanas
        'postermino': 0,  # > 41 semanas
    }
    
    for parto in partos:
        # Contar tipo de parto
        if parto.tipo_parto == 'Eutócico':
            estadisticas['eutocicos'] += 1
        elif parto.tipo_parto == 'Cesárea Electiva':
            estadisticas['cesareas_electivas'] += 1
        elif parto.tipo_parto == 'Cesárea Urgencia':
            estadisticas['cesareas_urgencia'] += 1
        elif parto.tipo_parto == 'Fórceps':
            estadisticas['forceps'] += 1
        elif parto.tipo_parto == 'Ventosa':
            estadisticas['ventosa'] += 1
        
        # Contar anestesia
        if parto.anestesia == 'Epidural':
            estadisticas['epidural'] += 1
        elif parto.anestesia == 'Raquídea':
            estadisticas['raquidea'] += 1
        elif parto.anestesia == 'General':
            estadisticas['general'] += 1
        elif parto.anestesia == 'Ninguna':
            estadisticas['sin_anestesia'] += 1
        
        # Contar edad gestacional
        if parto.edad_gestacional:
            if parto.edad_gestacional < 37:
                estadisticas['pretermino'] += 1
            elif parto.edad_gestacional <= 41:
                estadisticas['termino'] += 1
            else:
                estadisticas['postermino'] += 1
        
        # Estadísticas de recién nacidos
        for rn in parto.recien_nacidos.all():
            if rn.estado_al_nacer == 'Vivo':
                estadisticas['rn_vivos'] += 1
            else:
                estadisticas['rn_muertos'] += 1
            
            if rn.sexo == 'Masculino':
                estadisticas['rn_masculinos'] += 1
            elif rn.sexo == 'Femenino':
                estadisticas['rn_femeninos'] += 1
            
            # Peso
            if rn.peso_gramos:
                if rn.peso_gramos < 2500:
                    estadisticas['rn_bajo_peso'] += 1
                elif rn.peso_gramos < 4000:
                    estadisticas['rn_peso_normal'] += 1
                else:
                    estadisticas['rn_sobre_peso'] += 1
            
            # APGAR a los 5 minutos
            if rn.apgar_5_min is not None:
                if rn.apgar_5_min < 7:
                    estadisticas['apgar_bajo'] += 1
                else:
                    estadisticas['apgar_normal'] += 1
    
    return estadisticas


@login_required
def exportar_excel(request):
    """
    Exporta datos de partos a formato CSV (compatible con Excel)
    """
    if not request.user.puede_generar_reportes:
        messages.error(request, 'No tienes permiso para exportar datos')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            messages.error(request, 'Debe seleccionar ambas fechas')
            return render(request, 'reportes/exportar_form.html')
        
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        except ValueError:
            messages.error(request, 'Formato de fecha inválido')
            return render(request, 'reportes/exportar_form.html')
        
        # Filtrar partos
        partos = Parto.objects.filter(
            fecha_parto__gte=fecha_inicio,
            fecha_parto__lte=fecha_fin
        ).select_related('madre').prefetch_related('recien_nacidos')
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="partos_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.csv"'
        
        # Escribir BOM para Excel UTF-8
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Encabezados
        writer.writerow([
            'Fecha Parto',
            'Ficha Madre',
            'Edad Gestacional',
            'Tipo Parto',
            'Anestesia',
            'RN Estado',
            'RN Sexo',
            'RN Peso (g)',
            'RN Talla (cm)',
            'APGAR 1min',
            'APGAR 5min',
            'Usuario Registro'
        ])
        
        # Datos
        for parto in partos:
            for rn in parto.recien_nacidos.all():
                writer.writerow([
                    parto.fecha_parto.strftime('%d/%m/%Y %H:%M'),
                    parto.madre.ficha_clinica_id or '',
                    parto.edad_gestacional or '',
                    parto.tipo_parto,
                    parto.anestesia or '',
                    rn.estado_al_nacer,
                    rn.sexo or '',
                    rn.peso_gramos or '',
                    rn.talla_cm or '',
                    rn.apgar_1_min or '',
                    rn.apgar_5_min or '',
                    parto.usuario_registro.username
                ])
        
        # Registrar exportación
        LogAuditoria.registrar(
            usuario=request.user,
            accion='EXPORTAR_EXCEL',
            detalles=f'Exportados {partos.count()} partos del periodo {fecha_inicio.date()} a {fecha_fin.date()}'
        )
        
        return response
    
    return render(request, 'reportes/exportar_form.html')

@login_required
def generar_brazalete_pdf(request, pk):
    parto = get_object_or_404(Parto, pk=pk)
    madre = parto.madre
    rn = parto.recien_nacidos.first() # Asumiendo un RN

    if not rn:
        messages.error(request, 'Este parto aún no tiene un recién nacido registrado.')
        return redirect('core:parto_detail', pk=parto.pk)

    # (React: tienePermiso('generarBrazalete'))
    # Usamos el permiso del modelo Rol de Django
    if not request.user.puede_crear_partos: 
        messages.error(request, 'No tiene permisos para generar brazaletes.')
        return redirect('core:parto_detail', pk=parto.pk)

    context = {
        'parto': parto,
        'madre': madre,
        'rn': rn
    }

    pdf_response = render_to_pdf('reportes/pdf_brazalete.html', context)
    
    if not pdf_response:
        messages.error(request, 'Hubo un error al generar el documento PDF.')
        return redirect('core:parto_detail', pk=parto.pk)
    # --- FIN NUEVA LÓGICA ---

    # Asignamos el nombre al archivo
    nombre_archivo = f'brazalete-{rn.rut_provisorio or rn.id}.pdf'
    pdf_response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    LogAuditoria.registrar(
        usuario=request.user,
        accion='GENERAR_PDF_BRAZALETE',
        tabla_afectada='Parto',
        registro_id=parto.id
    )
    return pdf_response