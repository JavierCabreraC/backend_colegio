from .shared_views import academic_stats

from .director_views import (
    materia_detail, aula_list_create, aula_detail, nivel_list_create, grupo_list_create,
    gestion_list_create, gestion_detail, activar_gestion, profesor_materia_list_create,
    profesor_materia_delete, trimestre_list_create, trimestre_detail, matriculacion_list_create,
    matriculacion_detail, matricular_masivo, horario_list_create, horario_detail,
    validar_conflictos_horario, horario_vista_semanal, materia_list_create
)

from .profesor_views import (
    mis_materias, mis_grupos, mis_alumnos,
    mis_horarios, mi_horario_hoy, mi_horario_semana
)

__all__ = [
    academic_stats, materia_detail, aula_list_create, aula_detail, nivel_list_create, grupo_list_create,
    gestion_list_create, gestion_detail, activar_gestion, profesor_materia_list_create, profesor_materia_delete,
    trimestre_list_create, trimestre_detail, matriculacion_list_create, matriculacion_detail, matricular_masivo,
    horario_list_create, horario_detail, validar_conflictos_horario, horario_vista_semanal, mis_materias,
    mis_grupos, mis_alumnos, mis_horarios, mi_horario_hoy, mi_horario_semana
]
