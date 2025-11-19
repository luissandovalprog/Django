"""
Señales para el sistema de notificaciones
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Correccion
from .models import Notificacion


@receiver(post_save, sender=Correccion)
def crear_notificacion_correccion(sender, instance, created, **kwargs):
    """
    Signal que se dispara cuando se crea una Corrección
    Genera automáticamente una notificación al usuario que registró el dato
    """
    if created:  # Solo cuando se crea, no cuando se actualiza
        try:
            Notificacion.crear_notificacion_correccion(instance)
        except Exception as e:
            # Log del error pero no interrumpir el flujo
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear notificación para corrección {instance.id}: {str(e)}")