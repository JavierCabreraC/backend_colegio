from .models import Bitacora
from rest_framework import status
from django.core.paginator import Paginator
from .serializers import BitacoraSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bitacora_list(request):
    """
    Lista los registros de bitácora con paginación
    Solo directores pueden acceder
    """
    # Verificar permisos - solo directores
    if request.user.tipo_usuario != 'director':
        return Response(
            {'error': 'No tienes permisos para acceder a la bitácora'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Obtener parámetros de consulta
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    tipo_accion = request.GET.get('tipo_accion', None)
    usuario_id = request.GET.get('usuario_id', None)

    # Filtrar registros
    queryset = Bitacora.objects.all().order_by('-fecha_hora')

    if tipo_accion:
        queryset = queryset.filter(tipo_accion=tipo_accion)

    if usuario_id:
        queryset = queryset.filter(usuario_id=usuario_id)

    # Paginar resultados
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    # Serializar datos
    serializer = BitacoraSerializer(page_obj.object_list, many=True)

    return Response({
        'count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'results': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bitacora_stats(request):
    """
    Estadísticas de la bitácora
    Solo directores pueden acceder
    """
    if request.user.tipo_usuario != 'director':
        return Response(
            {'error': 'No tienes permisos para acceder a las estadísticas'},
            status=status.HTTP_403_FORBIDDEN
        )

    from django.db.models import Count
    from datetime import datetime, timedelta

    # Estadísticas generales
    total_acciones = Bitacora.objects.count()

    # Acciones por tipo
    acciones_por_tipo = Bitacora.objects.values('tipo_accion').annotate(
        count=Count('tipo_accion')
    ).order_by('-count')

    # Acciones en los últimos 7 días
    fecha_limite = datetime.now() - timedelta(days=7)
    acciones_ultimos_7_dias = Bitacora.objects.filter(
        fecha_hora__gte=fecha_limite
    ).count()

    # Usuarios más activos
    usuarios_activos = Bitacora.objects.values(
        'usuario__email', 'usuario__tipo_usuario'
    ).annotate(
        count=Count('usuario')
    ).order_by('-count')[:10]

    return Response({
        'total_acciones': total_acciones,
        'acciones_por_tipo': list(acciones_por_tipo),
        'acciones_ultimos_7_dias': acciones_ultimos_7_dias,
        'usuarios_mas_activos': list(usuarios_activos)
    }, status=status.HTTP_200_OK)

