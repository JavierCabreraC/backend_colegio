from django.db.models import Q
from rest_framework import status
from django.core.paginator import Paginator
from rest_framework.response import Response
from authentication.models import Profesor
from audit.utils import registrar_accion_bitacora
from rest_framework.permissions import IsAuthenticated
from ..models import Examen, Tarea, NotaExamen, NotaTarea
from academic.models import ProfesorMateria, Trimestre, Gestion
from rest_framework.decorators import api_view, permission_classes
from ..serializers import (
    MisExamenes_Serializer, ExamenCreateUpdateSerializer,
    MisTareas_Serializer, TareaCreateUpdateSerializer,
    ProfesorMateriaSimpleSerializer, TrimestreSimpleSerializer
)


def validar_profesor_autenticado(request):
    """Función auxiliar para validar profesor autenticado"""
    if request.user.tipo_usuario != 'profesor':
        return None, Response(
            {'error': 'Solo profesores pueden acceder a este endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        profesor = Profesor.objects.get(usuario=request.user)
        return profesor, None
    except Profesor.DoesNotExist:
        return None, Response(
            {'error': 'Perfil de profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )


# ==========================================
# GESTIÓN DE EXÁMENES
# ==========================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def mis_examenes(request):
    """
    GET: Listar exámenes del profesor
    POST: Crear nuevo examen
    """
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    if request.method == 'GET':
        # Parámetros de consulta
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        search = request.GET.get('search', '')
        trimestre_id = request.GET.get('trimestre', '')
        materia_id = request.GET.get('materia', '')
        numero_parcial = request.GET.get('numero_parcial', '')

        # Obtener exámenes del profesor
        queryset = Examen.objects.filter(
            profesor_materia__profesor=profesor
        ).select_related(
            'profesor_materia__materia',
            'trimestre', 'trimestre__gestion'
        ).order_by('-fecha_examen')

        # Aplicar filtros
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(profesor_materia__materia__nombre__icontains=search)
            )

        if trimestre_id:
            queryset = queryset.filter(trimestre_id=trimestre_id)

        if materia_id:
            queryset = queryset.filter(profesor_materia__materia_id=materia_id)

        if numero_parcial:
            queryset = queryset.filter(numero_parcial=numero_parcial)

        # Paginar
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = MisExamenes_Serializer(page_obj.object_list, many=True)

        registrar_accion_bitacora(
            request.user,
            'VER_MIS_EXAMENES',
            request
        )

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = ExamenCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            examen = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'CREAR_EXAMEN: {examen.titulo}',
                request
            )

            return Response(
                MisExamenes_Serializer(examen).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def examen_detail(request, pk):
    """
    GET: Ver detalle de examen
    PATCH: Actualizar examen
    """
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        examen = Examen.objects.select_related(
            'profesor_materia__materia',
            'trimestre', 'trimestre__gestion'
        ).get(
            pk=pk,
            profesor_materia__profesor=profesor
        )
    except Examen.DoesNotExist:
        return Response(
            {'error': 'Examen no encontrado o no tienes permisos para acceder'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = MisExamenes_Serializer(examen)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = ExamenCreateUpdateSerializer(
            examen,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            examen_updated = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_EXAMEN: {examen_updated.titulo}',
                request
            )

            return Response(MisExamenes_Serializer(examen_updated).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==========================================
# GESTIÓN DE TAREAS
# ==========================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def mis_tareas(request):
    """
    GET: Listar tareas del profesor
    POST: Crear nueva tarea
    """
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    if request.method == 'GET':
        # Parámetros de consulta
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        search = request.GET.get('search', '')
        trimestre_id = request.GET.get('trimestre', '')
        materia_id = request.GET.get('materia', '')
        estado = request.GET.get('estado', '')  # 'pendiente', 'vencida', 'activa'

        # Obtener tareas del profesor
        queryset = Tarea.objects.filter(
            profesor_materia__profesor=profesor
        ).select_related(
            'profesor_materia__materia',
            'trimestre', 'trimestre__gestion'
        ).order_by('-fecha_asignacion')

        # Aplicar filtros
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(profesor_materia__materia__nombre__icontains=search)
            )

        if trimestre_id:
            queryset = queryset.filter(trimestre_id=trimestre_id)

        if materia_id:
            queryset = queryset.filter(profesor_materia__materia_id=materia_id)

        if estado:
            from datetime import date
            hoy = date.today()
            if estado == 'vencida':
                queryset = queryset.filter(fecha_entrega__lt=hoy)
            elif estado == 'activa':
                queryset = queryset.filter(fecha_entrega__gte=hoy)

        # Paginar
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = MisTareas_Serializer(page_obj.object_list, many=True)

        registrar_accion_bitacora(
            request.user,
            'VER_MIS_TAREAS',
            request
        )

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = TareaCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            tarea = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'CREAR_TAREA: {tarea.titulo}',
                request
            )

            return Response(
                MisTareas_Serializer(tarea).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def tarea_detail(request, pk):
    """
    GET: Ver detalle de tarea
    PATCH: Actualizar tarea
    """
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        tarea = Tarea.objects.select_related(
            'profesor_materia__materia',
            'trimestre', 'trimestre__gestion'
        ).get(
            pk=pk,
            profesor_materia__profesor=profesor
        )
    except Tarea.DoesNotExist:
        return Response(
            {'error': 'Tarea no encontrada o no tienes permisos para acceder'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = MisTareas_Serializer(tarea)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = TareaCreateUpdateSerializer(
            tarea,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            tarea_updated = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_TAREA: {tarea_updated.titulo}',
                request
            )

            return Response(MisTareas_Serializer(tarea_updated).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# ENDPOINTS AUXILIARES
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def opciones_profesor_materias(request):
    """Obtener opciones de profesor-materias para formularios"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    profesor_materias = ProfesorMateria.objects.filter(
        profesor=profesor
    ).select_related('materia').order_by('materia__codigo')

    serializer = ProfesorMateriaSimpleSerializer(profesor_materias, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def opciones_trimestres(request):
    """Obtener opciones de trimestres para formularios"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    # Obtener trimestres de la gestión activa
    gestion_activa = Gestion.objects.filter(activa=True).first()
    if not gestion_activa:
        return Response({'error': 'No hay gestión activa'}, status=400)

    trimestres = Trimestre.objects.filter(
        gestion=gestion_activa
    ).order_by('numero')

    serializer = TrimestreSimpleSerializer(trimestres, many=True)
    return Response(serializer.data)