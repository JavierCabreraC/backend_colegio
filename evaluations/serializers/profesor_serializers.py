from rest_framework import serializers
from academic.models import ProfesorMateria, Trimestre, Horario
from ..models import Examen, Tarea, NotaExamen, NotaTarea, Participacion, Asistencia


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


# ==========================================
# SERIALIZERS PARA CALIFICACIONES
# ==========================================

class AlumnoParaCalificarSerializer(serializers.Serializer):
    """Serializer para mostrar alumnos disponibles para calificar"""
    id_matriculacion = serializers.IntegerField()
    alumno_id = serializers.IntegerField()
    matricula = serializers.CharField()
    nombre_completo = serializers.CharField()
    grupo_nombre = serializers.CharField()
    email = serializers.EmailField()
    ya_calificado = serializers.BooleanField()
    nota_actual = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    fecha_calificacion = serializers.DateTimeField(allow_null=True)


class NotaExamenSerializer(serializers.ModelSerializer):
    """Serializer para notas de exámenes"""
    alumno_matricula = serializers.CharField(source='matriculacion.alumno.matricula', read_only=True)
    alumno_nombre = serializers.SerializerMethodField()
    examen_titulo = serializers.CharField(source='examen.titulo', read_only=True)

    class Meta:
        model = NotaExamen
        fields = [
            'id', 'matriculacion', 'examen',
            'alumno_matricula', 'alumno_nombre', 'examen_titulo',
            'nota', 'observaciones', 'fecha_registro',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'fecha_registro', 'created_at', 'updated_at']

    def get_alumno_nombre(self, obj):
        return f"{obj.matriculacion.alumno.nombres} {obj.matriculacion.alumno.apellidos}"

    def validate_nota(self, value):
        """Validar rango de nota"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("La nota debe estar entre 0 y 100")
        return value

    def validate(self, attrs):
        """Validaciones adicionales"""
        # Validar que la matriculación pertenece al examen correcto
        matriculacion = attrs.get('matriculacion')
        examen = attrs.get('examen')

        if matriculacion and examen:
            # Verificar que el alumno está en un grupo que recibe esta materia
            from academic.models import Horario

            tiene_clase = Horario.objects.filter(
                profesor_materia=examen.profesor_materia,
                grupo=matriculacion.alumno.grupo,
                trimestre=examen.trimestre
            ).exists()

            if not tiene_clase:
                raise serializers.ValidationError(
                    "El alumno no está en un grupo que recibe esta materia en este trimestre"
                )

        return attrs


class CalificarExamenSerializer(serializers.Serializer):
    """Serializer para calificar un examen"""
    matriculacion_id = serializers.IntegerField()
    examen_id = serializers.IntegerField()
    nota = serializers.DecimalField(max_digits=5, decimal_places=2)
    observaciones = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_nota(self, value):
        """Validar rango de nota"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("La nota debe estar entre 0 y 100")
        return value

    def validate(self, attrs):
        """Validar que el examen y matriculación existen y son compatibles"""
        try:
            from academic.models import Matriculacion
            matriculacion = Matriculacion.objects.get(id=attrs['matriculacion_id'])
            examen = Examen.objects.get(id=attrs['examen_id'])
        except (Matriculacion.DoesNotExist, Examen.DoesNotExist):
            raise serializers.ValidationError("Matriculación o examen no encontrado")

        # Verificar que el alumno tiene clase con este profesor en esta materia
        from academic.models import Horario
        tiene_clase = Horario.objects.filter(
            profesor_materia=examen.profesor_materia,
            grupo=matriculacion.alumno.grupo,
            trimestre=examen.trimestre
        ).exists()

        if not tiene_clase:
            raise serializers.ValidationError(
                "El alumno no está inscrito en esta materia para este trimestre"
            )

        attrs['matriculacion'] = matriculacion
        attrs['examen'] = examen
        return attrs


