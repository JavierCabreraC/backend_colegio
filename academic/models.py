from django.db import models
from shared.models import BaseEntity


class Nivel(BaseEntity):
    numero = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'niveles'
        constraints = [
            models.CheckConstraint(
                check=models.Q(numero__gte=1) & models.Q(numero__lte=6),
                name='check_nivel_numero'
            )
        ]


class Grupo(BaseEntity):
    nivel = models.ForeignKey(Nivel, on_delete=models.CASCADE)
    letra = models.CharField(max_length=1)
    capacidad_maxima = models.IntegerField(default=40)
    
    class Meta:
        db_table = 'grupos'
        unique_together = ['nivel', 'letra']
        constraints = [
            models.CheckConstraint(
                check=models.Q(letra__in=['A', 'B']),
                name='check_grupo_letra'
            )
        ]


class Aula(BaseEntity):
    nombre = models.CharField(max_length=20, unique=True)
    capacidad = models.IntegerField()
    descripcion = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'aulas'


class Materia(BaseEntity):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=40, blank=True)
    horas_semanales = models.IntegerField()
    
    class Meta:
        db_table = 'materias'


class ProfesorMateria(BaseEntity):
    profesor = models.ForeignKey('authentication.Profesor', on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'profesor_materia'
        unique_together = ['profesor', 'materia']


class Gestion(BaseEntity):
    anio = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=40)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activa = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'gestiones'


class Trimestre(BaseEntity):
    gestion = models.ForeignKey(Gestion, on_delete=models.CASCADE)
    numero = models.IntegerField()
    nombre = models.CharField(max_length=50)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    class Meta:
        db_table = 'trimestres'
        unique_together = ['gestion', 'numero']
        constraints = [
            models.CheckConstraint(
                check=models.Q(numero__gte=1) & models.Q(numero__lte=3),
                name='check_trimestre_numero'
            )
        ]


class Horario(BaseEntity):
    profesor_materia = models.ForeignKey(ProfesorMateria, on_delete=models.CASCADE)
    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE)
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE)
    trimestre = models.ForeignKey(Trimestre, on_delete=models.CASCADE)
    dia_semana = models.IntegerField()  # 1=Lunes, 5=Viernes
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    class Meta:
        db_table = 'horarios'
        constraints = [
            models.CheckConstraint(
                check=models.Q(dia_semana__gte=1) & models.Q(dia_semana__lte=5),
                name='check_dia_semana'
            ),
            models.CheckConstraint(
                check=models.Q(hora_inicio__gte='07:15:00') & models.Q(hora_inicio__lt='13:00:00'),
                name='check_hora_inicio'
            ),
            models.CheckConstraint(
                check=models.Q(hora_fin__gt='07:15:00') & models.Q(hora_fin__lte='13:00:00'),
                name='check_hora_fin'
            )
        ]


class Matriculacion(BaseEntity):
    alumno = models.ForeignKey('authentication.Alumno', on_delete=models.CASCADE)
    gestion = models.ForeignKey(Gestion, on_delete=models.CASCADE)
    fecha_matriculacion = models.DateField()
    activa = models.BooleanField(default=True)
    observaciones = models.CharField(max_length=50, blank=True)
    
    class Meta:
        db_table = 'matriculaciones'
        unique_together = ['alumno', 'gestion']
