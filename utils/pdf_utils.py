# Django/utils/pdf_utils.py

import io
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    """
    Renderiza un template HTML de Django a un objeto HttpResponse PDF
    usando xhtml2pdf.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    
    # Creamos un buffer de memoria para el PDF
    result = io.BytesIO()
    
    # Convertimos el HTML a PDF
    # pisa.CreatePDF necesita que el HTML esté en bytes 'utf-8'
    pdf = pisa.CreatePDF(
        io.BytesIO(html.encode("UTF-8")), # El HTML a convertir
        dest=result,                       # El buffer de salida
        encoding='utf-8'
    )
    
    # Si pisa no reportó errores, devolvemos el PDF
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    
    # Si hay un error, devolvemos None (o puedes devolver un HttpResponse de error)
    print(f"Error al generar PDF: {pdf.err}")
    return None