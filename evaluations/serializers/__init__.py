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

from .alumno_serializers import (
    ExamenDetalleSerializer, NotaExamenSerializer, TareaDetalleSerializer, NotaTareaSerializer,
    AsistenciaSerializer, PromedioTrimestreSerializer, ResumenAsistenciaSerializer,
    ParticipacionAlumnoSerializer, EstadisticasParticipacionSerializer, DashboardRendimientoSerializer,
    RendimientoMateriaSerializer, TendenciaTrimestreSerializer, AlertaRendimientoSerializer,
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
    'ReporteAlumnoSerializer', 'ReporteMateriaSerializer', 'PromedioGrupoSerializer',
    # Alumnos
    'ExamenDetalleSerializer', 'NotaExamenSerializer', 'TareaDetalleSerializer', 'NotaTareaSerializer',
    'AsistenciaSerializer', 'PromedioTrimestreSerializer', 'ResumenAsistenciaSerializer',
    'ParticipacionAlumnoSerializer', 'EstadisticasParticipacionSerializer', 'DashboardRendimientoSerializer',
    'RendimientoMateriaSerializer', 'TendenciaTrimestreSerializer', 'AlertaRendimientoSerializer',
]