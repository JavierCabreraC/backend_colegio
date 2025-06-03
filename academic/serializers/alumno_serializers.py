from ..models import Horario, Materia
from rest_framework import serializers
from authentication.models import Profesor


class ProfesorHorarioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Profesor
        fields = ['nombre_completo']

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"


class MateriaHorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = ['codigo', 'nombre', 'horas_semanales']


class HorarioAlumnoSerializer(serializers.ModelSerializer):
    materia = MateriaHorarioSerializer(source='profesor_materia.materia', read_only=True)
    profesor = ProfesorHorarioSerializer(source='profesor_materia.profesor', read_only=True)
    aula_nombre = serializers.CharField(source='aula.nombre', read_only=True)
    dia_semana_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Horario
        fields = [
            'id', 'dia_semana', 'dia_semana_nombre', 'hora_inicio',
            'hora_fin', 'materia', 'profesor', 'aula_nombre'
        ]

    def get_dia_semana_nombre(self, obj):
        dias = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes'}
        return dias.get(obj.dia_semana, '')