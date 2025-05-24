from rest_framework import serializers
from .models import (
    Nivel, Grupo, Materia, Aula, ProfesorMateria,
    Gestion, Trimestre
)


class NivelSerializer(serializers.ModelSerializer):
    """Serializer para niveles académicos"""
    total_grupos = serializers.SerializerMethodField()
    total_alumnos = serializers.SerializerMethodField()

    class Meta:
        model = Nivel
        fields = [
            'id', 'numero', 'nombre', 'descripcion',
            'total_grupos', 'total_alumnos',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_grupos(self, obj):
        return obj.grupo_set.count()

    def get_total_alumnos(self, obj):
        from authentication.models import Alumno
        return Alumno.objects.filter(grupo__nivel=obj).count()


class GrupoSerializer(serializers.ModelSerializer):
    """Serializer para grupos"""
    nivel_nombre = serializers.CharField(source='nivel.nombre', read_only=True)
    nivel_numero = serializers.IntegerField(source='nivel.numero', read_only=True)
    total_alumnos = serializers.SerializerMethodField()
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Grupo
        fields = [
            'id', 'nivel', 'nivel_nombre', 'nivel_numero',
            'letra', 'capacidad_maxima', 'total_alumnos', 'nombre_completo',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_alumnos(self, obj):
        return obj.alumno_set.count()

    def get_nombre_completo(self, obj):
        return f"{obj.nivel.numero}° {obj.letra}"


class MateriaSerializer(serializers.ModelSerializer):
    """Serializer para materias"""
    total_profesores = serializers.SerializerMethodField()
    profesores_asignados = serializers.SerializerMethodField()

    class Meta:
        model = Materia
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'horas_semanales',
            'total_profesores', 'profesores_asignados',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_profesores(self, obj):
        return obj.profesormateria_set.count()

    def get_profesores_asignados(self, obj):
        profesores = []
        for pm in obj.profesormateria_set.select_related('profesor').all():
            profesores.append({
                'id': pm.profesor.usuario.id,
                'nombre': f"{pm.profesor.nombres} {pm.profesor.apellidos}",
                'email': pm.profesor.usuario.email
            })
        return profesores


class MateriaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de materias"""
    total_profesores = serializers.SerializerMethodField()

    class Meta:
        model = Materia
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'horas_semanales', 'total_profesores'
        ]

    def get_total_profesores(self, obj):
        return obj.profesormateria_set.count()


class AulaSerializer(serializers.ModelSerializer):
    """Serializer para aulas"""
    ocupacion_actual = serializers.SerializerMethodField()
    horarios_count = serializers.SerializerMethodField()

    class Meta:
        model = Aula
        fields = [
            'id', 'nombre', 'capacidad', 'descripcion',
            'ocupacion_actual', 'horarios_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_ocupacion_actual(self, obj):
        # Porcentaje de uso del aula (basado en horarios asignados)
        from datetime import datetime
        total_slots = 5 * 6  # 5 días x 6 horas aprox por día
        horarios_usados = obj.horario_set.count()
        return round((horarios_usados / total_slots) * 100, 2) if total_slots > 0 else 0

    def get_horarios_count(self, obj):
        return obj.horario_set.count()


class AulaListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de aulas"""
    horarios_count = serializers.SerializerMethodField()

    class Meta:
        model = Aula
        fields = ['id', 'nombre', 'capacidad', 'horarios_count']

    def get_horarios_count(self, obj):
        return obj.horario_set.count()


# Serializers adicionales para referencias
class ProfesorMateriaSerializer(serializers.ModelSerializer):
    """Serializer para asignaciones profesor-materia"""
    profesor_nombre = serializers.CharField(
        source='profesor.nombres', read_only=True
    )
    profesor_apellidos = serializers.CharField(
        source='profesor.apellidos', read_only=True
    )
    materia_nombre = serializers.CharField(
        source='materia.nombre', read_only=True
    )
    materia_codigo = serializers.CharField(
        source='materia.codigo', read_only=True
    )

    class Meta:
        model = ProfesorMateria
        fields = [
            'id', 'profesor', 'materia',
            'profesor_nombre', 'profesor_apellidos',
            'materia_nombre', 'materia_codigo',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GestionSerializer(serializers.ModelSerializer):
    """Serializer para gestiones académicas"""
    total_trimestres = serializers.SerializerMethodField()
    total_matriculaciones = serializers.SerializerMethodField()

    class Meta:
        model = Gestion
        fields = [
            'id', 'anio', 'nombre', 'fecha_inicio', 'fecha_fin',
            'activa', 'total_trimestres', 'total_matriculaciones',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_trimestres(self, obj):
        return obj.trimestre_set.count()

    def get_total_matriculaciones(self, obj):
        return obj.matriculacion_set.count()


class TrimestreSerializer(serializers.ModelSerializer):
    """Serializer para trimestres"""
    gestion_nombre = serializers.CharField(source='gestion.nombre', read_only=True)
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)

    class Meta:
        model = Trimestre
        fields = [
            'id', 'gestion', 'gestion_nombre', 'gestion_anio',
            'numero', 'nombre', 'fecha_inicio', 'fecha_fin',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
