import academic
from django.db.models import Q
from rest_framework import status
from shared.permissions import IsDirector
from django.core.paginator import Paginator
from rest_framework.response import Response
from .models import Materia, Aula, Nivel, Grupo
from audit.utils import registrar_accion_bitacora
from rest_framework.decorators import api_view, permission_classes
from .serializers import (
    MateriaSerializer, MateriaListSerializer,
    AulaSerializer, AulaListSerializer,
    NivelSerializer, GrupoSerializer
)


@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def materia_list_create(request):
    """
    GET: Listar materias con paginación y filtros
    POST: Crear nueva materia
    """
    if request.method == 'GET':
        # Parámetros de consulta
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        search = request.GET.get('search', '')

        # Filtrar materias
        queryset = Materia.objects.all().order_by('codigo')

        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search) |
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )

        # Paginar
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Serializar
        serializer = MateriaListSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = MateriaSerializer(data=request.data)
        if serializer.is_valid():
            materia = serializer.save()

            # Registrar en bitácora
            registrar_accion_bitacora(
                request.user,
                f'CREAR_MATERIA: {materia.codigo}',
                request
            )

            return Response(
                MateriaSerializer(materia).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def materia_detail(request, pk):
    """
    GET: Ver detalle de materia
    PUT: Actualizar materia completa
    PATCH: Actualizar materia parcial
    DELETE: Eliminar materia
    """
    try:
        materia = Materia.objects.get(pk=pk)
    except Materia.DoesNotExist:
        return Response(
            {'error': 'Materia no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = MateriaSerializer(materia)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = MateriaSerializer(materia, data=request.data, partial=partial)

        if serializer.is_valid():
            materia_updated = serializer.save()

            # Registrar en bitácora
            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_MATERIA: {materia_updated.codigo} - {materia_updated.nombre}',
                request
            )

            return Response(MateriaSerializer(materia_updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        codigo = materia.codigo
        nombre = materia.nombre

        # Verificar si tiene profesores asignados
        if materia.profesormateria_set.exists():
            return Response(
                {'error': 'No se puede eliminar la materia porque tiene profesores asignados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Eliminar materia
        materia.delete()

        # Registrar en bitácora
        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_MATERIA: {codigo} - {nombre}',
            request
        )

        return Response(
            {'message': 'Materia eliminada exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )


# CRUD DE AULAS

@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def aula_list_create(request):
    """
    GET: Listar aulas con paginación y filtros
    POST: Crear nueva aula
    """
    if request.method == 'GET':
        # Parámetros de consulta
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        search = request.GET.get('search', '')
        capacidad_min = request.GET.get('capacidad_min', '')
        capacidad_max = request.GET.get('capacidad_max', '')

        # Filtrar aulas
        queryset = Aula.objects.all().order_by('nombre')

        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search)
            )

        if capacidad_min:
            queryset = queryset.filter(capacidad__gte=capacidad_min)

        if capacidad_max:
            queryset = queryset.filter(capacidad__lte=capacidad_max)

        # Paginar
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Serializar
        serializer = AulaListSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = AulaSerializer(data=request.data)
        if serializer.is_valid():
            aula = serializer.save()

            # Registrar en bitácora
            registrar_accion_bitacora(
                request.user,
                f'CREAR_AULA: {aula.nombre} (Capacidad: {aula.capacidad})',
                request
            )

            return Response(
                AulaSerializer(aula).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def aula_detail(request, pk):
    """
    GET: Ver detalle de aula
    PUT: Actualizar aula completa
    PATCH: Actualizar aula parcial
    DELETE: Eliminar aula
    """
    try:
        aula = Aula.objects.get(pk=pk)
    except Aula.DoesNotExist:
        return Response(
            {'error': 'Aula no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = AulaSerializer(aula)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = AulaSerializer(aula, data=request.data, partial=partial)

        if serializer.is_valid():
            aula_updated = serializer.save()

            # Registrar en bitácora
            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_AULA: {aula_updated.nombre}',
                request
            )

            return Response(AulaSerializer(aula_updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        nombre = aula.nombre

        # Verificar si tiene horarios asignados
        if aula.horario_set.exists():
            return Response(
                {'error': 'No se puede eliminar el aula porque tiene horarios asignados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Eliminar aula
        aula.delete()

        # Registrar en bitácora
        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_AULA: {nombre}',
            request
        )

        return Response(
            {'message': 'Aula eliminada exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )


# CRUD ADICIONALES (Niveles y Grupos para completitud)

@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def nivel_list_create(request):
    """Listar y crear niveles académicos"""
    if request.method == 'GET':
        niveles = Nivel.objects.all().order_by('numero')
        serializer = NivelSerializer(niveles, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = NivelSerializer(data=request.data)
        if serializer.is_valid():
            nivel = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'CREAR_NIVEL: {nivel.numero}° - {nivel.nombre}',
                request
            )

            return Response(
                NivelSerializer(nivel).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def grupo_list_create(request):
    """Listar y crear grupos"""
    if request.method == 'GET':
        nivel = request.GET.get('nivel', '')
        queryset = Grupo.objects.all().select_related('nivel').order_by('nivel__numero', 'letra')

        if nivel:
            queryset = queryset.filter(nivel__numero=nivel)

        serializer = GrupoSerializer(queryset, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = GrupoSerializer(data=request.data)
        if serializer.is_valid():
            grupo = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'CREAR_GRUPO: {grupo.nivel.numero}° {grupo.letra}',
                request
            )

            return Response(
                GrupoSerializer(grupo).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
        num_profesores=academic.models.Count('profesormateria')
    ).order_by('-num_profesores')[:5]

    return Response({
        'estadisticas': stats,
        'materias_mas_profesores': MateriaListSerializer(materias_populares, many=True).data,
    })
