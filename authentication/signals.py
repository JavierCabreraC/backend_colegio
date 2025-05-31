from django.utils import timezone
from audit.models import Bitacora
from django.dispatch import receiver
from django.db.models.signals import post_save

@receiver(post_save, sender=Bitacora)
def update_last_login_on_login_action(sender, instance, created, **kwargs):
    """
    Actualiza last_login cuando se registra un LOGIN en bitácora
    """
    if created and instance.tipo_accion == 'LOGIN':
        usuario = instance.usuario
        usuario.last_login = timezone.now()
        usuario.save(update_fields=['last_login'])
