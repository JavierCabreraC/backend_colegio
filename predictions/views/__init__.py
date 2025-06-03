from .profesor_views import (
    mis_alumnos_predicciones, prediccion_alumno_materia,
    analisis_riesgo_grupo, alertas_inteligentes, estadisticas_modelo
)

from .alumno_views import (
    mis_predicciones, mi_prediccion_detallada, mis_recomendaciones,
    mi_resumen_predicciones, evolucion_prediccion
)

__all__ = [
    # Profesor views
    'mis_alumnos_predicciones', 'prediccion_alumno_materia',
    'analisis_riesgo_grupo', 'alertas_inteligentes', 'estadisticas_modelo',
    # Alumno views
    'mis_predicciones', 'mi_prediccion_detallada', 'mis_recomendaciones',
    'mi_resumen_predicciones', 'evolucion_prediccion'
]