"""
Modelos de Auditoría
Sistema de logs cifrados
"""

from django.db import models
from django.conf import settings
import uuid
from utils.crypto import crypto_service


class LogAuditoria(models.Model):
    """
    Modelo de Log de Auditoría con detalles cifrados
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='logs_auditoria'
    )
    accion = models.CharField(max_length=255)
    tabla_afectada = models.CharField(max_length=100, null=True, blank=True)
    registro_id_uuid = models.UUIDField(null=True, blank=True)
    
    # Detalles cifrados (pueden contener información sensible)
    detalles_encrypted = models.TextField(null=True, blank=True, db_column='detalles')
    
    ip_usuario = models.CharField(max_length=45, null=True, blank=True)
    fecha_accion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'LogAuditoria'
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-fecha_accion']
    
    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.fecha_accion.strftime('%d/%m/%Y %H:%M')}"
    
    def set_detalles(self, detalles):
        """Establece los detalles cifrados"""
        if detalles:
            self.detalles_encrypted = crypto_service.encrypt(str(detalles))
    
    def get_detalles(self):
        """Obtiene los detalles descifrados"""
        if self.detalles_encrypted:
            return crypto_service.decrypt(self.detalles_encrypted)
        return None
    
    @classmethod
    def registrar(cls, usuario, accion, tabla_afectada=None, registro_id=None, detalles=None, ip=None):
        """
        Método de clase para registrar una acción de auditoría
        
        Args:
            usuario: Usuario que realiza la acción
            accion: Descripción de la acción
            tabla_afectada: Tabla de la base de datos afectada
            registro_id: ID del registro afectado
            detalles: Detalles adicionales (serán cifrados)
            ip: Dirección IP del usuario
        
        Returns:
            LogAuditoria: Instancia del log creado
        """
        log = cls(
            usuario=usuario,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id_uuid=registro_id,
            ip_usuario=ip
        )
        log.set_detalles(detalles)
        log.save()
        return log
