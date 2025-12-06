# accounts/views_2fa.py
"""
Vistas para autenticación de dos factores (2FA)
Sistema TOTP con códigos de recuperación
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.util import random_hex
from auditoria.models import LogAuditoria
import qrcode
import io
import base64
from accounts.models import Usuario
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth import authenticate



def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    ip = request.META.get('HTTP_CF_CONNECTING_IP') 
    if ip:
        return ip.strip()
    ip = request.META.get('HTTP_TRUE_CLIENT_IP')
    if ip:
        return ip.strip()
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'Desconocida')


@login_required
def configurar_2fa(request):
    """Vista para configurar 2FA (primera vez)"""
    user = request.user
    
    # Verificar si ya tiene 2FA activado
    if user.require_2fa and TOTPDevice.objects.filter(user=user, confirmed=True).exists():
        messages.info(request, '2FA ya está activado en su cuenta.')
        return redirect('accounts:ver_codigos_recuperacion')
    
    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        device_id = request.POST.get('device_id')
        
        if not token or not device_id:
            messages.error(request, 'Debe ingresar el código de 6 dígitos.')
            return redirect('accounts:configurar_2fa')
        
        try:
            device = TOTPDevice.objects.get(id=device_id, user=user, confirmed=False)
            
            # Verificar el token
            if device.verify_token(token):
                # Token correcto: confirmar dispositivo
                device.confirmed = True
                device.save()
                
                # Activar 2FA en el usuario
                user.require_2fa = True
                user.save()
                
                # Generar códigos de recuperación
                static_device, _ = StaticDevice.objects.get_or_create(
                    user=user,
                    name='Códigos de Recuperación'
                )
                
                # Eliminar códigos anteriores si existen
                StaticToken.objects.filter(device=static_device).delete()
                
                # Generar 10 códigos nuevos
                codigos = []
                for _ in range(10):
                    token_obj = StaticToken.objects.create(
                        device=static_device,
                        token=random_hex(length=8)
                    )
                    codigos.append(token_obj.token)
                
                # Registrar en auditoría
                LogAuditoria.registrar(
                    usuario=user,
                    accion='ACTIVAR_2FA',
                    detalles='Autenticación de dos factores activada exitosamente',
                    ip=get_client_ip(request)
                )
                
                messages.success(request, '¡2FA activado exitosamente!')
                
                # Marcar sesión como verificada
                request.session['otp_verified'] = True
                
                # Guardar códigos en sesión para mostrar
                request.session['recovery_codes'] = codigos
                
                return redirect('accounts:codigos_recuperacion')
            else:
                # Token incorrecto
                messages.error(request, 'Código incorrecto. Verifique e intente nuevamente.')
                
                LogAuditoria.registrar(
                    usuario=user,
                    accion='2FA_CONFIGURACION_FALLIDA',
                    detalles='Código de verificación incorrecto durante configuración',
                    ip=get_client_ip(request)
                )
                
                return redirect('accounts:configurar_2fa')
                
        except TOTPDevice.DoesNotExist:
            messages.error(request, 'Dispositivo no encontrado. Intente nuevamente.')
            return redirect('accounts:configurar_2fa')
    
    # GET: Mostrar QR y formulario
    # Eliminar dispositivos no confirmados anteriores
    TOTPDevice.objects.filter(user=user, confirmed=False).delete()
    
    # Crear nuevo dispositivo TOTP
    device = TOTPDevice.objects.create(
        user=user,
        name='Autenticador',
        confirmed=False
    )
    
    # Generar URL para el QR
    otpauth_url = device.config_url
    
    # Generar QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'qr_code': img_base64,
        'secret_key': device.key,
        'device_id': device.id,
        'otpauth_url': otpauth_url
    }
    
    return render(request, 'accounts/configurar_2fa.html', context)


def verificar_2fa(request):
    """Vista para verificar código 2FA después de validar credenciales (SIN login aún)"""
    # Obtener usuario pendiente de sesión
    pending_user_id = request.session.get('pending_2fa_user_id')
    
    # Si no hay usuario pendiente, redirigir a login
    if not pending_user_id:
        # Verificar si ya está autenticado y verificado
        if request.user.is_authenticated and request.session.get('otp_verified', False):
            # Ya está logueado y verificado, redirigir según rol
            if request.user.rol and request.user.rol.nombre == 'Admin Sistema':
                return redirect('auditoria:historial_auditoria')
            else:
                return redirect('core:dashboard')
        
        messages.error(request, 'Sesión expirada. Por favor inicie sesión nuevamente.')
        return redirect('accounts:login')
    
    # Obtener objeto usuario
    try:
        user = Usuario.objects.get(id=pending_user_id)
    except Usuario.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        # Limpiar sesión
        if 'pending_2fa_user_id' in request.session:
            del request.session['pending_2fa_user_id']
        if 'pending_2fa_username' in request.session:
            del request.session['pending_2fa_username']
        return redirect('accounts:login')
    
    # Verificar que el usuario requiere 2FA
    if not user.require_2fa:
        messages.warning(request, 'Este usuario no requiere 2FA.')
        # Limpiar sesión y hacer login normal
        if 'pending_2fa_user_id' in request.session:
            del request.session['pending_2fa_user_id']
        if 'pending_2fa_username' in request.session:
            del request.session['pending_2fa_username']
        login(request, user)
        request.session['otp_verified'] = True
        return redirect('core:dashboard')
    
    # Verificar que tiene dispositivo confirmado
    devices = TOTPDevice.objects.filter(user=user, confirmed=True)
    if not devices.exists():
        messages.warning(request, 'No tiene 2FA configurado.')
        # Limpiar sesión y hacer login normal
        if 'pending_2fa_user_id' in request.session:
            del request.session['pending_2fa_user_id']
        if 'pending_2fa_username' in request.session:
            del request.session['pending_2fa_username']
        login(request, user)
        request.session['otp_verified'] = True
        return redirect('core:dashboard')
    
    
    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        codigo_recuperacion = request.POST.get('codigo_recuperacion', '').strip()
        
        # Opción 1: Verificar código TOTP
        if token:
            device = devices.first()
            if device.verify_token(token):
                # Código correcto: AHORA SÍ HACER LOGIN COMPLETO
                login(request, user)
                request.session['otp_verified'] = True
                
                # Limpiar datos temporales
                if 'pending_2fa_user_id' in request.session:
                    del request.session['pending_2fa_user_id']
                if 'pending_2fa_username' in request.session:
                    del request.session['pending_2fa_username']
                
                LogAuditoria.registrar(
                    usuario=user,
                    accion='2FA_VERIFIED',
                    detalles='Verificación 2FA exitosa con TOTP - Login completado',
                    ip=get_client_ip(request)
                )
                
                messages.success(request, f'Bienvenido, {user.nombre_completo}')
                
                # Redirigir según rol
                if user.rol and user.rol.nombre == 'Admin Sistema':
                    return redirect('auditoria:historial_auditoria')
                else:
                    return redirect('core:dashboard')
            else:
                # Código incorrecto
                LogAuditoria.registrar(
                    usuario=user,
                    accion='2FA_FAILED',
                    detalles='Código TOTP incorrecto',
                    ip=get_client_ip(request)
                )
                messages.error(request, 'Código incorrecto. Intente nuevamente.')
        
        # Opción 2: Verificar código de recuperación
        elif codigo_recuperacion:
            try:
                static_device = StaticDevice.objects.get(user=user, name='Códigos de Recuperación')
                static_token = StaticToken.objects.get(
                    device=static_device,
                    token=codigo_recuperacion
                )
                
                # Código válido: AHORA SÍ HACER LOGIN COMPLETO
                login(request, user)
                request.session['otp_verified'] = True
                
                # Limpiar datos temporales
                if 'pending_2fa_user_id' in request.session:
                    del request.session['pending_2fa_user_id']
                if 'pending_2fa_username' in request.session:
                    del request.session['pending_2fa_username']
                
                # Consumir el código
                static_token.delete()
                
                LogAuditoria.registrar(
                    usuario=user,
                    accion='2FA_RECUPERACION',
                    detalles='Verificación 2FA exitosa con código de recuperación - Login completado',
                    ip=get_client_ip(request)
                )
                
                messages.success(request, f'Bienvenido, {user.nombre_completo}')
                messages.warning(request, 'Se ha consumido un código de recuperación. Considere regenerarlos.')
                
                # Redirigir según rol
                if user.rol and user.rol.nombre == 'Admin Sistema':
                    return redirect('auditoria:historial_auditoria')
                else:
                    return redirect('core:dashboard')
                
            except (StaticDevice.DoesNotExist, StaticToken.DoesNotExist):
                LogAuditoria.registrar(
                    usuario=user,
                    accion='2FA_FAILED',
                    detalles='Código de recuperación inválido',
                    ip=get_client_ip(request)
                )
                messages.error(request, 'Código de recuperación inválido.')
        else:
            messages.error(request, 'Debe ingresar un código.')
    
    # Pasar nombre de usuario al template para mostrar
    context = {
        'username': request.session.get('pending_2fa_username', user.username)
    }
    return render(request, 'accounts/verificar_2fa.html', context)


@login_required
def desactivar_2fa(request):
    """Desactivar 2FA (requiere contraseña)"""
    user = request.user
    
    if not user.require_2fa:
        messages.info(request, '2FA no está activado en su cuenta.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        # Verificar contraseña
        if user.check_password(password):
            # Eliminar todos los dispositivos TOTP y códigos estáticos
            TOTPDevice.objects.filter(user=user).delete()
            StaticDevice.objects.filter(user=user).delete()
            
            # Desactivar 2FA
            user.require_2fa = False
            user.save()
            
            # Limpiar sesión
            if 'otp_verified' in request.session:
                del request.session['otp_verified']
            
            LogAuditoria.registrar(
                usuario=user,
                accion='DESACTIVAR_2FA',
                detalles='Autenticación de dos factores desactivada',
                ip=get_client_ip(request)
            )
            
            messages.success(request, '2FA desactivado exitosamente.')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Contraseña incorrecta.')
    
    return render(request, 'accounts/desactivar_2fa.html')


@login_required
def ver_codigos_recuperacion(request):
    """Mostrar códigos de recuperación existentes"""
    user = request.user
    
    if not user.require_2fa:
        messages.error(request, 'Primero debe activar 2FA.')
        return redirect('accounts:configurar_2fa')
    
    # Obtener códigos de la sesión (recién generados) o de la BD
    codigos_sesion = request.session.get('recovery_codes', [])
    
    if codigos_sesion:
        # Mostrar códigos recién generados
        codigos = codigos_sesion
        # Limpiar de la sesión
        del request.session['recovery_codes']
        recien_generados = True
    else:
        # Mostrar códigos existentes
        try:
            static_device = StaticDevice.objects.get(user=user, name='Códigos de Recuperación')
            codigos = list(StaticToken.objects.filter(device=static_device).values_list('token', flat=True))
            recien_generados = False
        except StaticDevice.DoesNotExist:
            codigos = []
            recien_generados = False
    
    context = {
        'codigos': codigos,
        'recien_generados': recien_generados,
        'total_codigos': len(codigos)
    }
    
    return render(request, 'accounts/codigos_recuperacion.html', context)


@login_required
def regenerar_codigos_recuperacion(request):
    """Regenerar códigos de recuperación"""
    user = request.user
    
    if not user.require_2fa:
        messages.error(request, 'Primero debe activar 2FA.')
        return redirect('accounts:configurar_2fa')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        # Verificar contraseña
        if user.check_password(password):
            # Obtener o crear dispositivo estático
            static_device, _ = StaticDevice.objects.get_or_create(
                user=user,
                name='Códigos de Recuperación'
            )
            
            # Eliminar códigos anteriores
            StaticToken.objects.filter(device=static_device).delete()
            
            # Generar 10 códigos nuevos
            codigos = []
            for _ in range(10):
                token_obj = StaticToken.objects.create(
                    device=static_device,
                    token=random_hex(length=8)
                )
                codigos.append(token_obj.token)
            
            LogAuditoria.registrar(
                usuario=user,
                accion='REGENERAR_CODIGOS_2FA',
                detalles='Códigos de recuperación regenerados',
                ip=get_client_ip(request)
            )
            
            # Guardar en sesión para mostrar
            request.session['recovery_codes'] = codigos
            
            messages.success(request, f'Bienvenido, {user.nombre_completo}')
                
            # Redirigir según rol
            if user.rol and user.rol.nombre == 'Admin Sistema':
                return redirect('auditoria:historial_auditoria')
            else:
                return redirect('core:dashboard')
        
        # Opción 2: Verificar código de recuperación
        elif codigo_recuperacion:
            try:
                static_device = StaticDevice.objects.get(user=user, name='Códigos de Recuperación')
                static_token = StaticToken.objects.get(
                    device=static_device,
                    token=codigo_recuperacion
                )
                
                # Código válido: AHORA SÍ HACER LOGIN COMPLETO
                login(request, user)
                request.session['otp_verified'] = True
                
                # Limpiar datos temporales
                if 'pending_2fa_user_id' in request.session:
                    del request.session['pending_2fa_user_id']
                if 'pending_2fa_username' in request.session:
                    del request.session['pending_2fa_username']
                
                # Consumir el código
                static_token.delete()
                
                LogAuditoria.registrar(
                    usuario=user,
                    accion='2FA_RECUPERACION',
                    detalles='Verificación 2FA exitosa con código de recuperación - Login completado',
                    ip=get_client_ip(request)
                )
                
                messages.success(request, f'Bienvenido, {user.nombre_completo}')
                messages.warning(request, 'Se ha consumido un código de recuperación. Considere regenerarlos.')
                
                # Redirigir según rol
                if user.rol and user.rol.nombre == 'Admin Sistema':
                    return redirect('auditoria:historial_auditoria')
                else:
                    return redirect('core:dashboard')
                
            except (StaticDevice.DoesNotExist, StaticToken.DoesNotExist):
                LogAuditoria.registrar(
                    usuario=user,
                    accion='2FA_FAILED',
                    detalles='Código de recuperación inválido',
                    ip=get_client_ip(request)
                )
                messages.error(request, 'Código de recuperación inválido.')
        else:
            messages.error(request, 'Debe ingresar un código.')
    
    # Pasar nombre de usuario al template para mostrar
    context = {
        'username': request.session.get('pending_2fa_username', user.username)
    }
    return render(request, 'accounts/verificar_2fa.html', context)


@login_required
def desactivar_2fa(request):
    """Desactivar 2FA (requiere contraseña)"""
    user = request.user
    
    if not user.require_2fa:
        messages.info(request, '2FA no está activado en su cuenta.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        # Verificar contraseña
        if user.check_password(password):
            # Eliminar todos los dispositivos TOTP y códigos estáticos
            TOTPDevice.objects.filter(user=user).delete()
            StaticDevice.objects.filter(user=user).delete()
            
            # Desactivar 2FA
            user.require_2fa = False
            user.save()
            
            # Limpiar sesión
            if 'otp_verified' in request.session:
                del request.session['otp_verified']
            
            LogAuditoria.registrar(
                usuario=user,
                accion='DESACTIVAR_2FA',
                detalles='Autenticación de dos factores desactivada',
                ip=get_client_ip(request)
            )
            
            messages.success(request, '2FA desactivado exitosamente.')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Contraseña incorrecta.')
    
    return render(request, 'accounts/desactivar_2fa.html')


@login_required
def ver_codigos_recuperacion(request):
    """Mostrar códigos de recuperación existentes"""
    user = request.user
    
    if not user.require_2fa:
        messages.error(request, 'Primero debe activar 2FA.')
        return redirect('accounts:configurar_2fa')
    
    # Obtener códigos de la sesión (recién generados) o de la BD
    codigos_sesion = request.session.get('recovery_codes', [])
    
    if codigos_sesion:
        # Mostrar códigos recién generados
        codigos = codigos_sesion
        # Limpiar de la sesión
        del request.session['recovery_codes']
        recien_generados = True
    else:
        # Mostrar códigos existentes
        try:
            static_device = StaticDevice.objects.get(user=user, name='Códigos de Recuperación')
            codigos = list(StaticToken.objects.filter(device=static_device).values_list('token', flat=True))
            recien_generados = False
        except StaticDevice.DoesNotExist:
            codigos = []
            recien_generados = False
    
    context = {
        'codigos': codigos,
        'recien_generados': recien_generados,
        'total_codigos': len(codigos)
    }
    
    return render(request, 'accounts/codigos_recuperacion.html', context)


@login_required
def regenerar_codigos_recuperacion(request):
    """Regenerar códigos de recuperación"""
    user = request.user
    
    if not user.require_2fa:
        messages.error(request, 'Primero debe activar 2FA.')
        return redirect('accounts:configurar_2fa')
    
    if request.method == 'POST':
        password = request.POST.get('password', '')
        
        # Verificar contraseña
        if user.check_password(password):
            # Obtener o crear dispositivo estático
            static_device, _ = StaticDevice.objects.get_or_create(
                user=user,
                name='Códigos de Recuperación'
            )
            
            # Eliminar códigos anteriores
            StaticToken.objects.filter(device=static_device).delete()
            
            # Generar 10 códigos nuevos
            codigos = []
            for _ in range(10):
                token_obj = StaticToken.objects.create(
                    device=static_device,
                    token=random_hex(length=8)
                )
                codigos.append(token_obj.token)
            
            LogAuditoria.registrar(
                usuario=user,
                accion='REGENERAR_CODIGOS_2FA',
                detalles='Códigos de recuperación regenerados',
                ip=get_client_ip(request)
            )
            
            # Guardar en sesión para mostrar
            request.session['recovery_codes'] = codigos
            
            messages.success(request, 'Códigos de recuperación regenerados exitosamente.')
            return redirect('accounts:ver_codigos_recuperacion')
        else:
            messages.error(request, 'Contraseña incorrecta.')
    
    return render(request, 'accounts/regenerar_codigos.html')


@login_required
def menu_2fa(request):
    """Menú principal de gestión 2FA"""
    user = request.user
    
    # Verificar estado actual de 2FA
    tiene_2fa_activo = user.require_2fa
    tiene_dispositivo = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
    
    # Contar códigos de recuperación disponibles
    codigos_disponibles = 0
    if tiene_2fa_activo:
        try:
            static_device = StaticDevice.objects.get(user=user, name='Códigos de Recuperación')
            codigos_disponibles = StaticToken.objects.filter(device=static_device).count()
        except StaticDevice.DoesNotExist:
            pass
    
    context = {
        'tiene_2fa_activo': tiene_2fa_activo,
        'tiene_dispositivo': tiene_dispositivo,
        'codigos_disponibles': codigos_disponibles,
    }
    
    return render(request, 'accounts/menu_2fa.html', context)