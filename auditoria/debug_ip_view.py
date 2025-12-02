# auditoria/debug_ip_view.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def debug_headers_view(request):
    """Vista temporal para ver qué headers envía Render"""
    headers_info = {
        'HTTP_X_FORWARDED_FOR': request.META.get('HTTP_X_FORWARDED_FOR', 'No existe'),
        'HTTP_X_REAL_IP': request.META.get('HTTP_X_REAL_IP', 'No existe'),
        'REMOTE_ADDR': request.META.get('REMOTE_ADDR', 'No existe'),
        'HTTP_CF_CONNECTING_IP': request.META.get('HTTP_CF_CONNECTING_IP', 'No existe'),
        'todos_los_headers_HTTP': {
            k: v for k, v in request.META.items() 
            if k.startswith('HTTP_') or k in ['REMOTE_ADDR', 'REMOTE_HOST']
        }
    }
    return JsonResponse(headers_info, json_dumps_params={'indent': 2})
