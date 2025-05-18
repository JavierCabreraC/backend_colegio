from django.db import models
from shared.models import BaseEntity



class Examen(BaseEntity):
    profesor_materia = models.ForeignKey('academic.ProfesorMateria', on_delete=models.CASCADE)
    trimestre = models.ForeignKey('academic.Trimestre', on_delete=models.CASCADE)
    numero_parcial = models.IntegerField()
    titulo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=100, blank=True)
    fecha_examen = models.DateField()
    ponderacion = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        db_table = 'examenes'
        constraints = [
            models.CheckConstraint(
                check=models.Q(numero_parcial__gte=1) & models.Q(numero_parcial__lte=3),
                name='check_numero_parcial'
            ),
            models.CheckConstraint(
                check=models.Q(ponderacion__gt=0),
                name='check_ponderacion_positiva'
            )
        ]


class NotaExamen(BaseEntity):
    matriculacion = models.ForeignKey('academic.Matriculacion', on_delete=models.CASCADE)
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    nota = models.DecimalField(max_digits=5, decimal_places=2)
    observaciones = models.CharField(max_length=100, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notas_examenes'
        unique_together = ['matriculacion', 'examen']
        constraints = [
            models.CheckConstraint(
                check=models.Q(nota__gte=0) & models.Q(nota__lte=100),
                name='check_nota_examen_rango'
            )
        ]


class Tarea(BaseEntity):
    profesor_materia = models.ForeignKey('academic.ProfesorMateria', on_delete=models.CASCADE)
    trimestre = models.ForeignKey('academic.Trimestre', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=50, blank=True)
    fecha_asignacion = models.DateField()
    fecha_entrega = models.DateField()
    ponderacion = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        db_table = 'tareas'
        constraints = [
            models.CheckConstraint(
                check=models.Q(fecha_entrega__gte=models.F('fecha_asignacion')),
                name='check_fecha_entrega_valida'
            ),
            models.CheckConstraint(
                check=models.Q(ponderacion__gt=0),
                name='check_ponderacion_tarea_positiva'
            )
        ]


class NotaTarea(BaseEntity):
    matriculacion = models.ForeignKey('academic.Matriculacion', on_delete=models.CASCADE)
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE)
    nota = models.DecimalField(max_digits=5, decimal_places=2)
    observaciones = models.CharField(max_length=50, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notas_tareas'
        unique_together = ['matriculacion', 'tarea']
        constraints = [
            models.CheckConstraint(
                check=models.Q(nota__gte=0) & models.Q(nota__lte=100),
                name='check_nota_tarea_rango'
            )
        ]


class EstadoAsistencia(models.TextChoices):
    PRESENTE = 'P', 'Presente'
    FALTA = 'F', 'Falta'
    TARDANZA = 'T', 'Tardanza'
    JUSTIFICADA = 'J', 'Justificada'


class Asistencia(BaseEntity):
    matriculacion = models.ForeignKey('academic.Matriculacion', on_delete=models.CASCADE)
    horario = models.ForeignKey('academic.Horario', on_delete=models.CASCADE)
    fecha = models.DateField()
    estado = models.CharField(
        max_length=1,
        choices=EstadoAsistencia.choices
    )
    
    class Meta:
        db_table = 'asistencias'
        unique_together = ['matriculacion', 'horario', 'fecha']


class Participacion(BaseEntity):
    matriculacion = models.ForeignKey('academic.Matriculacion', on_delete=models.CASCADE)
    horario = models.ForeignKey('academic.Horario', on_delete=models.CASCADE)
    fecha = models.DateField()
    descripcion = models.CharField(max_length=50)
    valor = models.IntegerField()
    
    class Meta:
        db_table = 'participaciones'
        constraints = [
            models.CheckConstraint(
                check=models.Q(valor__gte=1) & models.Q(valor__lte=5),
                name='check_valor_participacion'
            )
        ]


class EstadoMateria(models.TextChoices):
    APROBADO = 'aprobado', 'Aprobado'
    REPROBADO = 'reprobado', 'Reprobado'
    EN_RECUPERACION = 'en_recuperacion', 'En Recuperación'


class HistoricoTrimestral(BaseEntity):
    alumno = models.ForeignKey('authentication.Alumno', on_delete=models.CASCADE)
    trimestre = models.ForeignKey('academic.Trimestre', on_delete=models.CASCADE)
    materia = models.ForeignKey('academic.Materia', on_delete=models.CASCADE)
    promedio_trimestre = models.DecimalField(max_digits=5, decimal_places=2)
    promedio_examenes = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promedio_tareas = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    porcentaje_asistencia = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    num_participaciones = models.IntegerField(default=0)
    observaciones = models.CharField(max_length=50, blank=True)
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'historico_trimestral'
        unique_together = ['alumno', 'trimestre', 'materia']


class HistoricoAnual(BaseEntity):
    alumno = models.ForeignKey('authentication.Alumno', on_delete=models.CASCADE)
    gestion = models.ForeignKey('academic.Gestion', on_delete=models.CASCADE)
    materia = models.ForeignKey('academic.Materia', on_delete=models.CASCADE)
    promedio_anual = models.DecimalField(max_digits=5, decimal_places=2)
    promedio_t1 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promedio_t2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    promedio_t3 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    porcentaje_asistencia_anual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_participaciones = models.IntegerField(default=0)
    estado_materia = models.CharField(
        max_length=20,
        choices=EstadoMateria.choices
    )
    observaciones = models.CharField(max_length=50, blank=True)
    fecha_calculo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'historico_anual'
        unique_together = ['alumno', 'gestion', 'materia']
