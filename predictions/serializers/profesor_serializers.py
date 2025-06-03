from rest_framework import serializers
from ..models import PrediccionRendimiento


class PrediccionRendimientoSerializer(serializers.ModelSerializer):
    """Serializer para predicciones de rendimiento"""
    alumno_info = serializers.SerializerMethodField()
    materia_info = serializers.SerializerMethodField()
    nivel_riesgo = serializers.SerializerMethodField()
    factores_clave = serializers.SerializerMethodField()

    class Meta:
        model = PrediccionRendimiento
        fields = [
            'id', 'alumno_info', 'materia_info', 'nota_predicha',
            'confianza_prediccion', 'nivel_riesgo', 'factores_clave',
            'fecha_prediccion', 'metadata'
        ]

    def get_alumno_info(self, obj):
        return {
            'id': obj.alumno.usuario.id,
            'matricula': obj.alumno.matricula,
            'nombre_completo': f"{obj.alumno.nombres} {obj.alumno.apellidos}",
            'grupo': f"{obj.alumno.grupo.nivel.numero}° {obj.alumno.grupo.letra}"
        }

    def get_materia_info(self, obj):
        return {
            'id': obj.materia.id,
            'codigo': obj.materia.codigo,
            'nombre': obj.materia.nombre
        }

    def get_nivel_riesgo(self, obj):
        if obj.nota_predicha < 50:
            return 'alto'
        elif obj.nota_predicha < 70:
            return 'medio'
        else:
            return 'bajo'

    def get_factores_clave(self, obj):
        # Extraer factores del metadata si están disponibles
        if obj.metadata and 'factores_importantes' in obj.metadata:
            return obj.metadata['factores_importantes']
        return []

class MisAlumnosPrediccionSerializer(serializers.Serializer):
    """Serializer para vista general de predicciones de todos los alumnos"""
    alumno_id = serializers.IntegerField()
    matricula = serializers.CharField()
    nombre_completo = serializers.CharField()
    grupo_nombre = serializers.CharField()
    total_materias = serializers.IntegerField()
    promedio_predicciones = serializers.DecimalField(max_digits=5, decimal_places=2)
    nivel_riesgo_general = serializers.CharField()
    materias_riesgo_alto = serializers.IntegerField()
    ultima_actualizacion = serializers.DateTimeField()

class PrediccionAlumnoMateriaSerializer(serializers.Serializer):
    """Serializer para predicción específica alumno-materia"""
    alumno_info = serializers.DictField()
    materia_info = serializers.DictField()
    prediccion_actual = serializers.DictField()
    historial_rendimiento = serializers.ListField()
    recomendaciones = serializers.ListField()
    comparacion_grupo = serializers.DictField()

class AnalisisRiesgoGrupoSerializer(serializers.Serializer):
    """Serializer para análisis de riesgo grupal"""
    grupo_info = serializers.DictField()
    estadisticas_riesgo = serializers.DictField()
    alumnos_alto_riesgo = serializers.ListField()
    alumnos_medio_riesgo = serializers.ListField()
    alumnos_bajo_riesgo = serializers.ListField()
    tendencias_grupo = serializers.DictField()
    recomendaciones_generales = serializers.ListField()

class AlertaInteligentSerializer(serializers.Serializer):
    """Serializer para sistema de alertas inteligentes"""
    id = serializers.CharField()
    tipo_alerta = serializers.CharField()  # 'rendimiento_bajo', 'ausencias', 'tendencia_negativa'
    prioridad = serializers.CharField()  # 'alta', 'media', 'baja'
    alumno_info = serializers.DictField()
    materia_info = serializers.DictField()
    descripcion = serializers.CharField()
    metricas_relevantes = serializers.DictField()
    acciones_sugeridas = serializers.ListField()
    fecha_deteccion = serializers.DateTimeField()
    dias_desde_deteccion = serializers.IntegerField()

class EstadisticasMLSerializer(serializers.Serializer):
    """Serializer para estadísticas del modelo ML"""
    modelo_info = serializers.DictField()
    precision_metricas = serializers.DictField()
    total_predicciones = serializers.IntegerField()
    distribucion_riesgo = serializers.DictField()
    factores_mas_importantes = serializers.ListField()
    ultima_actualizacion = serializers.DateTimeField()
