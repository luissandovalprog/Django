"""
Vistas JSON para el sistema de notificaciones
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from .models import Notificacion
from django.utils.timesince import timesince
import json


@login_required
@require_http_methods(["GET"])
def obtener_conteo_notificaciones(request):
    """
    Endpoint para obtener el conteo de notificaciones no leídas
    
    Returns:
        JSON: {
            "count": int,
            "success": bool
        }
    """
    try:
        count = Notificacion.objects.filter(
            receptor=request.user,
            leida=False
        ).count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def obtener_lista_notificaciones(request):
    """
    Endpoint para obtener la lista de notificaciones del usuario
    
    Query params:
        - limit: int (default: 10) - Límite de notificaciones a retornar
        - solo_no_leidas: bool (default: false)
    
    Returns:
        JSON: {
            "success": bool,
            "notificaciones": [
                {
                    "id": str,
                    "tipo": str,
                    "titulo": str,
                    "mensaje": str,
                    "link": str,
                    "leida": bool,
                    "fecha": str (tiempo relativo),
                    "fecha_iso": str
                }
            ],
            "count_total": int,
            "count_no_leidas": int
        }
    """
    try:
        # Parámetros
        limit = int(request.GET.get('limit', 10))
        solo_no_leidas = request.GET.get('solo_no_leidas', 'false').lower() == 'true'
        
        # Query base
        notificaciones_qs = Notificacion.objects.filter(receptor=request.user)
        
        if solo_no_leidas:
            notificaciones_qs = notificaciones_qs.filter(leida=False)
        
        # Conteos
        count_total = notificaciones_qs.count()
        count_no_leidas = Notificacion.objects.filter(
            receptor=request.user,
            leida=False
        ).count()
        
        # Obtener notificaciones limitadas
        notificaciones = notificaciones_qs[:limit]
        
        # Serializar
        notificaciones_data = []
        for notif in notificaciones:
            notificaciones_data.append({
                'id': str(notif.id),
                'tipo': notif.tipo,
                'titulo': notif.titulo,
                'mensaje': notif.mensaje,
                'link': notif.link or '#',
                'leida': notif.leida,
                'fecha': timesince(notif.fecha_creacion) + ' atrás',
                'fecha_iso': notif.fecha_creacion.isoformat(),
            })
        
        return JsonResponse({
            'success': True,
            'notificaciones': notificaciones_data,
            'count_total': count_total,
            'count_no_leidas': count_no_leidas
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def marcar_notificacion_leida(request):
    """
    Endpoint para marcar una notificación como leída
    
    POST body:
        {
            "notificacion_id": str
        }
    
    Returns:
        JSON: {
            "success": bool,
            "message": str
        }
    """
    try:
        data = json.loads(request.body)
        notificacion_id = data.get('notificacion_id')
        
        if not notificacion_id:
            return JsonResponse({
                'success': False,
                'error': 'ID de notificación requerido'
            }, status=400)
        
        # Obtener y marcar como leída
        notificacion = get_object_or_404(
            Notificacion,
            id=notificacion_id,
            receptor=request.user
        )
        
        notificacion.marcar_como_leida()
        
        # Obtener nuevo conteo
        nuevo_conteo = Notificacion.objects.filter(
            receptor=request.user,
            leida=False
        ).count()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída',
            'nuevo_conteo': nuevo_conteo
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def marcar_todas_leidas(request):
    """
    Endpoint para marcar todas las notificaciones como leídas
    
    Returns:
        JSON: {
            "success": bool,
            "message": str,
            "count": int
        }
    """
    try:
        from django.utils import timezone
        
        # Actualizar todas las no leídas
        count = Notificacion.objects.filter(
            receptor=request.user,
            leida=False
        ).update(
            leida=True,
            fecha_lectura=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'message': f'{count} notificaciones marcadas como leídas',
            'count': count
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)