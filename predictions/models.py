from django.db import models
from shared.models import BaseEntity


class PrediccionRendimiento(BaseEntity):
    alumno = models.ForeignKey('authentication.Alumno', on_delete=models.CASCADE)
    gestion = models.ForeignKey('academic.Gestion', on_delete=models.CASCADE)
    trimestre = models.ForeignKey('academic.Trimestre', on_delete=models.CASCADE, null=True, blank=True)
    materia = models.ForeignKey('academic.Materia', on_delete=models.CASCADE)
    nota_predicha = models.DecimalField(max_digits=5, decimal_places=2)
    confianza_prediccion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    features_utilizados = models.JSONField(null=True, blank=True)  # JSONB en PostgreSQL
    fecha_prediccion = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True)  # JSON para parámetros adicionales
    
    class Meta:
        db_table = 'predicciones_rendimiento'
