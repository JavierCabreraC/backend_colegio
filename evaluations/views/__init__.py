# Importar todas las vistas para mantener compatibilidad
from .profesor_views import (
    mis_examenes, examen_detail,
    mis_tareas, tarea_detail,
    opciones_profesor_materias, opciones_trimestres
)

# Mantener las importaciones existentes para no romper urls.py
__all__ = [
    'mis_examenes', 'examen_detail',
    'mis_tareas', 'tarea_detail',
    'opciones_profesor_materias', 'opciones_trimestres'
]