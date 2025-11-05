"""
Middleware de Auditoría
Registra automáticamente las acciones importantes de los usuarios
"""

from .models import LogAuditoria


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class AuditLogMiddleware:
    """
    Middleware para logging automático de acciones
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Registrar solo acciones importantes
        if request.user.is_authenticated:
            path = request.path
            method = request.method
            
            # Lista de rutas que queremos auditar
            audit_paths = [
                '/madre/',
                '/parto/',
                '/recien-nacido/',
                '/reportes/',
            ]
            
            # Solo auditar modificaciones (POST, PUT, DELETE)
            if method in ['POST', 'PUT', 'DELETE'] and any(audit_path in path for audit_path in audit_paths):
                LogAuditoria.registrar(
                    usuario=request.user,
                    accion=f"{method} {path}",
                    detalles=f"Status: {response.status_code}",
                    ip=get_client_ip(request)
                )
        
        return response
