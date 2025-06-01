# Importar todos los serializers para mantener compatibilidad
from .profesor_serializers import (
    # Evaluaciones básicas
    MisExamenes_Serializer, ExamenCreateUpdateSerializer,
    MisTareas_Serializer, TareaCreateUpdateSerializer,
    ProfesorMateriaSimpleSerializer, TrimestreSimpleSerializer,
    # Calificaciones
    AlumnoParaCalificarSerializer, NotaExamenSerializer, CalificarExamenSerializer,
    CalificarMasivoSerializer, NotaTareaSerializer, CalificarTareaSerializer,
    TareasPendientesSerializer,
    # Asistencias
    AsistenciaSerializer, TomarAsistenciaSerializer, ListaClaseSerializer,
    MisAsistenciasSerializer,
    # Participaciones
    ParticipacionSerializer, RegistrarParticipacionSerializer,
    ParticipacionesClaseSerializer, MisParticipacionesSerializer,
    # Reportes
    EstadisticasClaseSerializer, ReporteGrupoSerializer, RendimientoAlumnoSerializer,
    ReporteAlumnoSerializer, ReporteMateriaSerializer, PromedioGrupoSerializer
)

__all__ = [
    # Evaluaciones básicas
    'MisExamenes_Serializer', 'ExamenCreateUpdateSerializer',
    'MisTareas_Serializer', 'TareaCreateUpdateSerializer',
    'ProfesorMateriaSimpleSerializer', 'TrimestreSimpleSerializer',
    # Calificaciones
    'AlumnoParaCalificarSerializer', 'NotaExamenSerializer', 'CalificarExamenSerializer',
    'CalificarMasivoSerializer', 'NotaTareaSerializer', 'CalificarTareaSerializer',
    'TareasPendientesSerializer',
    # Asistencias
    'AsistenciaSerializer', 'TomarAsistenciaSerializer', 'ListaClaseSerializer',
    'MisAsistenciasSerializer',
    # Participaciones
    'ParticipacionSerializer', 'RegistrarParticipacionSerializer',
    'ParticipacionesClaseSerializer', 'MisParticipacionesSerializer',
    # Reportes
    'EstadisticasClaseSerializer', 'ReporteGrupoSerializer', 'RendimientoAlumnoSerializer',
    'ReporteAlumnoSerializer', 'ReporteMateriaSerializer', 'PromedioGrupoSerializer'
]