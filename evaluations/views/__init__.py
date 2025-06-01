# Importar todas las vistas para mantener compatibilidad
from .profesor_views import (
    # ==========================================
    # FASE 2: GESTIÓN DE EXÁMENES Y TAREAS
    # ==========================================
    mis_examenes, examen_detail,
    mis_tareas, tarea_detail,
    opciones_profesor_materias, opciones_trimestres,

    # ==========================================
    # FASE 3: CALIFICACIÓN DE EXÁMENES
    # ==========================================
    examen_alumnos, calificar_examen, nota_examen_detail, calificar_masivo,

    # ==========================================
    # FASE 3: CALIFICACIÓN DE TAREAS
    # ==========================================
    tarea_entregas, calificar_tarea, nota_tarea_detail, tareas_pendientes,

    # ==========================================
    # FASE 4: GESTIÓN DE ASISTENCIAS
    # ==========================================
    mis_asistencias, tomar_asistencia, asistencia_clase, asistencia_detail, lista_clase,

    # ==========================================
    # FASE 4: GESTIÓN DE PARTICIPACIONES
    # ==========================================
    mis_participaciones, registrar_participacion, participacion_detail, participaciones_clase,

    # ==========================================
    # FASE 5: REPORTES Y ANÁLISIS
    # ==========================================
    estadisticas_mis_clases, reporte_grupo, reporte_alumno, reporte_materia, promedio_grupo
)

# Mantener las importaciones existentes para no romper urls.py
__all__ = [
    # ==========================================
    # FASE 2: GESTIÓN DE EVALUACIONES (6 funciones)
    # ==========================================
    'mis_examenes', 'examen_detail',
    'mis_tareas', 'tarea_detail',
    'opciones_profesor_materias', 'opciones_trimestres',

    # ==========================================
    # FASE 3: CALIFICACIONES (8 funciones)
    # ==========================================
    # Calificaciones de exámenes
    'examen_alumnos', 'calificar_examen', 'nota_examen_detail', 'calificar_masivo',
    # Calificaciones de tareas
    'tarea_entregas', 'calificar_tarea', 'nota_tarea_detail', 'tareas_pendientes',

    # ==========================================
    # FASE 4: ASISTENCIAS Y PARTICIPACIONES (9 funciones)
    # ==========================================
    # Gestión de asistencias
    'mis_asistencias', 'tomar_asistencia', 'asistencia_clase', 'asistencia_detail', 'lista_clase',
    # Gestión de participaciones
    'mis_participaciones', 'registrar_participacion', 'participacion_detail', 'participaciones_clase',

    # ==========================================
    # FASE 5: REPORTES Y ANÁLISIS (5 funciones)
    # ==========================================
    'estadisticas_mis_clases', 'reporte_grupo', 'reporte_alumno', 'reporte_materia', 'promedio_grupo'
]