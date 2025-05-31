from django.db import models
from shared.models import BaseEntity

class Bitacora(BaseEntity):
    usuario = models.ForeignKey('authentication.Usuario', on_delete=models.CASCADE)
    tipo_accion = models.CharField(max_length=30)
    ip = models.CharField(max_length=50)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bitacora'