class CalificarMasivoSerializer(serializers.Serializer):
    """Serializer para calificación masiva"""
    examen_id = serializers.IntegerField()
    calificaciones = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        min_length=1
    )

    def validate_calificaciones(self, value):
        """Validar estructura de calificaciones masivas"""
        for calificacion in value:
            # Verificar campos requeridos
            if 'matriculacion_id' not in calificacion or 'nota' not in calificacion:
                raise serializers.ValidationError(
                    "Cada calificación debe tener 'matriculacion_id' y 'nota'"
                )

            # Validar que la nota es numérica y en rango
            try:
                nota = float(calificacion['nota'])
                if nota < 0 or nota > 100:
                    raise serializers.ValidationError(
                        f"La nota {nota} está fuera del rango 0-100"
                    )
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"La nota '{calificacion['nota']}' no es un número válido"
                )

        return value


class NotaTareaSerializer(serializers.ModelSerializer):
    """Serializer para notas de tareas"""
    alumno_matricula = serializers.CharField(source='matriculacion.alumno.matricula', read_only=True)
    alumno_nombre = serializers.SerializerMethodField()
    tarea_titulo = serializers.CharField(source='tarea.titulo', read_only=True)

    class Meta:
        model = NotaTarea
        fields = [
            'id', 'matriculacion', 'tarea',
            'alumno_matricula', 'alumno_nombre', 'tarea_titulo',
            'nota', 'observaciones', 'fecha_registro',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'fecha_registro', 'created_at', 'updated_at']

    def get_alumno_nombre(self, obj):
        return f"{obj.matriculacion.alumno.nombres} {obj.matriculacion.alumno.apellidos}"

    def validate_nota(self, value):
        """Validar rango de nota"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("La nota debe estar entre 0 y 100")
        return value


class CalificarTareaSerializer(serializers.Serializer):
    """Serializer para calificar una tarea"""
    matriculacion_id = serializers.IntegerField()
    tarea_id = serializers.IntegerField()
    nota = serializers.DecimalField(max_digits=5, decimal_places=2)
    observaciones = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_nota(self, value):
        """Validar rango de nota"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("La nota debe estar entre 0 y 100")
        return value

    def validate(self, attrs):
        """Validar que la tarea y matriculación existen y son compatibles"""
        try:
            from academic.models import Matriculacion
            matriculacion = Matriculacion.objects.get(id=attrs['matriculacion_id'])
            tarea = Tarea.objects.get(id=attrs['tarea_id'])
        except (Matriculacion.DoesNotExist, Tarea.DoesNotExist):
            raise serializers.ValidationError("Matriculación o tarea no encontrada")

        # Verificar que el alumno tiene clase con este profesor en esta materia
        from academic.models import Horario
        tiene_clase = Horario.objects.filter(
            profesor_materia=tarea.profesor_materia,
            grupo=matriculacion.alumno.grupo,
            trimestre=tarea.trimestre
        ).exists()

        if not tiene_clase:
            raise serializers.ValidationError(
                "El alumno no está inscrito en esta materia para este trimestre"
            )

        attrs['matriculacion'] = matriculacion
        attrs['tarea'] = tarea
        return attrs


class TareasPendientesSerializer(serializers.ModelSerializer):
    """Serializer para tareas pendientes de calificación"""
    materia_nombre = serializers.CharField(source='profesor_materia.materia.nombre', read_only=True)
    total_entregas = serializers.SerializerMethodField()
    pendientes_calificar = serializers.SerializerMethodField()
    dias_vencimiento = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = [
            'id', 'titulo', 'materia_nombre', 'fecha_entrega',
            'total_entregas', 'pendientes_calificar', 'dias_vencimiento'
        ]

    def get_total_entregas(self, obj):
        """Total de alumnos que deben entregar"""
        from academic.models import Horario, Matriculacion

        grupos_ids = Horario.objects.filter(
            profesor_materia=obj.profesor_materia,
            trimestre=obj.trimestre
        ).values_list('grupo_id', flat=True).distinct()

        return Matriculacion.objects.filter(
            alumno__grupo__in=grupos_ids,
            gestion=obj.trimestre.gestion,
            activa=True
        ).count()

    def get_pendientes_calificar(self, obj):
        """Entregas pendientes de calificar"""
        calificadas = NotaTarea.objects.filter(tarea=obj).count()
        return self.get_total_entregas(obj) - calificadas

    def get_dias_vencimiento(self, obj):
        """Días desde el vencimiento (negativo = vencida)"""
        from datetime import date
        if obj.fecha_entrega:
            delta = date.today() - obj.fecha_entrega
            return -delta.days  # Negativo si ya venció
        return 0


