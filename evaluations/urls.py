from . import views
from django.urls import path

urlpatterns = [
    # ==========================================
    # GESTIÓN DE EXÁMENES
    # ==========================================
    path('mis-examenes/', views.mis_examenes, name='mis-examenes'),
    path('mis-examenes/<int:pk>/', views.examen_detail, name='examen-detail'),

    # ==========================================
    # GESTIÓN DE TAREAS
    # ==========================================
    path('mis-tareas/', views.mis_tareas, name='mis-tareas'),
    path('mis-tareas/<int:pk>/', views.tarea_detail, name='tarea-detail'),

    # ==========================================
    # CALIFICACIÓN DE EXÁMENES
    # ==========================================
    path('examen/<int:examen_id>/alumnos/', views.examen_alumnos, name='examen-alumnos'),
    path('calificar-examen/', views.calificar_examen, name='calificar-examen'),
    path('nota-examen/<int:pk>/', views.nota_examen_detail, name='nota-examen-detail'),
    path('calificar-masivo/', views.calificar_masivo, name='calificar-masivo'),

    # ==========================================
    # CALIFICACIÓN DE TAREAS
    # ==========================================
    path('tarea/<int:tarea_id>/entregas/', views.tarea_entregas, name='tarea-entregas'),
    path('calificar-tarea/', views.calificar_tarea, name='calificar-tarea'),
    path('nota-tarea/<int:pk>/', views.nota_tarea_detail, name='nota-tarea-detail'),
    path('tareas-pendientes/', views.tareas_pendientes, name='tareas-pendientes'),

    # ==========================================
    # GESTIÓN DE ASISTENCIAS
    # ==========================================
    path('mis-asistencias/', views.mis_asistencias, name='mis-asistencias'),
    path('tomar-asistencia/', views.tomar_asistencia, name='tomar-asistencia'),
    path('asistencia/clase/<int:horario_id>/', views.asistencia_clase, name='asistencia-clase'),
    path('asistencia/<int:pk>/', views.asistencia_detail, name='asistencia-detail'),
    path('lista-clase/', views.lista_clase, name='lista-clase'),

    # ==========================================
    # GESTIÓN DE PARTICIPACIONES
    # ==========================================
    path('mis-participaciones/', views.mis_participaciones, name='mis-participaciones'),
    path('registrar-participacion/', views.registrar_participacion, name='registrar-participacion'),
    path('participacion/<int:pk>/', views.participacion_detail, name='participacion-detail'),
    path('participaciones/clase/', views.participaciones_clase, name='participaciones-clase'),

    # ==========================================
    # REPORTES Y ANÁLISIS
    # ==========================================
    path('estadisticas/mis-clases/', views.estadisticas_mis_clases, name='estadisticas-mis-clases'),
    path('reporte/grupo/<int:grupo_id>/', views.reporte_grupo, name='reporte-grupo'),
    path('reporte/alumno/<int:alumno_id>/', views.reporte_alumno, name='reporte-alumno'),
    path('reporte/materia/<int:materia_id>/', views.reporte_materia, name='reporte-materia'),
    path('promedio/grupo/<int:grupo_id>/', views.promedio_grupo, name='promedio-grupo'),

    # ==========================================
    # ENDPOINTS AUXILIARES
    # ==========================================
    path('opciones/profesor-materias/', views.opciones_profesor_materias, name='opciones-profesor-materias'),
    path('opciones/trimestres/', views.opciones_trimestres, name='opciones-trimestres'),
]