from .director_serializers import (
    NivelSerializer, GrupoSerializer, MateriaSerializer, MateriaListSerializer,
    AulaSerializer, AulaListSerializer, ProfesorMateriaSerializer,
    GestionSerializer, TrimestreSerializer, MatriculacionSerializer, HorarioSerializer
)

from .profesor_serializers import (
    MisMaterias_Serializer ,MisGrupos_Serializer ,MisHorarios_Serializer ,MisAlumnos_Serializer
)

from .alumno_serializers import (
    HorarioAlumnoSerializer, ProfesorHorarioSerializer, MateriaHorarioSerializer
)

__all__ = [
    # Shared/Director serializers
    'NivelSerializer', 'GrupoSerializer', 'MateriaSerializer', 'MateriaListSerializer',
    'AulaSerializer', 'AulaListSerializer', 'ProfesorMateriaSerializer',
    'GestionSerializer', 'TrimestreSerializer', 'MatriculacionSerializer', 'HorarioSerializer',
    # Profesor serializers
    'MisMaterias_Serializer', 'MisGrupos_Serializer', 'MisAlumnos_Serializer', 'MisHorarios_Serializer',
    # Alumnos
    'HorarioAlumnoSerializer', 'ProfesorHorarioSerializer', 'MateriaHorarioSerializer'
]