# ==========================================
# SERIALIZERS PARA ASISTENCIAS
# ==========================================

class AsistenciaSerializer(serializers.ModelSerializer):
    """Serializer para asistencias"""
    alumno_matricula = serializers.CharField(source='matriculacion.alumno.matricula', read_only=True)
    alumno_nombre = serializers.SerializerMethodField()
    grupo_nombre = serializers.SerializerMethodField()
    materia_nombre = serializers.CharField(source='horario.profesor_materia.materia.nombre', read_only=True)
    estado_display = serializers.SerializerMethodField()

    class Meta:
        model = Asistencia
        fields = [
            'id', 'matriculacion', 'horario', 'fecha', 'estado',
            'alumno_matricula', 'alumno_nombre', 'grupo_nombre',
            'materia_nombre', 'estado_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_alumno_nombre(self, obj):
        return f"{obj.matriculacion.alumno.nombres} {obj.matriculacion.alumno.apellidos}"

    def get_grupo_nombre(self, obj):
        grupo = obj.matriculacion.alumno.grupo
        return f"{grupo.nivel.numero}° {grupo.letra}"

    def get_estado_display(self, obj):
        estados = {
            'P': 'Presente',
            'F': 'Falta',
            'T': 'Tardanza',
            'J': 'Justificada'
        }
        return estados.get(obj.estado, obj.estado)


class TomarAsistenciaSerializer(serializers.Serializer):
    """Serializer para tomar asistencia de una clase"""
    horario_id = serializers.IntegerField()
    fecha = serializers.DateField()
    asistencias = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        ),
        min_length=1
    )

    def validate_horario_id(self, value):
        """Validar que el horario existe y pertenece al profesor"""
        try:
            from academic.models import Horario
            horario = Horario.objects.get(id=value)
        except Horario.DoesNotExist:
            raise serializers.ValidationError("Horario no encontrado")

        # Verificar permisos del profesor
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if request.user.tipo_usuario == 'profesor':
                try:
                    from authentication.models import Profesor
                    profesor = Profesor.objects.get(usuario=request.user)
                    if horario.profesor_materia.profesor != profesor:
                        raise serializers.ValidationError(
                            "No tienes permisos para tomar asistencia en este horario"
                        )
                except Profesor.DoesNotExist:
                    raise serializers.ValidationError("Perfil de profesor no encontrado")

        return value

    def validate_fecha(self, value):
        """Validar que la fecha no sea futura"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("No puedes tomar asistencia de fechas futuras")
        return value

    def validate_asistencias(self, value):
        """Validar estructura de asistencias"""
        estados_validos = ['P', 'F', 'T', 'J']

        for asistencia in value:
            # Verificar campos requeridos
            if 'matriculacion_id' not in asistencia or 'estado' not in asistencia:
                raise serializers.ValidationError(
                    "Cada asistencia debe tener 'matriculacion_id' y 'estado'"
                )

            # Validar estado
            if asistencia['estado'] not in estados_validos:
                raise serializers.ValidationError(
                    f"Estado '{asistencia['estado']}' no válido. Debe ser: {', '.join(estados_validos)}"
                )

        return value


class ListaClaseSerializer(serializers.Serializer):
    """Serializer para lista de alumnos de una clase"""
    id_matriculacion = serializers.IntegerField()
    alumno_id = serializers.IntegerField()
    matricula = serializers.CharField()
    nombre_completo = serializers.CharField()
    grupo_nombre = serializers.CharField()
    foto_url = serializers.CharField(allow_null=True)
    asistencia_actual = serializers.DictField(allow_null=True)


class MisAsistenciasSerializer(serializers.ModelSerializer):
    """Serializer para historial de asistencias del profesor"""
    materia_nombre = serializers.CharField(source='horario.profesor_materia.materia.nombre', read_only=True)
    grupo_nombre = serializers.SerializerMethodField()
    total_alumnos = serializers.SerializerMethodField()
    presentes = serializers.SerializerMethodField()
    faltas = serializers.SerializerMethodField()
    tardanzas = serializers.SerializerMethodField()
    justificadas = serializers.SerializerMethodField()

    class Meta:
        model = Horario
        fields = [
            'id', 'fecha', 'materia_nombre', 'grupo_nombre',
            'total_alumnos', 'presentes', 'faltas', 'tardanzas', 'justificadas'
        ]

    def get_grupo_nombre(self, obj):
        return f"{obj.grupo.nivel.numero}° {obj.grupo.letra}"

    def get_total_alumnos(self, obj):
        # Se calcula en la vista
        return getattr(obj, 'total_alumnos', 0)

    def get_presentes(self, obj):
        return getattr(obj, 'presentes', 0)

    def get_faltas(self, obj):
        return getattr(obj, 'faltas', 0)

    def get_tardanzas(self, obj):
        return getattr(obj, 'tardanzas', 0)

    def get_justificadas(self, obj):
        return getattr(obj, 'justificadas', 0)


# ==========================================
# SERIALIZERS PARA PARTICIPACIONES
# ==========================================

class ParticipacionSerializer(serializers.ModelSerializer):
    """Serializer para participaciones"""
    alumno_matricula = serializers.CharField(source='matriculacion.alumno.matricula', read_only=True)
    alumno_nombre = serializers.SerializerMethodField()
    grupo_nombre = serializers.SerializerMethodField()
    materia_nombre = serializers.CharField(source='horario.profesor_materia.materia.nombre', read_only=True)

    class Meta:
        model = Participacion
        fields = [
            'id', 'matriculacion', 'horario', 'fecha', 'descripcion', 'valor',
            'alumno_matricula', 'alumno_nombre', 'grupo_nombre', 'materia_nombre',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_alumno_nombre(self, obj):
        return f"{obj.matriculacion.alumno.nombres} {obj.matriculacion.alumno.apellidos}"

    def get_grupo_nombre(self, obj):
        grupo = obj.matriculacion.alumno.grupo
        return f"{grupo.nivel.numero}° {grupo.letra}"

    def validate_valor(self, value):
        """Validar rango de valor de participación"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("El valor de participación debe estar entre 1 y 5")
        return value


