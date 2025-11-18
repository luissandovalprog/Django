# utils/pdf_rem.py
"""
Generador de Reportes REM en PDF
Basado en REM Serie A sección A24 y otros relacionados
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from django.utils import timezone
from datetime import datetime


def generar_rem_pdf(partos, fecha_inicio, fecha_fin, usuario):
    """
    Genera el reporte REM completo en PDF
    Incluye todas las secciones según normativa MINSAL
    """
    buffer = BytesIO()
    
    # Configurar documento en orientación horizontal para tablas anchas
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'TituloREM',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        alignment=TA_CENTER,
        spaceAfter=8
    )
    
    subtitulo_style = ParagraphStyle(
        'SubtituloREM',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#4b5563'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    seccion_style = ParagraphStyle(
        'SeccionREM',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    # ===== ENCABEZADO DEL REPORTE =====
    elements.append(Paragraph('REPORTE ESTADÍSTICO MENSUAL (REM)', titulo_style))
    elements.append(Paragraph('HOSPITAL CLÍNICO HERMINDA MARTÍN', subtitulo_style))
    elements.append(Paragraph(f'Servicio de Obstetricia y Ginecología', 
                             ParagraphStyle('subtitulo2', parent=subtitulo_style, fontSize=10)))
    
    # Información del periodo
    periodo_text = f'<b>Periodo:</b> {fecha_inicio.strftime("%d-%m-%Y")} a {fecha_fin.strftime("%d-%m-%Y")}'
    elements.append(Paragraph(periodo_text, 
                             ParagraphStyle('periodo', parent=subtitulo_style, fontSize=11, alignment=TA_LEFT)))
    
    fecha_generacion = timezone.now().strftime('%d-%m-%Y %H:%M:%S')
    elements.append(Paragraph(f'<b>Fecha de generación:</b> {fecha_generacion}', 
                             ParagraphStyle('fecha_gen', parent=subtitulo_style, fontSize=10, alignment=TA_LEFT)))
    elements.append(Paragraph(f'<b>Generado por:</b> {usuario.nombre_completo}', 
                             ParagraphStyle('generado_por', parent=subtitulo_style, fontSize=10, alignment=TA_LEFT)))
    
    elements.append(Spacer(1, 10*mm))
    
    # ===== RESUMEN ESTADÍSTICO =====
    elements.append(Paragraph('RESUMEN ESTADÍSTICO', seccion_style))
    
    # Calcular estadísticas
    from reportes.views import calcular_estadisticas_rem_bs22
    stats = calcular_estadisticas_rem_bs22(partos)
    
    # Tabla de resumen
    resumen_data = [
        ['INDICADOR', 'CANTIDAD', 'PORCENTAJE'],
        ['Total de Partos', str(partos.count()), '100%'],
        ['', '', ''],
        ['TIPO DE PARTO', '', ''],
        ['Partos Eutócicos', str(stats['eutocicos']), f"{_porcentaje(stats['eutocicos'], partos.count())}%"],
        ['Cesáreas Electivas', str(stats['cesareas_electivas']), f"{_porcentaje(stats['cesareas_electivas'], partos.count())}%"],
        ['Cesáreas de Urgencia', str(stats['cesareas_urgencia']), f"{_porcentaje(stats['cesareas_urgencia'], partos.count())}%"],
        ['Fórceps', str(stats['forceps']), f"{_porcentaje(stats['forceps'], partos.count())}%"],
        ['Ventosa', str(stats['ventosa']), f"{_porcentaje(stats['ventosa'], partos.count())}%"],
        ['', '', ''],
        ['RECIÉN NACIDOS', '', ''],
        ['RN Vivos', str(stats['rn_vivos']), f"{_porcentaje(stats['rn_vivos'], stats['rn_vivos'] + stats['rn_muertos'])}%"],
        ['RN Nacidos Muertos', str(stats['rn_muertos']), f"{_porcentaje(stats['rn_muertos'], stats['rn_vivos'] + stats['rn_muertos'])}%"],
        ['RN Masculinos', str(stats['rn_masculinos']), f"{_porcentaje(stats['rn_masculinos'], stats['rn_vivos'])}%"],
        ['RN Femeninos', str(stats['rn_femeninos']), f"{_porcentaje(stats['rn_femeninos'], stats['rn_vivos'])}%"],
        ['', '', ''],
        ['PESO AL NACER', '', ''],
        ['Bajo Peso (<2500g)', str(stats['rn_bajo_peso']), f"{_porcentaje(stats['rn_bajo_peso'], stats['rn_vivos'])}%"],
        ['Peso Normal (2500-3999g)', str(stats['rn_peso_normal']), f"{_porcentaje(stats['rn_peso_normal'], stats['rn_vivos'])}%"],
        ['Sobre Peso (≥4000g)', str(stats['rn_sobre_peso']), f"{_porcentaje(stats['rn_sobre_peso'], stats['rn_vivos'])}%"],
        ['', '', ''],
        ['EDAD GESTACIONAL', '', ''],
        ['Pretérmino (<37 sem)', str(stats['pretermino']), f"{_porcentaje(stats['pretermino'], partos.count())}%"],
        ['A Término (37-41 sem)', str(stats['termino']), f"{_porcentaje(stats['termino'], partos.count())}%"],
        ['Postérmino (>41 sem)', str(stats['postermino']), f"{_porcentaje(stats['postermino'], partos.count())}%"],
    ]
    
    resumen_table = Table(resumen_data, colWidths=[150*mm, 30*mm, 30*mm])
    resumen_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Subtítulos de sección
        ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#e0e7ff')),
        ('BACKGROUND', (0, 10), (0, 10), colors.HexColor('#e0e7ff')),
        ('BACKGROUND', (0, 16), (0, 16), colors.HexColor('#e0e7ff')),
        ('BACKGROUND', (0, 20), (0, 20), colors.HexColor('#e0e7ff')),
        ('FONTNAME', (0, 3), (0, 3), 'Helvetica-Bold'),
        ('FONTNAME', (0, 10), (0, 10), 'Helvetica-Bold'),
        ('FONTNAME', (0, 16), (0, 16), 'Helvetica-Bold'),
        ('FONTNAME', (0, 20), (0, 20), 'Helvetica-Bold'),
        # Datos
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(resumen_table)
    elements.append(PageBreak())
    
    # ===== DETALLE DE PARTOS =====
    elements.append(Paragraph('DETALLE DE PARTOS', seccion_style))
    elements.append(Spacer(1, 5*mm))
    
    # Tabla de detalle
    detalle_data = [
        ['Fecha', 'Ficha', 'Edad', 'Nacionalidad', 'Previsión', 'Tipo Parto', 'Anestesia', 'EG', 'RN Estado', 'Peso', 'APGAR']
    ]
    
    for parto in partos:
        madre = parto.madre
        rn = parto.recien_nacidos.first()
        
        # Calcular edad de la madre
        edad_madre = _calcular_edad(madre.fecha_nacimiento) if madre.fecha_nacimiento else 'N/A'
        
        detalle_data.append([
            parto.fecha_parto.strftime('%d-%m-%Y'),
            madre.ficha_clinica_numero or 'N/A',
            str(edad_madre),
            madre.nacionalidad[:3] if madre.nacionalidad else 'N/A',
            madre.prevision[:3] if madre.prevision else 'N/A',
            _abreviar_tipo_parto(parto.tipo_parto),
            parto.anestesia[:3] if parto.anestesia else 'N/A',
            f"{parto.edad_gestacional}s" if parto.edad_gestacional else 'N/A',
            'V' if rn and rn.estado_al_nacer == 'Vivo' else 'M',
            f"{rn.peso_gramos}g" if rn and rn.peso_gramos else 'N/A',
            f"{rn.apgar_1_min}/{rn.apgar_5_min}" if rn and rn.apgar_1_min and rn.apgar_5_min else 'N/A'
        ])
    
    detalle_table = Table(detalle_data, colWidths=[23*mm, 20*mm, 15*mm, 20*mm, 20*mm, 25*mm, 20*mm, 15*mm, 18*mm, 18*mm, 18*mm])
    detalle_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Datos
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#d1d5db')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        # Colores alternados
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb')) for i in range(2, len(detalle_data), 2)]
    ]))
    
    elements.append(detalle_table)
    
    # Si hay muchos partos, agregar página adicional con recién nacidos
    if partos.count() > 10:
        elements.append(PageBreak())
    else:
        elements.append(Spacer(1, 10*mm))
    
    # ===== DETALLE DE RECIÉN NACIDOS =====
    elements.append(Paragraph('DETALLE DE RECIÉN NACIDOS', seccion_style))
    elements.append(Spacer(1, 5*mm))
    
    rn_data = [
        ['RUT Provisorio', 'Sexo', 'Peso (g)', 'Talla (cm)', 'APGAR 1\'', 'APGAR 5\'', 'Vit K', 'Prof. Oft.', 'Fecha Nacimiento']
    ]
    
    for parto in partos:
        for rn in parto.recien_nacidos.all():
            rn_data.append([
                rn.rut_provisorio[:15] if rn.rut_provisorio else f'RN-{str(rn.id)[:8]}',
                rn.sexo[0] if rn.sexo else 'I',
                str(rn.peso_gramos) if rn.peso_gramos else 'N/A',
                str(rn.talla_cm) if rn.talla_cm else 'N/A',
                str(rn.apgar_1_min) if rn.apgar_1_min is not None else 'N/A',
                str(rn.apgar_5_min) if rn.apgar_5_min is not None else 'N/A',
                'Sí' if rn.profilaxis_vit_k else 'No',
                'Sí' if rn.profilaxis_oftalmica else 'No',
                parto.fecha_parto.strftime('%d-%m-%Y')
            ])
    
    rn_table = Table(rn_data, colWidths=[35*mm, 18*mm, 22*mm, 22*mm, 20*mm, 20*mm, 18*mm, 22*mm, 28*mm])
    rn_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Datos
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#d1d5db')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        # Colores alternados
        *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f9fafb')) for i in range(2, len(rn_data), 2)]
    ]))
    
    elements.append(rn_table)
    
    # ===== PIE DE PÁGINA =====
    elements.append(Spacer(1, 15*mm))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph('_' * 80, footer_style))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(f'Reporte generado el {fecha_generacion} por {usuario.nombre_completo}', footer_style))
    elements.append(Paragraph('Sistema de Trazabilidad de Partos v1.0 - Hospital Clínico Herminda Martín', 
                             ParagraphStyle('footer2', parent=footer_style, fontSize=7)))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph('Chillán, Chile', 
                             ParagraphStyle('footer3', parent=footer_style, fontSize=7, fontName='Helvetica-Oblique')))
    
    # Construir PDF
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def _porcentaje(valor, total):
    """Calcula el porcentaje"""
    if total == 0:
        return 0
    return round((valor / total) * 100, 1)


def _calcular_edad(fecha_nacimiento):
    """Calcula la edad en años"""
    if not fecha_nacimiento:
        return 0
    
    hoy = timezone.now().date()
    edad = hoy.year - fecha_nacimiento.year
    
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    
    return edad


def _abreviar_tipo_parto(tipo_parto):
    """Abrevia el tipo de parto para la tabla"""
    abreviaturas = {
        'Eutócico': 'Eutócico',
        'Cesárea Electiva': 'Cesárea E.',
        'Cesárea Urgencia': 'Cesárea U.',
        'Fórceps': 'Fórceps',
        'Ventosa': 'Ventosa'
    }
    return abreviaturas.get(tipo_parto, tipo_parto[:10])