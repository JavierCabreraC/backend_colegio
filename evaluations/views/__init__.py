from .profesor_views import (
    # ==========================================
    # GESTIÓN DE EXÁMENES Y TAREAS
    # ==========================================
    mis_examenes, examen_detail,
    mis_tareas, tarea_detail,
    opciones_profesor_materias, opciones_trimestres,

    # ==========================================
    # CALIFICACIÓN DE EXÁMENES
    # ==========================================
    examen_alumnos, calificar_examen, nota_examen_detail, calificar_masivo,

    # ==========================================
    # CALIFICACIÓN DE TAREAS
    # ==========================================
    tarea_entregas, calificar_tarea, nota_tarea_detail, tareas_pendientes,

    # ==========================================
    # GESTIÓN DE ASISTENCIAS
    # ==========================================
    mis_asistencias, tomar_asistencia, asistencia_clase, asistencia_detail, lista_clase,

    # ==========================================
    # GESTIÓN DE PARTICIPACIONES
    # ==========================================
    mis_participaciones, registrar_participacion, participacion_detail, participaciones_clase,

    # ==========================================
    # REPORTES Y ANÁLISIS
    # ==========================================
    estadisticas_mis_clases, reporte_grupo, reporte_alumno, reporte_materia, promedio_grupo
)

# Mantener las importaciones existentes para no romper urls.py
__all__ = [
    # ==========================================
    # GESTIÓN DE EVALUACIONES (6 funciones)
    # ==========================================
    'mis_examenes', 'examen_detail',
    'mis_tareas', 'tarea_detail',
    'opciones_profesor_materias', 'opciones_trimestres',

    # ==========================================
    # CALIFICACIONES (8 funciones)
    # ==========================================
    # Calificaciones de exámenes
    'examen_alumnos', 'calificar_examen', 'nota_examen_detail', 'calificar_masivo',
    # Calificaciones de tareas
    'tarea_entregas', 'calificar_tarea', 'nota_tarea_detail', 'tareas_pendientes',

    # ==========================================
    # ASISTENCIAS Y PARTICIPACIONES (9 funciones)
    # ==========================================
    # Gestión de asistencias
    'mis_asistencias', 'tomar_asistencia', 'asistencia_clase', 'asistencia_detail', 'lista_clase',
    # Gestión de participaciones
    'mis_participaciones', 'registrar_participacion', 'participacion_detail', 'participaciones_clase',

    # ==========================================
    # REPORTES Y ANÁLISIS (5 funciones)
    # ==========================================
    'estadisticas_mis_clases', 'reporte_grupo', 'reporte_alumno', 'reporte_materia', 'promedio_grupo'
]