"""
Modelos del sistema de notificaciones
"""

from django.db import models
from django.conf import settings
import uuid


class Notificacion(models.Model):
    """
    Modelo para gestionar notificaciones a usuarios
    """
    TIPO_CHOICES = [
        ('correccion', 'Corrección Anexada'),
        ('parto', 'Nuevo Parto'),
        ('sistema', 'Notificación del Sistema'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Usuario receptor
    receptor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones_recibidas'
    )
    
    # Contenido
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='sistema')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    link = models.CharField(max_length=500, blank=True, null=True)
    
    # Estado
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'Notificacion'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['receptor', 'leida']),
            models.Index(fields=['-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Notificación para {self.receptor.nombre_completo} - {self.titulo}"
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            from django.utils import timezone
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save(update_fields=['leida', 'fecha_lectura'])
    
    @staticmethod
    def crear_notificacion_correccion(correccion):
        """
        Crea una notificación cuando se anexa una corrección
        
        Args:
            correccion: Instancia del modelo Correccion
        """
        from django.urls import reverse
        
        # Obtener el objeto relacionado (Parto, Madre, RecienNacido)
        objeto_corregido = correccion.content_object
        
        # Determinar el usuario_registro según el tipo de objeto
        usuario_destino = None
        link = None
        nombre_objeto = correccion.content_type.model
        
        if nombre_objeto == 'parto':
            usuario_destino = objeto_corregido.usuario_registro
            link = reverse('core:parto_detail', kwargs={'pk': objeto_corregido.pk})
            descripcion = f"Parto del {objeto_corregido.fecha_parto.strftime('%d/%m/%Y')}"
        
        elif nombre_objeto == 'madre':
            # Para Madre, verificar si tiene campo usuario_registro
            if hasattr(objeto_corregido, 'usuario_registro') and objeto_corregido.usuario_registro:
                usuario_destino = objeto_corregido.usuario_registro
            else:
                # Fallback: buscar el último parto asociado
                ultimo_parto = objeto_corregido.partos.order_by('-fecha_parto').first()
                if ultimo_parto:
                    usuario_destino = ultimo_parto.usuario_registro
            
            link = reverse('core:madre_detail', kwargs={'pk': objeto_corregido.pk})
            descripcion = f"Ficha: {objeto_corregido.ficha_clinica_numero or 'S/N'}"
        
        elif nombre_objeto == 'reciennacido':
            usuario_destino = objeto_corregido.usuario_registro
            link = reverse('core:parto_detail', kwargs={'pk': objeto_corregido.parto.pk})
            descripcion = f"Recién Nacido - Parto del {objeto_corregido.parto.fecha_parto.strftime('%d/%m/%Y')}"
        
        # Solo crear notificación si hay un usuario destino
        if usuario_destino:
            titulo = f"Corrección anexada en {nombre_objeto.title()}"
            mensaje = (
                f"El Dr(a). {correccion.usuario.nombre_completo} ha anexado una corrección "
                f"al campo '{correccion.campo_corregido}' en {descripcion}. "
                f"Justificación: {correccion.justificacion[:100]}..."
            )
            
            Notificacion.objects.create(
                receptor=usuario_destino,
                tipo='correccion',
                titulo=titulo,
                mensaje=mensaje,
                link=link
            )
            
            return True
        
        return False