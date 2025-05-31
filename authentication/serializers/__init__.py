# Importar todos los serializers para mantener compatibilidad
from .shared_serializers import (
    LoginSerializer, UsuarioSerializer, CustomTokenObtainPairSerializer
)

from .director_serializers import (
    ProfesorSerializer, ProfesorListSerializer,
    AlumnoSerializer, AlumnoListSerializer,
    DirectorSerializer
)

from .profesor_serializers import DashboardProfesorSerializer

# Mantener las importaciones existentes para no romper código
__all__ = [
    'LoginSerializer', 'UsuarioSerializer', 'CustomTokenObtainPairSerializer',
    'ProfesorSerializer', 'ProfesorListSerializer',
    'AlumnoSerializer', 'AlumnoListSerializer', 'DirectorSerializer',
    'DashboardProfesorSerializer'
]