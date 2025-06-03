from .shared_views import academic_stats

from .director_views import (
    # CRUD Materias
    materia_list_create, materia_detail,
    # CRUD Aulas
    aula_list_create, aula_detail,
    # CRUD Niveles y Grupos
    nivel_list_create, grupo_list_create,
    # Gestiones Académicas
    gestion_list_create, gestion_detail, activar_gestion,
    # Trimestres
    trimestre_list_create, trimestre_detail,
    # Matriculaciones
    matriculacion_list_create, matriculacion_detail, matricular_masivo,
    # Horarios
    horario_list_create, horario_detail, horario_vista_semanal,
    # Asignaciones Profesor-Materia
    profesor_materia_list_create, profesor_materia_delete
)

from .profesor_views import (
    mis_materias, mis_grupos, mis_alumnos,
    mis_horarios, mi_horario_hoy, mi_horario_semana
)

from .alumno_views import ( mi_horario )

__all__ = [
    # Shared
    'academic_stats',
    # Director views
    'materia_list_create', 'materia_detail',
    'aula_list_create', 'aula_detail',
    'nivel_list_create', 'grupo_list_create',
    'gestion_list_create', 'gestion_detail', 'activar_gestion',
    'trimestre_list_create', 'trimestre_detail',
    'matriculacion_list_create', 'matriculacion_detail', 'matricular_masivo',
    'horario_list_create', 'horario_detail', 'horario_vista_semanal',
    'profesor_materia_list_create', 'profesor_materia_delete',
    # Profesor views
    'mis_materias', 'mis_grupos', 'mis_alumnos',
    'mis_horarios', 'mi_horario_hoy', 'mi_horario_semana',
    # Alumnos
    'mi_horario'
]