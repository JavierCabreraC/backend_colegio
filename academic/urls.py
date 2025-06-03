from . import views
from django.urls import path

urlpatterns = [
    # CRUD de Materias
    path('materias/', views.materia_list_create, name='materia-list-create'),
    path('materias/<int:pk>/', views.materia_detail, name='materia-detail'),

    # CRUD de Aulas
    path('aulas/', views.aula_list_create, name='aula-list-create'),
    path('aulas/<int:pk>/', views.aula_detail, name='aula-detail'),

    # CRUD de Niveles y Grupos
    path('niveles/', views.nivel_list_create, name='nivel-list-create'),
    path('grupos/', views.grupo_list_create, name='grupo-list-create'),

    # Gestiones Académicas
    path('gestiones/', views.gestion_list_create, name='gestion-list-create'),
    path('gestiones/<int:pk>/', views.gestion_detail, name='gestion-detail'),
    path('gestiones/<int:pk>/activar/', views.activar_gestion, name='activar-gestion'),

    # Trimestres
    path('trimestres/', views.trimestre_list_create, name='trimestre-list-create'),
    path('trimestres/<int:pk>/', views.trimestre_detail, name='trimestre-detail'),

    # Matriculaciones
    path('matriculaciones/', views.matriculacion_list_create, name='matriculacion-list-create'),
    path('matriculaciones/<int:pk>/', views.matriculacion_detail, name='matriculacion-detail'),
    path('matriculaciones/masivo/', views.matricular_masivo, name='matricular-masivo'),

    # Horarios
    path('horarios/', views.horario_list_create, name='horario-list-create'),
    path('horarios/<int:pk>/', views.horario_detail, name='horario-detail'),
    path('horarios/vista-semanal/', views.horario_vista_semanal, name='horario-vista-semanal'),

    # Asignaciones Profesor-Materia
    path('profesor-materias/', views.profesor_materia_list_create, name='profesor-materia-list-create'),
    path('profesor-materias/<int:pk>/', views.profesor_materia_delete, name='profesor-materia-delete'),

    # Estadísticas
    path('stats/', views.academic_stats, name='academic-stats'),

    # Endpoints para profesores
    path('mis-materias/', views.mis_materias, name='mis-materias'),
    path('mis-grupos/', views.mis_grupos, name='mis-grupos'),
    path('mis-alumnos/', views.mis_alumnos, name='mis-alumnos'),
    path('mis-horarios/', views.mis_horarios, name='mis-horarios'),
    path('mi-horario/hoy/', views.mi_horario_hoy, name='mi-horario-hoy'),
    path('mi-horario/semana/', views.mi_horario_semana, name='mi-horario-semana'),

    # ==========================================
    # ENDPOINTS PARA ALUMNOS
    # ==========================================
    path('mi-horario/', views.mi_horario, name='mi-horario'),
]