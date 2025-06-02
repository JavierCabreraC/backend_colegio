from ..models import Profesor
from rest_framework import status
from rest_framework.response import Response
from audit.utils import registrar_accion_bitacora
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from ..serializers.profesor_serializers import DashboardProfesorSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_profesor(request):
    """Dashboard completo para profesores"""
    # Verificar que es profesor
    if request.user.tipo_usuario != 'profesor':
        return Response(
            {'error': 'No tienes permisos para acceder a este dashboard'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        profesor = Profesor.objects.select_related('usuario').get(
            usuario=request.user
        )
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Perfil de profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Registrar acceso en bitácora
    registrar_accion_bitacora(
        request.user,
        'ACCESO_DASHBOARD_PROFESOR',
        request
    )

    # Serializar datos
    serializer = DashboardProfesorSerializer(profesor)
    return Response(serializer.data)