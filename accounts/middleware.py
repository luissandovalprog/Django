# accounts/middleware.py
"""
Middleware para forzar verificación 2FA
"""

from django.shortcuts import redirect
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

class Require2FAMiddleware:
    """
    Middleware que fuerza la verificación 2FA antes de permitir acceso
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rutas exentas de verificación 2FA
        self.exempt_paths = [
            '/accounts/login/',
            '/accounts/logout/',
            '/accounts/2fa/verificar/',
            '/accounts/2fa/configurar/',
            '/accounts/2fa/codigos/',
            '/accounts/2fa/regenerar/',
            '/static/',
            '/media/',
            '/admin/',  # Admin de Django
        ]
    
    def __call__(self, request):
        # Si el usuario está autenticado
        if request.user.is_authenticated:
            user = request.user
            
            # Verificar si requiere 2FA
            if user.require_2fa:
                # Verificar si tiene dispositivo TOTP confirmado
                devices = TOTPDevice.objects.filter(user=user, confirmed=True)
                
                if devices.exists():
                    # Verificar si la sesión está verificada con 2FA
                    otp_verified = request.session.get('otp_verified', False)
                    
                    if not otp_verified:
                        # Verificar si la ruta está exenta
                        path = request.path
                        is_exempt = any(path.startswith(exempt) for exempt in self.exempt_paths)
                        
                        if not is_exempt:
                            # Redirigir a verificación 2FA
                            return redirect('accounts:verificar_2fa')
        
        response = self.get_response(request)
        return response