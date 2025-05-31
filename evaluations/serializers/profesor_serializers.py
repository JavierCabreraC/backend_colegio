from rest_framework import serializers
from academic.models import ProfesorMateria, Trimestre
from ..models import Examen, Tarea, NotaExamen, NotaTarea


class MisExamenes_Serializer(serializers.ModelSerializer):
    """Serializer para exámenes del profesor"""
    materia_codigo = serializers.CharField(source='profesor_materia.materia.codigo', read_only=True)
    materia_nombre = serializers.CharField(source='profesor_materia.materia.nombre', read_only=True)
    trimestre_nombre = serializers.CharField(source='trimestre.nombre', read_only=True)
    gestion_anio = serializers.IntegerField(source='trimestre.gestion.anio', read_only=True)
    total_calificados = serializers.SerializerMethodField()
    total_pendientes = serializers.SerializerMethodField()

    class Meta:
        model = Examen
        fields = [
            'id', 'profesor_materia', 'trimestre',
            'materia_codigo', 'materia_nombre', 'trimestre_nombre', 'gestion_anio',
            'numero_parcial', 'titulo', 'descripcion', 'fecha_examen', 'ponderacion',
            'total_calificados', 'total_pendientes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_calificados(self, obj):
        """Contar alumnos ya calificados"""
        return NotaExamen.objects.filter(examen=obj).count()

    def get_total_pendientes(self, obj):
        """Contar alumnos pendientes de calificación"""
        from academic.models import Matriculacion, Horario

        # Obtener grupos donde se imparte este examen
        grupos_ids = Horario.objects.filter(
            profesor_materia=obj.profesor_materia,
            trimestre=obj.trimestre
        ).values_list('grupo_id', flat=True).distinct()

        # Alumnos matriculados en estos grupos
        alumnos_matriculados = Matriculacion.objects.filter(
            alumno__grupo__in=grupos_ids,
            gestion=obj.trimestre.gestion,
            activa=True
        ).count()

        return alumnos_matriculados - self.get_total_calificados(obj)


class ExamenCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar exámenes"""

    class Meta:
        model = Examen
        fields = [
            'profesor_materia', 'trimestre', 'numero_parcial',
            'titulo', 'descripcion', 'fecha_examen', 'ponderacion'
        ]

    def validate_profesor_materia(self, value):
        """Validar que el profesor_materia pertenece al usuario autenticado"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if request.user.tipo_usuario == 'profesor':
                try:
                    from authentication.models import Profesor
                    profesor = Profesor.objects.get(usuario=request.user)
                    if value.profesor != profesor:
                        raise serializers.ValidationError(
                            "Solo puedes crear exámenes para tus materias asignadas"
                        )
                except Profesor.DoesNotExist:
                    raise serializers.ValidationError("Perfil de profesor no encontrado")
        return value

    def validate(self, attrs):
        """Validaciones adicionales"""
        from datetime import date

        # Validar que la fecha del examen no sea en el pasado
        if attrs.get('fecha_examen') and attrs['fecha_examen'] < date.today():
            raise serializers.ValidationError({
                'fecha_examen': 'La fecha del examen no puede ser en el pasado'
            })

        # Validar que el trimestre pertenece a la gestión activa
        trimestre = attrs.get('trimestre')
        if trimestre and not trimestre.gestion.activa:
            raise serializers.ValidationError({
                'trimestre': 'Solo puedes crear exámenes en la gestión activa'
            })

        return attrs


class MisTareas_Serializer(serializers.ModelSerializer):
    """Serializer para tareas del profesor"""
    materia_codigo = serializers.CharField(source='profesor_materia.materia.codigo', read_only=True)
    materia_nombre = serializers.CharField(source='profesor_materia.materia.nombre', read_only=True)
    trimestre_nombre = serializers.CharField(source='trimestre.nombre', read_only=True)
    gestion_anio = serializers.IntegerField(source='trimestre.gestion.anio', read_only=True)
    total_calificados = serializers.SerializerMethodField()
    total_pendientes = serializers.SerializerMethodField()
    dias_restantes = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = [
            'id', 'profesor_materia', 'trimestre',
            'materia_codigo', 'materia_nombre', 'trimestre_nombre', 'gestion_anio',
            'titulo', 'descripcion', 'fecha_asignacion', 'fecha_entrega', 'ponderacion',
            'total_calificados', 'total_pendientes', 'dias_restantes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_calificados(self, obj):
        """Contar alumnos ya calificados"""
        return NotaTarea.objects.filter(tarea=obj).count()

    def get_total_pendientes(self, obj):
        """Contar alumnos pendientes de calificación"""
        from academic.models import Matriculacion, Horario

        # Obtener grupos donde se imparte esta tarea
        grupos_ids = Horario.objects.filter(
            profesor_materia=obj.profesor_materia,
            trimestre=obj.trimestre
        ).values_list('grupo_id', flat=True).distinct()

        # Alumnos matriculados en estos grupos
        alumnos_matriculados = Matriculacion.objects.filter(
            alumno__grupo__in=grupos_ids,
            gestion=obj.trimestre.gestion,
            activa=True
        ).count()

        return alumnos_matriculados - self.get_total_calificados(obj)

    def get_dias_restantes(self, obj):
        """Días restantes para la entrega"""
        from datetime import date
        if obj.fecha_entrega:
            delta = obj.fecha_entrega - date.today()
            return delta.days if delta.days >= 0 else 0
        return 0


class TareaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar tareas"""

    class Meta:
        model = Tarea
        fields = [
            'profesor_materia', 'trimestre', 'titulo', 'descripcion',
            'fecha_asignacion', 'fecha_entrega', 'ponderacion'
        ]

    def validate_profesor_materia(self, value):
        """Validar que el profesor_materia pertenece al usuario autenticado"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if request.user.tipo_usuario == 'profesor':
                try:
                    from authentication.models import Profesor
                    profesor = Profesor.objects.get(usuario=request.user)
                    if value.profesor != profesor:
                        raise serializers.ValidationError(
                            "Solo puedes crear tareas para tus materias asignadas"
                        )
                except Profesor.DoesNotExist:
                    raise serializers.ValidationError("Perfil de profesor no encontrado")
        return value

    def validate(self, attrs):
        """Validaciones adicionales"""
        from datetime import date

        fecha_asignacion = attrs.get('fecha_asignacion')
        fecha_entrega = attrs.get('fecha_entrega')

        # Validar que la fecha de entrega sea posterior a la asignación
        if fecha_asignacion and fecha_entrega:
            if fecha_entrega <= fecha_asignacion:
                raise serializers.ValidationError({
                    'fecha_entrega': 'La fecha de entrega debe ser posterior a la fecha de asignación'
                })

        # Validar que las fechas no sean en el pasado (para creación)
        if not self.instance:  # Solo para creación
            if fecha_asignacion and fecha_asignacion < date.today():
                raise serializers.ValidationError({
                    'fecha_asignacion': 'La fecha de asignación no puede ser en el pasado'
                })

        # Validar que el trimestre pertenece a la gestión activa
        trimestre = attrs.get('trimestre')
        if trimestre and not trimestre.gestion.activa:
            raise serializers.ValidationError({
                'trimestre': 'Solo puedes crear tareas en la gestión activa'
            })

        return attrs


# Serializers auxiliares para referencias rápidas
class ProfesorMateriaSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para profesor-materia"""
    materia_codigo = serializers.CharField(source='materia.codigo', read_only=True)
    materia_nombre = serializers.CharField(source='materia.nombre', read_only=True)

    class Meta:
        model = ProfesorMateria
        fields = ['id', 'materia_codigo', 'materia_nombre']


class TrimestreSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para trimestres"""
    gestion_anio = serializers.IntegerField(source='gestion.anio', read_only=True)

    class Meta:
        model = Trimestre
        fields = ['id', 'numero', 'nombre', 'gestion_anio']