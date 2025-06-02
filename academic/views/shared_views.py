from django.db.models import Count
from shared.permissions import IsDirector
from rest_framework.response import Response
from ..models import Materia, Aula, Nivel, Grupo
from ..serializers import ( MateriaListSerializer )
from rest_framework.decorators import api_view, permission_classes


# Vista de estadísticas académicas
@api_view(['GET'])
@permission_classes([IsDirector])
def academic_stats(request):
    """Estadísticas académicas para dashboard"""
    stats = {
        'total_materias': Materia.objects.count(),
        'total_aulas': Aula.objects.count(),
        'total_niveles': Nivel.objects.count(),
        'total_grupos': Grupo.objects.count(),
        'materias_sin_profesor': Materia.objects.filter(profesormateria__isnull=True).count(),
        'aulas_disponibles': Aula.objects.filter(horario__isnull=True).count(),
    }

    # Materias por número de profesores
    materias_populares = Materia.objects.annotate(
        num_profesores=Count('profesormateria')
    ).order_by('-num_profesores')[:5]

    return Response({
        'estadisticas': stats,
        'materias_mas_profesores': MateriaListSerializer(materias_populares, many=True).data,
    })