from django.db import models


class BaseEntity(models.Model):
    """
    Clase base abstracta que proporciona campos comunes
    """
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
