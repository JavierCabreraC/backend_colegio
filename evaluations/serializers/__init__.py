# Importar todos los serializers para mantener compatibilidad
from .profesor_serializers import (
    MisExamenes_Serializer, ExamenCreateUpdateSerializer,
    MisTareas_Serializer, TareaCreateUpdateSerializer,
    ProfesorMateriaSimpleSerializer, TrimestreSimpleSerializer
)

# Mantener las importaciones existentes para no romper código
__all__ = [
    'MisExamenes_Serializer', 'ExamenCreateUpdateSerializer',
    'MisTareas_Serializer', 'TareaCreateUpdateSerializer',
    'ProfesorMateriaSimpleSerializer', 'TrimestreSimpleSerializer'
]
