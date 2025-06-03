from rest_framework import serializers
from ..models import (NotaExamen, NotaTarea, Examen, Tarea, Asistencia, Participacion)


class ExamenDetalleSerializer(serializers.ModelSerializer):
    materia = serializers.CharField(source='profesor_materia.materia.nombre', read_only=True)
    profesor = serializers.CharField(source='profesor_materia.profesor.nombres', read_only=True)

    class Meta:
        model = Examen
        fields = [
            'id', 'titulo', 'descripcion', 'fecha_examen',
            'ponderacion', 'numero_parcial', 'materia', 'profesor'
        ]


class NotaExamenSerializer(serializers.ModelSerializer):
    examen = ExamenDetalleSerializer(read_only=True)

    class Meta:
        model = NotaExamen
        fields = [
            'id', 'nota', 'observaciones', 'fecha_registro', 'examen'
        ]


class TareaDetalleSerializer(serializers.ModelSerializer):
    materia = serializers.CharField(source='profesor_materia.materia.nombre', read_only=True)
    profesor = serializers.CharField(source='profesor_materia.profesor.nombres', read_only=True)

    class Meta:
        model = Tarea
        fields = [
            'id', 'titulo', 'descripcion', 'fecha_asignacion',
            'fecha_entrega', 'ponderacion', 'materia', 'profesor'
        ]


class NotaTareaSerializer(serializers.ModelSerializer):
    tarea = TareaDetalleSerializer(read_only=True)

    class Meta:
        model = NotaTarea
        fields = [
            'id', 'nota', 'observaciones', 'fecha_registro', 'tarea'
        ]


class AsistenciaSerializer(serializers.ModelSerializer):
    materia = serializers.CharField(source='horario.profesor_materia.materia.nombre', read_only=True)
    profesor = serializers.CharField(source='horario.profesor_materia.profesor.nombres', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    hora_clase = serializers.SerializerMethodField()

    class Meta:
        model = Asistencia
        fields = [
            'id', 'fecha', 'estado', 'estado_display',
            'materia', 'profesor', 'hora_clase'
        ]

    def get_hora_clase(self, obj):
        return f"{obj.horario.hora_inicio} - {obj.horario.hora_fin}"


class PromedioTrimestreSerializer(serializers.Serializer):
    """Serializer para promedios calculados"""
    materia = serializers.CharField()
    promedio_examenes = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    promedio_tareas = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    promedio_general = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    total_examenes = serializers.IntegerField()
    total_tareas = serializers.IntegerField()


class ResumenAsistenciaSerializer(serializers.Serializer):
    """Serializer para resumen de asistencias"""
    materia = serializers.CharField()
    total_clases = serializers.IntegerField()
    presentes = serializers.IntegerField()
    faltas = serializers.IntegerField()
    tardanzas = serializers.IntegerField()
    justificadas = serializers.IntegerField()
    porcentaje_asistencia = serializers.DecimalField(max_digits=5, decimal_places=2)


class ParticipacionAlumnoSerializer(serializers.ModelSerializer):
    materia = serializers.CharField(source='horario.profesor_materia.materia.nombre', read_only=True)
    codigo_materia = serializers.CharField(source='horario.profesor_materia.materia.codigo', read_only=True)
    profesor = serializers.CharField(source='horario.profesor_materia.profesor.nombres', read_only=True)
    profesor_apellidos = serializers.CharField(source='horario.profesor_materia.profesor.apellidos', read_only=True)
    profesor_completo = serializers.SerializerMethodField()
    hora_clase = serializers.SerializerMethodField()
    valor_texto = serializers.SerializerMethodField()

    class Meta:
        model = Participacion
        fields = [
            'id', 'fecha', 'descripcion', 'valor', 'valor_texto',
            'materia', 'codigo_materia', 'profesor', 'profesor_apellidos',
            'profesor_completo', 'hora_clase'
        ]

    def get_profesor_completo(self, obj):
        return f"{obj.horario.profesor_materia.profesor.nombres} {obj.horario.profesor_materia.profesor.apellidos}"

    def get_hora_clase(self, obj):
        return f"{obj.horario.hora_inicio} - {obj.horario.hora_fin}"

    def get_valor_texto(self, obj):
        valores = {1: 'Deficiente', 2: 'Regular', 3: 'Bueno', 4: 'Muy Bueno', 5: 'Excelente'}
        return valores.get(obj.valor, '')


class EstadisticasParticipacionSerializer(serializers.Serializer):
    """Serializer para estadísticas de participaciones por materia"""
    materia = serializers.CharField()
    codigo_materia = serializers.CharField()
    total_participaciones = serializers.IntegerField()
    promedio_valor = serializers.DecimalField(max_digits=3, decimal_places=2)
    mejor_participacion = serializers.IntegerField()
    participacion_mas_reciente = serializers.DateField()
    distribucion_valores = serializers.DictField()


class DashboardRendimientoSerializer(serializers.Serializer):
    """Serializer para el dashboard general de rendimiento"""
    resumen_general = serializers.DictField()
    rendimiento_por_materia = serializers.ListField()
    tendencias_trimestrales = serializers.ListField()
    alertas = serializers.ListField()
    comparativo_grupo = serializers.DictField()


class RendimientoMateriaSerializer(serializers.Serializer):
    """Serializer para rendimiento por materia"""
    materia = serializers.CharField()
    codigo_materia = serializers.CharField()
    promedio_notas = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    promedio_examenes = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    promedio_tareas = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    porcentaje_asistencia = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    total_participaciones = serializers.IntegerField()
    promedio_participaciones = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)
    estado = serializers.CharField()  # aprobado, en_riesgo, reprobado
    tendencia = serializers.CharField()  # positiva, estable, negativa
    color_estado = serializers.CharField()  # para frontend


class TendenciaTrimestreSerializer(serializers.Serializer):
    """Serializer para tendencias por trimestre"""
    trimestre = serializers.CharField()
    promedio_general = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    porcentaje_asistencia = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    total_participaciones = serializers.IntegerField()
    materias_aprobadas = serializers.IntegerField()
    materias_en_riesgo = serializers.IntegerField()


class AlertaRendimientoSerializer(serializers.Serializer):
    """Serializer para alertas de rendimiento"""
    tipo = serializers.CharField()  # bajo_rendimiento, baja_asistencia, sin_participacion
    materia = serializers.CharField()
    mensaje = serializers.CharField()
    nivel_criticidad = serializers.CharField()  # alta, media, baja
    sugerencias = serializers.ListField()