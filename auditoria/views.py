# En auditoria/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .models import LogAuditoria
from django.db.models import Q

def es_admin_sistema(user):
    return user.is_authenticated and user.puede_gestionar_usuarios

@user_passes_test(es_admin_sistema)
def log_auditoria_list(request):
    # Lógica de filtrado de React
    busqueda_query = request.GET.get('busqueda', '')
    filtro_accion = request.GET.get('accion', 'todas')
    filtro_usuario = request.GET.get('usuario', 'todos')

    logs = LogAuditoria.objects.select_related('usuario').all()

    if busqueda_query:
        # Nota: 'detalles_encrypted' no se puede buscar directamente si está cifrado.
        # Se debe buscar por campos no cifrados.
        logs = logs.filter(
            Q(usuario__username__icontains=busqueda_query) |
            Q(accion__icontains=busqueda_query) |
            Q(ip_usuario__icontains=busqueda_query)
        )

    if filtro_accion != 'todas':
        logs = logs.filter(accion=filtro_accion)

    if filtro_usuario != 'todos':
        logs = logs.filter(usuario__username=filtro_usuario)

    context = {
        'logs': logs[:200], # Limitar a los últimos 200
        'usuarios_unicos': LogAuditoria.objects.values_list('usuario__username', flat=True).distinct(),
        'acciones_unicas': LogAuditoria.objects.values_list('accion', flat=True).distinct(),
    }
    return render(request, 'auditoria/log_list.html', context)