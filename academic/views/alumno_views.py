from rest_framework import status
from datetime import datetime, date
from shared.permissions import IsAlumno
from rest_framework.response import Response
from ..models import Horario, Trimestre, Gestion
from ..serializers import HorarioAlumnoSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mi_horario(request):
    """
    Endpoint para obtener el horario personal del alumno
    Query params opcionales:
    - trimestre: ID del trimestre (por defecto el activo)
    - fecha: YYYY-MM-DD para horario de un día específico
    """
    try:
        alumno = request.user.alumno

        # Obtener trimestre (por defecto el activo)
        trimestre_id = request.query_params.get('trimestre')
        if trimestre_id:
            try:
                trimestre = Trimestre.objects.get(id=trimestre_id)
            except Trimestre.DoesNotExist:
                return Response(
                    {'error': 'Trimestre no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Buscar trimestre activo de la gestión activa
            try:
                gestion_activa = Gestion.objects.get(activa=True)
                trimestre = Trimestre.objects.filter(
                    gestion=gestion_activa,
                    fecha_inicio__lte=date.today(),
                    fecha_fin__gte=date.today()
                ).first()

                if not trimestre:
                    # Si no hay trimestre activo, tomar el más reciente
                    trimestre = Trimestre.objects.filter(
                        gestion=gestion_activa
                    ).order_by('-numero').first()

            except Gestion.DoesNotExist:
                return Response(
                    {'error': 'No hay gestión académica activa'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if not trimestre:
            return Response(
                {'error': 'No se encontró trimestre válido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filtrar horarios del grupo del alumno
        horarios = Horario.objects.filter(
            grupo=alumno.grupo,
            trimestre=trimestre
        ).select_related(
            'profesor_materia__materia',
            'profesor_materia__profesor',
            'aula'
        ).order_by('dia_semana', 'hora_inicio')

        # Filtro por fecha específica si se proporciona
        fecha_param = request.query_params.get('fecha')
        if fecha_param:
            try:
                fecha_obj = datetime.strptime(fecha_param, '%Y-%m-%d').date()
                dia_semana = fecha_obj.weekday() + 1  # Lunes=1, Viernes=5
                if dia_semana > 5:
                    return Response(
                        {'horarios': [], 'mensaje': 'No hay clases los fines de semana'},
                        status=status.HTTP_200_OK
                    )
                horarios = horarios.filter(dia_semana=dia_semana)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = HorarioAlumnoSerializer(horarios, many=True)

        return Response({
            'horarios': serializer.data,
            'trimestre': {
                'id': trimestre.id,
                'nombre': trimestre.nombre,
                'fecha_inicio': trimestre.fecha_inicio,
                'fecha_fin': trimestre.fecha_fin
            },
            'grupo': {
                'nivel': alumno.grupo.nivel.nombre,
                'letra': alumno.grupo.letra
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )