# Importar todas las vistas para mantener compatibilidad
from .shared_views import login_view, logout_view, user_activity

from .director_views import (
    profesor_list_create, profesor_detail,
    alumno_list_create, alumno_detail,
    dashboard_director
)

from .profesor_views import dashboard_profesor

# Mantener las importaciones existentes para no romper urls.py
__all__ = [
    'login_view', 'logout_view', 'user_activity',
    'profesor_list_create', 'profesor_detail',
    'alumno_list_create', 'alumno_detail',
    'dashboard_director', 'dashboard_profesor'
]