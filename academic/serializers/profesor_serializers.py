from rest_framework import serializers
from authentication.models import Alumno
from ..models import (
    Nivel, Grupo, Materia, Aula, ProfesorMateria,
    Gestion, Trimestre, Matriculacion, Horario
)


class MisMaterias_Serializer(serializers.ModelSerializer):
    """Serializer para materias del profesor"""
    codigo = serializers.CharField(source='materia.codigo', read_only=True)
    nombre = serializers.CharField(source='materia.nombre', read_only=True)
    descripcion = serializers.CharField(source='materia.descripcion', read_only=True)
    horas_semanales = serializers.IntegerField(source='materia.horas_semanales', read_only=True)
    total_grupos = serializers.SerializerMethodField()
    total_alumnos = serializers.SerializerMethodField()

    class Meta:
        model = ProfesorMateria
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'horas_semanales',
            'total_grupos', 'total_alumnos', 'created_at'
        ]

    def get_total_grupos(self, obj):
        """Contar grupos donde enseña esta materia"""
        return Horario.objects.filter(
            profesor_materia=obj
        ).values('grupo').distinct().count()

    def get_total_alumnos(self, obj):
        """Contar alumnos que toma esta materia con este profesor"""
        from authentication.models import Alumno
        grupos_ids = Horario.objects.filter(
            profesor_materia=obj
        ).values_list('grupo_id', flat=True).distinct()

        return Alumno.objects.filter(grupo__in=grupos_ids).count()


class MisGrupos_Serializer(serializers.ModelSerializer):
    """Serializer para grupos del profesor"""
    nivel_numero = serializers.IntegerField(source='nivel.numero', read_only=True)
    nivel_nombre = serializers.CharField(source='nivel.nombre', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    total_alumnos = serializers.SerializerMethodField()
    materias_imparto = serializers.SerializerMethodField()

    class Meta:
        model = Grupo
        fields = [
            'id', 'nivel_numero', 'nivel_nombre', 'letra',
            'nombre_completo', 'capacidad_maxima', 'total_alumnos', 'materias_imparto'
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.nivel.numero}° {obj.letra}"

    def get_total_alumnos(self, obj):
        return obj.alumno_set.count()

    def get_materias_imparto(self, obj):
        """Materias que imparte en este grupo"""
        profesor = self.context.get('profesor')
        if not profesor:
            return []

        horarios = Horario.objects.filter(
            grupo=obj,
            profesor_materia__profesor=profesor
        ).select_related('profesor_materia__materia')

        return [
            {
                'id': h.profesor_materia.materia.id,
                'codigo': h.profesor_materia.materia.codigo,
                'nombre': h.profesor_materia.materia.nombre
            }
            for h in horarios
        ]


class MisHorarios_Serializer(serializers.ModelSerializer):
    """Serializer para horarios del profesor"""
    materia_codigo = serializers.CharField(source='profesor_materia.materia.codigo', read_only=True)
    materia_nombre = serializers.CharField(source='profesor_materia.materia.nombre', read_only=True)
    grupo_nombre = serializers.SerializerMethodField()
    aula_nombre = serializers.CharField(source='aula.nombre', read_only=True)
    trimestre_nombre = serializers.CharField(source='trimestre.nombre', read_only=True)
    gestion_anio = serializers.IntegerField(source='trimestre.gestion.anio', read_only=True)
    dia_semana_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Horario
        fields = [
            'id', 'materia_codigo', 'materia_nombre', 'grupo_nombre',
            'aula_nombre', 'trimestre_nombre', 'gestion_anio',
            'dia_semana', 'dia_semana_nombre', 'hora_inicio', 'hora_fin'
        ]

    def get_grupo_nombre(self, obj):
        return f"{obj.grupo.nivel.numero}° {obj.grupo.letra}"

    def get_dia_semana_nombre(self, obj):
        dias = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes'}
        return dias.get(obj.dia_semana, 'N/A')


class MisAlumnos_Serializer(serializers.ModelSerializer):
    """Serializer para alumnos del profesor"""
    email = serializers.CharField(source='usuario.email', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    grupo_nombre = serializers.SerializerMethodField()
    activo = serializers.BooleanField(source='usuario.activo', read_only=True)
    edad = serializers.SerializerMethodField()

    class Meta:
        model = Alumno
        fields = [
            'usuario', 'email', 'nombre_completo', 'matricula',
            'grupo', 'grupo_nombre', 'telefono', 'activo', 'edad'
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"

    def get_grupo_nombre(self, obj):
        return f"{obj.grupo.nivel.numero}° {obj.grupo.letra}"

    def get_edad(self, obj):
        from datetime import date
        if obj.fecha_nacimiento:
            today = date.today()
            return today.year - obj.fecha_nacimiento.year - (
                    (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
            )
        return None