class RegistrarParticipacionSerializer(serializers.Serializer):
    """Serializer para registrar participación"""
    matriculacion_id = serializers.IntegerField()
    horario_id = serializers.IntegerField()
    fecha = serializers.DateField()
    descripcion = serializers.CharField(max_length=50)
    valor = serializers.IntegerField()

    def validate_valor(self, value):
        """Validar rango de valor"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("El valor debe estar entre 1 y 5")
        return value

    def validate_fecha(self, value):
        """Validar que la fecha no sea futura"""
        from datetime import date
        if value > date.today():
            raise serializers.ValidationError("No puedes registrar participaciones de fechas futuras")
        return value

    def validate(self, attrs):
        """Validaciones adicionales"""
        try:
            from academic.models import Matriculacion, Horario
            matriculacion = Matriculacion.objects.get(id=attrs['matriculacion_id'])
            horario = Horario.objects.get(id=attrs['horario_id'])
        except (Matriculacion.DoesNotExist, Horario.DoesNotExist):
            raise serializers.ValidationError("Matriculación o horario no encontrado")

        # Verificar que el alumno está en el grupo correcto
        if matriculacion.alumno.grupo != horario.grupo:
            raise serializers.ValidationError(
                "El alumno no pertenece al grupo de este horario"
            )

        # Verificar permisos del profesor
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if request.user.tipo_usuario == 'profesor':
                try:
                    from authentication.models import Profesor
                    profesor = Profesor.objects.get(usuario=request.user)
                    if horario.profesor_materia.profesor != profesor:
                        raise serializers.ValidationError(
                            "No tienes permisos para registrar participaciones en este horario"
                        )
                except Profesor.DoesNotExist:
                    raise serializers.ValidationError("Perfil de profesor no encontrado")

        attrs['matriculacion'] = matriculacion
        attrs['horario'] = horario
        return attrs


class ParticipacionesClaseSerializer(serializers.Serializer):
    """Serializer para participaciones de una clase específica"""
    horario_id = serializers.IntegerField()
    fecha = serializers.DateField()
    materia_nombre = serializers.CharField()
    grupo_nombre = serializers.CharField()
    total_participaciones = serializers.IntegerField()
    participaciones = ParticipacionSerializer(many=True)


class MisParticipacionesSerializer(serializers.ModelSerializer):
    """Serializer para historial de participaciones del profesor"""
    materia_nombre = serializers.CharField(source='horario.profesor_materia.materia.nombre', read_only=True)
    grupo_nombre = serializers.SerializerMethodField()
    total_participaciones = serializers.IntegerField()
    promedio_valor = serializers.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        model = Horario
        fields = [
            'id', 'fecha', 'materia_nombre', 'grupo_nombre',
            'total_participaciones', 'promedio_valor'
        ]

    def get_grupo_nombre(self, obj):
        return f"{obj.grupo.nivel.numero}° {obj.grupo.letra}"

# ==========================================
# SERIALIZERS PARA REPORTES
# ==========================================

class EstadisticasClaseSerializer(serializers.Serializer):
    """Serializer para estadísticas de clases del profesor"""
    total_examenes = serializers.IntegerField()
    total_tareas = serializers.IntegerField()
    total_asistencias_tomadas = serializers.IntegerField()
    total_participaciones = serializers.IntegerField()
    promedio_examenes = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    promedio_tareas = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    porcentaje_asistencia_promedio = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    participacion_promedio = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)

class ReporteGrupoSerializer(serializers.Serializer):
    """Serializer para reporte de rendimiento de un grupo"""
    grupo_info = serializers.DictField()
    estadisticas_generales = serializers.DictField()
    alumnos_rendimiento = serializers.ListField()
    materias_impartidas = serializers.ListField()

class RendimientoAlumnoSerializer(serializers.Serializer):
    """Serializer para rendimiento individual de un alumno"""
    id_alumno = serializers.IntegerField()
    matricula = serializers.CharField()
    nombre_completo = serializers.CharField()
    promedio_examenes = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    promedio_tareas = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    porcentaje_asistencia = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    total_participaciones = serializers.IntegerField()
    promedio_participaciones = serializers.DecimalField(max_digits=3, decimal_places=2, allow_null=True)

class ReporteAlumnoSerializer(serializers.Serializer):
    """Serializer para reporte completo de un alumno"""
    alumno_info = serializers.DictField()
    materias_profesor = serializers.ListField()
    resumen_rendimiento = serializers.DictField()

class ReporteMateriaSerializer(serializers.Serializer):
    """Serializer para reporte de rendimiento por materia"""
    materia_info = serializers.DictField()
    grupos_atendidos = serializers.ListField()
    estadisticas_generales = serializers.DictField()
    distribucion_notas = serializers.DictField()

class PromedioGrupoSerializer(serializers.Serializer):
    """Serializer para promedios de un grupo en una materia"""
    grupo_info = serializers.DictField()
    materia_info = serializers.DictField()
    estadisticas = serializers.DictField()
    alumnos_detalle = serializers.ListField()