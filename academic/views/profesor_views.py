from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from authentication.models import Alumno, Profesor
from shared.permissions import IsDirector
from django.core.paginator import Paginator
from rest_framework.response import Response
from audit.utils import registrar_accion_bitacora
from rest_framework.decorators import api_view, permission_classes
from ..models import Materia, Aula, Nivel, Grupo, Gestion, ProfesorMateria, Horario, Matriculacion, Trimestre
from .director_views import (
    MateriaSerializer, MateriaListSerializer, AulaSerializer, AulaListSerializer, NivelSerializer, GrupoSerializer,
    GestionSerializer, ProfesorMateriaSerializer, HorarioSerializer, MatriculacionSerializer, TrimestreSerializer,
    MisHorarios_Serializer, MisMaterias_Serializer, MisGrupos_Serializer, MisAlumnos_Serializer
)


# ==========================================
# VISTAS PARA PROFESORES
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_materias(request):
    """Listar materias asignadas al profesor autenticado"""
    # Verificar que es profesor
    if request.user.tipo_usuario != 'profesor':
        return Response(
            {'error': 'Solo profesores pueden acceder a este endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        profesor = Profesor.objects.get(usuario=request.user)
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Perfil de profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener materias del profesor
    profesor_materias = ProfesorMateria.objects.filter(
        profesor=profesor
    ).select_related('materia').order_by('materia__codigo')

    serializer = MisMaterias_Serializer(profesor_materias, many=True)

    # Registrar en bitácora
    registrar_accion_bitacora(
        request.user,
        'VER_MIS_MATERIAS',
        request
    )

    return Response({
        'count': profesor_materias.count(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_grupos(request):
    """Listar grupos asignados al profesor autenticado"""
    if request.user.tipo_usuario != 'profesor':
        return Response(
            {'error': 'Solo profesores pueden acceder a este endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        profesor = Profesor.objects.get(usuario=request.user)
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Perfil de profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener grupos únicos donde enseña el profesor
    grupos_ids = Horario.objects.filter(
        profesor_materia__profesor=profesor
    ).values_list('grupo_id', flat=True).distinct()

    grupos = Grupo.objects.filter(
        id__in=grupos_ids
    ).select_related('nivel').order_by('nivel__numero', 'letra')

    serializer = MisGrupos_Serializer(
        grupos,
        many=True,
        context={'profesor': profesor}
    )

    registrar_accion_bitacora(
        request.user,
        'VER_MIS_GRUPOS',
        request
    )

    return Response({
        'count': grupos.count(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_alumnos(request):
    """Listar todos los alumnos en clases del profesor"""
    if request.user.tipo_usuario != 'profesor':
        return Response(
            {'error': 'Solo profesores pueden acceder a este endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        profesor = Profesor.objects.get(usuario=request.user)
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Perfil de profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Parámetros de consulta
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    search = request.GET.get('search', '')
    grupo_id = request.GET.get('grupo', '')

    # Obtener grupos donde enseña el profesor
    grupos_ids = Horario.objects.filter(
        profesor_materia__profesor=profesor
    ).values_list('grupo_id', flat=True).distinct()

    # Filtrar alumnos
    queryset = Alumno.objects.filter(
        grupo__in=grupos_ids
    ).select_related('usuario', 'grupo', 'grupo__nivel').order_by('nombres', 'apellidos')

    if search:
        queryset = queryset.filter(
            Q(nombres__icontains=search) |
            Q(apellidos__icontains=search) |
            Q(matricula__icontains=search) |
            Q(usuario__email__icontains=search)
        )

    if grupo_id:
        queryset = queryset.filter(grupo_id=grupo_id)

    # Paginar
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    serializer = MisAlumnos_Serializer(page_obj.object_list, many=True)

    registrar_accion_bitacora(
        request.user,
        'VER_MIS_ALUMNOS',
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_horarios(request):
    """Listar todos los horarios del profesor con filtros"""
    if request.user.tipo_usuario != 'profesor':
        return Response(
            {'error': 'Solo profesores pueden acceder a este endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        profesor = Profesor.objects.get(usuario=request.user)
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Perfil de profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Parámetros de consulta
    trimestre_id = request.GET.get('trimestre', '')
    dia_semana = request.GET.get('dia_semana', '')
    materia_id = request.GET.get('materia', '')

    # Obtener horarios del profesor
    queryset = Horario.objects.filter(
        profesor_materia__profesor=profesor
    ).select_related(
        'profesor_materia__materia',
        'grupo', 'grupo__nivel',
        'aula', 'trimestre', 'trimestre__gestion'
    ).order_by('dia_semana', 'hora_inicio')

    # Aplicar filtros
    if trimestre_id:
        queryset = queryset.filter(trimestre_id=trimestre_id)

    if dia_semana:
        queryset = queryset.filter(dia_semana=dia_semana)

    if materia_id:
        queryset = queryset.filter(profesor_materia__materia_id=materia_id)

    serializer = MisHorarios_Serializer(queryset, many=True)

    registrar_accion_bitacora(
        request.user,
        'VER_MIS_HORARIOS',
        request
    )

    return Response({
        'count': queryset.count(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_horario_hoy(request):
    """Clases del profesor para el día actual"""
    if request.user.tipo_usuario != 'profesor':
        return Response(
            {'error': 'Solo profesores pueden acceder a este endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        profesor = Profesor.objects.get(usuario=request.user)
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Perfil de profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    from datetime import date
    hoy = date.today()
    dia_semana = hoy.weekday() + 1  # Django usa 1=Lunes

    if dia_semana > 5:  # Fin de semana
        return Response({
            'mensaje': 'No hay clases programadas para hoy (fin de semana)',
            'dia': hoy.strftime('%A'),
            'results': []
        })

    # Obtener gestión activa
    gestion_activa = Gestion.objects.filter(activa=True).first()
    if not gestion_activa:
        return Response({
            'mensaje': 'No hay gestión académica activa',
            'results': []
        })

    # Obtener trimestre actual
    trimestre_actual = Trimestre.objects.filter(
        gestion=gestion_activa,
        fecha_inicio__lte=hoy,
        fecha_fin__gte=hoy
    ).first()

    if not trimestre_actual:
        return Response({
            'mensaje': 'No hay trimestre activo para la fecha actual',
            'results': []
        })

    # Obtener horarios de hoy
    horarios = Horario.objects.filter(
        profesor_materia__profesor=profesor,
        dia_semana=dia_semana,
        trimestre=trimestre_actual
    ).select_related(
        'profesor_materia__materia',
        'grupo', 'grupo__nivel',
        'aula'
    ).order_by('hora_inicio')

    serializer = MisHorarios_Serializer(horarios, many=True)

    return Response({
        'fecha': hoy,
        'dia_semana': dia_semana,
        'total_clases': horarios.count(),
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mi_horario_semana(request):
    """Vista semanal de horarios del profesor"""
    if request.user.tipo_usuario != 'profesor':
        return Response(
            {'error': 'Solo profesores pueden acceder a este endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        profesor = Profesor.objects.get(usuario=request.user)
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Perfil de profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener trimestre (parámetro opcional)
    trimestre_id = request.GET.get('trimestre', '')

    if trimestre_id:
        try:
            trimestre = Trimestre.objects.get(id=trimestre_id)
        except Trimestre.DoesNotExist:
            return Response(
                {'error': 'Trimestre no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Usar trimestre actual
        from datetime import date
        gestion_activa = Gestion.objects.filter(activa=True).first()
        if not gestion_activa:
            return Response({'error': 'No hay gestión activa'}, status=400)

        hoy = date.today()
        trimestre = Trimestre.objects.filter(
            gestion=gestion_activa,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).first()

        if not trimestre:
            return Response({'error': 'No hay trimestre activo'}, status=400)

    # Organizar horarios por día
    horarios_semana = {}
    for dia in range(1, 6):  # Lunes a Viernes
        horarios = Horario.objects.filter(
            profesor_materia__profesor=profesor,
            trimestre=trimestre,
            dia_semana=dia
        ).select_related(
            'profesor_materia__materia',
            'grupo', 'grupo__nivel',
            'aula'
        ).order_by('hora_inicio')

        horarios_semana[dia] = MisHorarios_Serializer(horarios, many=True).data

    return Response({
        'trimestre': {
            'id': trimestre.id,
            'nombre': trimestre.nombre,
            'gestion': trimestre.gestion.anio
        },
        'horarios_por_dia': horarios_semana
    })
