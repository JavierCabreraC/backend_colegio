from . import views
from django.urls import path

urlpatterns = [
    # Endpoints principales de predicciones ML
    path('mis-alumnos/', views.mis_alumnos_predicciones, name='mis_alumnos_predicciones'),
    path('alumno/<int:alumno_id>/materia/<str:codigo_materia>/', views.prediccion_alumno_materia,
         name='prediccion_alumno_materia'),
    path('grupo/<int:grupo_id>/riesgo/', views.analisis_riesgo_grupo, name='analisis_riesgo_grupo'),
    path('alertas/mis-clases/', views.alertas_inteligentes, name='alertas_inteligentes'),

    # Endpoint adicional para estadísticas del modelo
    path('estadisticas/', views.estadisticas_modelo, name='estadisticas_modelo'),

    # ==========================================
    # ENDPOINTS PARA ALUMNOS
    # ==========================================
    path('mis-predicciones/', views.mis_predicciones, name='alumno-mis-predicciones'),
    path('mi-prediccion/<int:materia_id>/', views.mi_prediccion_detallada, name='alumno-prediccion-detallada'),
    path('mis-recomendaciones/', views.mis_recomendaciones, name='alumno-mis-recomendaciones'),
    path('mi-resumen/', views.mi_resumen_predicciones, name='alumno-resumen-predicciones'),
    path('evolucion/<int:materia_id>/', views.evolucion_prediccion, name='alumno-evolucion-prediccion'),
]