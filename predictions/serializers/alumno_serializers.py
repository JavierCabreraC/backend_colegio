from rest_framework import serializers
from ..models import PrediccionRendimiento


class PrediccionAlumnoSerializer(serializers.ModelSerializer):
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)
    materia_codigo = serializers.CharField(source='materia.codigo', read_only=True)
    trimestre_nombre = serializers.CharField(source='trimestre.nombre', read_only=True)
    gestion_nombre = serializers.CharField(source='gestion.nombre', read_only=True)
    nivel_confianza = serializers.SerializerMethodField()
    estado_prediccion = serializers.SerializerMethodField()
    color_estado = serializers.SerializerMethodField()

    class Meta:
        model = PrediccionRendimiento
        fields = [
            'id', 'nota_predicha', 'confianza_prediccion', 'fecha_prediccion',
            'materia_nombre', 'materia_codigo', 'trimestre_nombre', 'gestion_nombre',
            'nivel_confianza', 'estado_prediccion', 'color_estado'
        ]

    def get_nivel_confianza(self, obj):
        """Categoriza el nivel de confianza"""
        if not obj.confianza_prediccion:
            return 'sin_datos'

        confianza = float(obj.confianza_prediccion)
        if confianza >= 85:
            return 'muy_alta'
        elif confianza >= 70:
            return 'alta'
        elif confianza >= 50:
            return 'media'
        else:
            return 'baja'

    def get_estado_prediccion(self, obj):
        """Determina el estado de la predicción basado en la nota"""
        nota = float(obj.nota_predicha)
        if nota >= 85:
            return 'excelente'
        elif nota >= 75:
            return 'muy_bueno'
        elif nota >= 65:
            return 'bueno'
        elif nota >= 51:
            return 'regular'
        else:
            return 'deficiente'

    def get_color_estado(self, obj):
        """Asigna color para el frontend según la predicción"""
        nota = float(obj.nota_predicha)
        if nota >= 80:
            return '#22c55e'  # green
        elif nota >= 70:
            return '#3b82f6'  # blue
        elif nota >= 60:
            return '#f59e0b'  # yellow
        else:
            return '#ef4444'  # red

class FactorInfluyenteSerializer(serializers.Serializer):
    """Serializer para factores que influyen en la predicción"""
    factor = serializers.CharField()
    importancia = serializers.DecimalField(max_digits=5, decimal_places=2)
    descripcion = serializers.CharField()
    tendencia = serializers.CharField()  # positiva, negativa, estable

class RecomendacionSerializer(serializers.Serializer):
    """Serializer para recomendaciones basadas en predicciones"""
    tipo = serializers.CharField()  # estudio, asistencia, participacion, examenes
    materia = serializers.CharField()
    prioridad = serializers.CharField()  # alta, media, baja
    mensaje = serializers.CharField()
    acciones_sugeridas = serializers.ListField(child=serializers.CharField())
    impacto_estimado = serializers.DecimalField(max_digits=4, decimal_places=1, help_text="Mejora estimada en puntos")

class PrediccionDetalladaSerializer(serializers.Serializer):
    """Serializer para predicción detallada con análisis completo"""
    prediccion = PrediccionAlumnoSerializer()
    factores_influyentes = serializers.ListField(child=FactorInfluyenteSerializer())
    recomendaciones = serializers.ListField(child=RecomendacionSerializer())
    comparacion_historica = serializers.DictField()
    meta_sugerida = serializers.DecimalField(max_digits=5, decimal_places=2)
    probabilidad_aprobacion = serializers.DecimalField(max_digits=5, decimal_places=2)

class ResumenPrediccionesSerializer(serializers.Serializer):
    """Serializer para resumen general de todas las predicciones"""
    total_materias = serializers.IntegerField()
    promedio_predicho = serializers.DecimalField(max_digits=5, decimal_places=2)
    materias_en_riesgo = serializers.IntegerField()
    materias_excelentes = serializers.IntegerField()
    confianza_promedio = serializers.DecimalField(max_digits=5, decimal_places=2)
    tendencia_general = serializers.CharField()
    proxima_actualizacion = serializers.DateTimeField()

class EvolucionPrediccionSerializer(serializers.Serializer):
    """Serializer para mostrar evolución de predicciones en el tiempo"""
    fecha = serializers.DateField()
    nota_predicha = serializers.DecimalField(max_digits=5, decimal_places=2)
    confianza = serializers.DecimalField(max_digits=5, decimal_places=2)
    nota_real = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)

