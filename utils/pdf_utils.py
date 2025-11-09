# utils/pdf_utils.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse
from datetime import datetime


def generar_brazalete_pdf(parto, madre, rn):
    """
    Genera un PDF de brazalete para recién nacido
    Replica el diseño del sistema React original
    """
    # Crear buffer de memoria
    buffer = BytesIO()
    
    # Configurar documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=0,
        bottomMargin=20*mm
    )
    
    # Contenedor de elementos
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo para encabezado principal
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.white,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    # Estilo para subtítulo del encabezado
    subheader_style = ParagraphStyle(
        'CustomSubheader',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.white,
        alignment=TA_CENTER,
        spaceAfter=6
    )
    
    # Estilo para ubicación
    location_style = ParagraphStyle(
        'LocationStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.white,
        alignment=TA_CENTER
    )
    
    # Estilo para títulos de sección
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    # Estilo para labels
    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#1f2937'),
        fontName='Helvetica-Bold'
    )
    
    # Estilo para valores
    value_style = ParagraphStyle(
        'ValueStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#1f2937')
    )
    
    # Estilo para texto pequeño
    small_style = ParagraphStyle(
        'SmallStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    # Estilo para código de barras
    barcode_style = ParagraphStyle(
        'BarcodeStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        alignment=TA_CENTER,
        fontName='Courier'
    )
    
    # ===== ENCABEZADO AZUL =====
    def draw_header(canvas, doc):
        canvas.saveState()
        # Rectángulo azul
        canvas.setFillColor(colors.HexColor('#2563eb'))
        canvas.rect(0, A4[1] - 40*mm, A4[0], 40*mm, fill=True, stroke=False)
        canvas.restoreState()
    
    # Espaciador para el header
    elements.append(Spacer(1, 5*mm))
    
    # Título principal (se dibujará sobre el azul)
    elements.append(Paragraph('HOSPITAL CLÍNICO HERMINDA MARTÍN', header_style))
    elements.append(Paragraph('BRAZALETE DE IDENTIFICACIÓN', subheader_style))
    elements.append(Paragraph('Chillán, Chile', location_style))
    elements.append(Spacer(1, 15*mm))
    
    # ===== SECCIÓN RECIÉN NACIDO =====
    elements.append(Paragraph('RECIÉN NACIDO', section_title_style))
    
    # Línea separadora
    line_table = Table([['']], colWidths=[170*mm])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5*mm, colors.HexColor('#2563eb')),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 5*mm))
    
    # Datos del RN
    rn_data = [
        ['ID:', rn.rut_provisorio or f'RN-{rn.id}'],
        ['RUT:', rn.rut_provisorio or 'Pendiente Registro Civil'],
        ['', ''],
        ['Fecha Nacimiento:', parto.fecha_parto.strftime('%d-%m-%Y')],
        ['Hora:', parto.fecha_parto.strftime('%H:%M')],
        ['', ''],
        ['Peso:', f'{rn.peso_gramos} gramos', 'Talla:', f'{rn.talla_cm} cm'],
        ['APGAR:', f'{rn.apgar_1_min} / {rn.apgar_5_min}', 'Tipo Parto:', parto.tipo_parto],
    ]
    
    # Crear tabla para datos del RN
    rn_table_data = []
    for row in rn_data:
        if len(row) == 2:
            rn_table_data.append([
                Paragraph(f'<b>{row[0]}</b>', label_style),
                Paragraph(row[1], value_style),
                '',
                ''
            ])
        elif len(row) == 4:
            rn_table_data.append([
                Paragraph(f'<b>{row[0]}</b>', label_style),
                Paragraph(row[1], value_style),
                Paragraph(f'<b>{row[2]}</b>', label_style),
                Paragraph(row[3], value_style)
            ])
        else:
            rn_table_data.append(['', '', '', ''])
    
    rn_table = Table(rn_table_data, colWidths=[30*mm, 50*mm, 30*mm, 50*mm])
    rn_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    elements.append(rn_table)
    elements.append(Spacer(1, 10*mm))
    
    # ===== SECCIÓN MADRE =====
    elements.append(Paragraph('MADRE', section_title_style))
    
    # Línea separadora
    line_table2 = Table([['']], colWidths=[170*mm])
    line_table2.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 0.5*mm, colors.HexColor('#2563eb')),
    ]))
    elements.append(line_table2)
    elements.append(Spacer(1, 5*mm))
    
    # Datos de la madre
    madre_data = [
        ['Nombre:', madre.get_nombre() or 'N/A'],
        ['RUT:', madre.get_rut() or 'N/A', 'Edad:', f'{_calcular_edad(madre.fecha_nacimiento)} años'],
        ['Dirección:', madre.direccion or madre.ficha_clinica_id or 'N/A'],
        ['Teléfono:', madre.get_telefono() or 'N/A'],
        ['Previsión:', madre.prevision or 'N/A'],
    ]
    
    # Crear tabla para datos de la madre
    madre_table_data = []
    for row in madre_data:
        if len(row) == 2:
            madre_table_data.append([
                Paragraph(f'<b>{row[0]}</b>', label_style),
                Paragraph(row[1], value_style),
                '',
                ''
            ])
        elif len(row) == 4:
            madre_table_data.append([
                Paragraph(f'<b>{row[0]}</b>', label_style),
                Paragraph(row[1], value_style),
                Paragraph(f'<b>{row[2]}</b>', label_style),
                Paragraph(row[3], value_style)
            ])
    
    madre_table = Table(madre_table_data, colWidths=[30*mm, 50*mm, 30*mm, 50*mm])
    madre_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2*mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2*mm),
    ]))
    elements.append(madre_table)
    elements.append(Spacer(1, 10*mm))
    
    # ===== OBSERVACIONES =====
    if parto.epicrisis_data and parto.epicrisis_data.get('observaciones'):
        elements.append(Paragraph('OBSERVACIONES', section_title_style))
        line_table3 = Table([['']], colWidths=[170*mm])
        line_table3.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 0.5*mm, colors.HexColor('#2563eb')),
        ]))
        elements.append(line_table3)
        elements.append(Spacer(1, 3*mm))
        
        obs_text = parto.epicrisis_data.get('observaciones', 'Parto sin complicaciones.')
        elements.append(Paragraph(obs_text, value_style))
        elements.append(Spacer(1, 10*mm))
    else:
        elements.append(Paragraph('OBSERVACIONES', section_title_style))
        line_table3 = Table([['']], colWidths=[170*mm])
        line_table3.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 0.5*mm, colors.HexColor('#2563eb')),
        ]))
        elements.append(line_table3)
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph('Parto sin complicaciones.', value_style))
        elements.append(Spacer(1, 10*mm))
    
    # ===== PIE DE PÁGINA =====
    elements.append(Spacer(1, 20*mm))
    
    # Código de barras simulado
    barcode_text = f'||||| {rn.rut_provisorio or f"RN-{rn.id}"} |||||'
    elements.append(Paragraph(barcode_text, barcode_style))
    elements.append(Spacer(1, 5*mm))
    
    # Texto informativo
    info_text = 'Este brazalete debe permanecer en el recién nacido durante toda su estancia hospitalaria'
    elements.append(Paragraph(info_text, small_style))
    elements.append(Spacer(1, 3*mm))
    
    # Fecha de impresión
    fecha_impresion = datetime.now().strftime('%d-%m-%Y, %H:%M:%S')
    elements.append(Paragraph(f'Fecha de impresión: {fecha_impresion}', small_style))
    elements.append(Spacer(1, 2*mm))
    
    # Registrado por
    registrado_por = parto.usuario_registro.nombre_completo if parto.usuario_registro else 'Sistema'
    elements.append(Paragraph(f'Registrado por: {registrado_por}', small_style))
    elements.append(Spacer(1, 3*mm))
    
    # Sistema
    elements.append(Paragraph('Sistema de Trazabilidad de Partos v1.0 - Hospital Herminda Martín', 
                             ParagraphStyle('footer', parent=small_style, fontSize=7)))
    
    # Construir PDF
    doc.build(elements, onFirstPage=draw_header)
    
    # Obtener el PDF del buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf


def _calcular_edad(fecha_nacimiento):
    """Calcula la edad en años desde una fecha de nacimiento"""
    if not fecha_nacimiento:
        return 0
    
    hoy = datetime.now().date()
    edad = hoy.year - fecha_nacimiento.year
    
    # Ajustar si aún no ha cumplido años este año
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        edad -= 1
    
    return edad


def render_to_pdf(template_src, context_dict={}):
    """
    Renderiza un template HTML de Django a un objeto HttpResponse PDF
    usando xhtml2pdf.
    """
    from django.template.loader import get_template
    from xhtml2pdf import pisa
    import io
    
    template = get_template(template_src)
    html = template.render(context_dict)
    
    # Creamos un buffer de memoria para el PDF
    result = io.BytesIO()
    
    # Convertimos el HTML a PDF
    pdf = pisa.CreatePDF(
        io.BytesIO(html.encode("UTF-8")),
        dest=result,
        encoding='utf-8'
    )
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    
    print(f"Error al generar PDF: {pdf.err}")
    return None