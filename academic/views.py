from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from django.db.models import Count
from authentication.models import Alumno
from shared.permissions import IsDirector
from django.core.paginator import Paginator
from rest_framework.response import Response
from audit.utils import registrar_accion_bitacora
from rest_framework.decorators import api_view, permission_classes
from .serializers import (
    MateriaSerializer, MateriaListSerializer, AulaSerializer, AulaListSerializer, NivelSerializer, GrupoSerializer,
    GestionSerializer, ProfesorMateriaSerializer, HorarioSerializer, MatriculacionSerializer, TrimestreSerializer
)
from .models import Materia, Aula, Nivel, Grupo, Gestion, ProfesorMateria, Horario, Matriculacion, Trimestre

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
                f'ACTUALIZAR_MATERIA: {materia_updated.codigo}',
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
            f'ELIMINAR_MATERIA: {codigo}',
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
                f'CREAR_AULA: {aula.nombre}',
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
                f'ACTUALIZAR_AULA',
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
            f'ELIMINAR_AULA',
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
                f'CREAR_NIVEL: {nivel.numero}°',
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
                f'CREAR_GRUPO: {grupo.nivel.numero}°',
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
        num_profesores=Count('profesormateria')
    ).order_by('-num_profesores')[:5]

    return Response({
        'estadisticas': stats,
        'materias_mas_profesores': MateriaListSerializer(materias_populares, many=True).data,
    })

@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def gestion_list_create(request):
    """
    GET: Listar gestiones académicas
    POST: Crear nueva gestión
    """
    if request.method == 'GET':
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        activa = request.GET.get('activa', '')

        queryset = Gestion.objects.all().order_by('-anio')

        if activa:
            activa_bool = activa.lower() == 'true'
            queryset = queryset.filter(activa=activa_bool)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = GestionSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = GestionSerializer(data=request.data)
        if serializer.is_valid():
            # Solo una gestión puede estar activa
            if request.data.get('activa', False):
                Gestion.objects.filter(activa=True).update(activa=False)

            gestion = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'CREAR_GESTION: {gestion.anio}',
                request
            )

            return Response(
                GestionSerializer(gestion).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def gestion_detail(request, pk):
    """
    GET: Ver detalle de gestión
    PUT/PATCH: Actualizar gestión
    DELETE: Eliminar gestión
    """
    try:
        gestion = Gestion.objects.get(pk=pk)
    except Gestion.DoesNotExist:
        return Response(
            {'error': 'Gestión no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = GestionSerializer(gestion)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = GestionSerializer(gestion, data=request.data, partial=partial)

        if serializer.is_valid():
            # Solo una gestión puede estar activa
            if request.data.get('activa', False):
                Gestion.objects.exclude(pk=pk).update(activa=False)

            gestion_updated = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_GESTION: {gestion_updated.anio}',
                request
            )

            return Response(GestionSerializer(gestion_updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        anio = gestion.anio

        # Verificar si tiene matriculaciones
        if gestion.matriculacion_set.exists():
            return Response(
                {'error': 'No se puede eliminar la gestión porque tiene matriculaciones'},
                status=status.HTTP_400_BAD_REQUEST
            )

        gestion.delete()

        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_GESTION: {anio}',
            request
        )

        return Response(
            {'message': 'Gestión eliminada exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )

@api_view(['POST'])
@permission_classes([IsDirector])
def activar_gestion(request, pk):
    """Activar una gestión específica (solo una puede estar activa)"""
    try:
        gestion = Gestion.objects.get(pk=pk)
    except Gestion.DoesNotExist:
        return Response(
            {'error': 'Gestión no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Desactivar todas las demás
    Gestion.objects.update(activa=False)

    # Activar la seleccionada
    gestion.activa = True
    gestion.save()

    registrar_accion_bitacora(
        request.user,
        f'ACTIVAR_GESTION: {gestion.anio}',
        request
    )

    return Response({
        'message': f'Gestión {gestion.anio} activada exitosamente',
        'gestion': GestionSerializer(gestion).data
    })

@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def profesor_materia_list_create(request):
    """
    GET: Listar asignaciones profesor-materia
    POST: Asignar profesor a materia
    """
    if request.method == 'GET':
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        profesor_id = request.GET.get('profesor', '')
        materia_id = request.GET.get('materia', '')

        queryset = ProfesorMateria.objects.all().select_related(
            'profesor', 'profesor__usuario', 'materia'
        ).order_by('profesor__apellidos')

        if profesor_id:
            queryset = queryset.filter(profesor_id=profesor_id)
        if materia_id:
            queryset = queryset.filter(materia_id=materia_id)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = ProfesorMateriaSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = ProfesorMateriaSerializer(data=request.data)
        if serializer.is_valid():
            profesor_materia = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'ASIGNAR_PROFESOR_MATERIA: {profesor_materia.profesor.nombres} - {profesor_materia.materia.nombre}',
                request
            )

            return Response(
                ProfesorMateriaSerializer(profesor_materia).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsDirector])
def profesor_materia_delete(request, pk):
    """Eliminar asignación profesor-materia"""
    try:
        profesor_materia = ProfesorMateria.objects.select_related(
            'profesor', 'materia'
        ).get(pk=pk)
    except ProfesorMateria.DoesNotExist:
        return Response(
            {'error': 'Asignación no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    profesor_nombre = f"{profesor_materia.profesor.nombres} {profesor_materia.profesor.apellidos}"
    materia_nombre = profesor_materia.materia.nombre

    # Verificar si tiene horarios asignados
    if profesor_materia.horario_set.exists():
        return Response(
            {'error': 'No se puede eliminar la asignación porque tiene horarios activos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    profesor_materia.delete()

    registrar_accion_bitacora(
        request.user,
        f'ELIMINAR_ASIGNACION: {profesor_nombre} - {materia_nombre}',
        request
    )

    return Response(
        {'message': 'Asignación eliminada exitosamente'},
        status=status.HTTP_204_NO_CONTENT
    )

@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def trimestre_list_create(request):
    """
    GET: Listar trimestres
    POST: Crear nuevo trimestre
    """
    if request.method == 'GET':
        gestion_id = request.GET.get('gestion', '')

        queryset = Trimestre.objects.all().select_related('gestion').order_by('gestion__anio', 'numero')

        if gestion_id:
            queryset = queryset.filter(gestion_id=gestion_id)

        serializer = TrimestreSerializer(queryset, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = TrimestreSerializer(data=request.data)
        if serializer.is_valid():
            trimestre = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'CREAR_TRIMESTRE: {trimestre.gestion.anio} - T{trimestre.numero}',
                request
            )

            return Response(
                TrimestreSerializer(trimestre).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def trimestre_detail(request, pk):
    """CRUD individual de trimestres"""
    try:
        trimestre = Trimestre.objects.select_related('gestion').get(pk=pk)
    except Trimestre.DoesNotExist:
        return Response(
            {'error': 'Trimestre no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = TrimestreSerializer(trimestre)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = TrimestreSerializer(trimestre, data=request.data, partial=partial)

        if serializer.is_valid():
            trimestre_updated = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_TRIMESTRE: {trimestre_updated.gestion.anio} - T{trimestre_updated.numero}',
                request
            )

            return Response(TrimestreSerializer(trimestre_updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        gestion_anio = trimestre.gestion.anio
        numero = trimestre.numero

        # Verificar si tiene horarios asignados
        if trimestre.horario_set.exists():
            return Response(
                {'error': 'No se puede eliminar el trimestre porque tiene horarios asignados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        trimestre.delete()

        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_TRIMESTRE: {gestion_anio} - T{numero}',
            request
        )

        return Response(
            {'message': 'Trimestre eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )

@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def matriculacion_list_create(request):
    """
    GET: Listar matriculaciones
    POST: Matricular alumno
    """
    if request.method == 'GET':
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        gestion_id = request.GET.get('gestion', '')
        activa = request.GET.get('activa', '')
        search = request.GET.get('search', '')

        queryset = Matriculacion.objects.all().select_related(
            'alumno', 'alumno__usuario', 'gestion'
        ).order_by('-fecha_matriculacion')

        if gestion_id:
            queryset = queryset.filter(gestion_id=gestion_id)

        if activa:
            activa_bool = activa.lower() == 'true'
            queryset = queryset.filter(activa=activa_bool)

        if search:
            queryset = queryset.filter(
                Q(alumno__nombres__icontains=search) |
                Q(alumno__apellidos__icontains=search) |
                Q(alumno__matricula__icontains=search)
            )

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = MatriculacionSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = MatriculacionSerializer(data=request.data)
        if serializer.is_valid():
            matriculacion = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'MATRICULAR_ALUMNO: {matriculacion.alumno.matricula} - {matriculacion.gestion.anio}',
                request
            )

            return Response(
                MatriculacionSerializer(matriculacion).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def matriculacion_detail(request, pk):
    """CRUD individual de matriculaciones"""
    try:
        matriculacion = Matriculacion.objects.select_related(
            'alumno', 'alumno__usuario', 'gestion'
        ).get(pk=pk)
    except Matriculacion.DoesNotExist:
        return Response(
            {'error': 'Matriculación no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = MatriculacionSerializer(matriculacion)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = MatriculacionSerializer(matriculacion, data=request.data, partial=partial)

        if serializer.is_valid():
            matriculacion_updated = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_MATRICULACION: {matriculacion_updated.alumno.matricula}',
                request
            )

            return Response(MatriculacionSerializer(matriculacion_updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        alumno_matricula = matriculacion.alumno.matricula
        gestion_anio = matriculacion.gestion.anio

        matriculacion.delete()

        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_MATRICULACION: {alumno_matricula} - {gestion_anio}',
            request
        )

        return Response(
            {'message': 'Matriculación eliminada exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )

@api_view(['POST'])
@permission_classes([IsDirector])
def matricular_masivo(request):
    """Matricular múltiples alumnos a una gestión"""
    gestion_id = request.data.get('gestion_id')
    alumnos_ids = request.data.get('alumnos_ids', [])
    fecha_matriculacion = request.data.get('fecha_matriculacion')

    if not gestion_id or not alumnos_ids:
        return Response(
            {'error': 'gestion_id y alumnos_ids son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        gestion = Gestion.objects.get(pk=gestion_id)
    except Gestion.DoesNotExist:
        return Response(
            {'error': 'Gestión no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    matriculaciones_creadas = []
    errores = []

    for alumno_id in alumnos_ids:
        try:
            alumno = Alumno.objects.get(pk=alumno_id)

            # Verificar si ya está matriculado
            if Matriculacion.objects.filter(alumno=alumno, gestion=gestion).exists():
                errores.append(f'Alumno {alumno.matricula} ya está matriculado')
                continue

            matriculacion = Matriculacion.objects.create(
                alumno=alumno,
                gestion=gestion,
                fecha_matriculacion=fecha_matriculacion or timezone.now().date()
            )
            matriculaciones_creadas.append(matriculacion)

        except Alumno.DoesNotExist:
            errores.append(f'Alumno con ID {alumno_id} no encontrado')

    registrar_accion_bitacora(
        request.user,
        f'MATRICULACION_MASIVA: {len(matriculaciones_creadas)} alumnos - {gestion.anio}',
        request
    )

    return Response({
        'matriculaciones_creadas': len(matriculaciones_creadas),
        'errores': errores,
        'matriculaciones': MatriculacionSerializer(matriculaciones_creadas, many=True).data
    })

@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def horario_list_create(request):
    """
    GET: Listar horarios
    POST: Crear nuevo horario
    """
    if request.method == 'GET':
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        trimestre_id = request.GET.get('trimestre', '')
        grupo_id = request.GET.get('grupo', '')
        profesor_id = request.GET.get('profesor', '')
        dia_semana = request.GET.get('dia_semana', '')

        queryset = Horario.objects.all().select_related(
            'profesor_materia__profesor',
            'profesor_materia__materia',
            'grupo', 'grupo__nivel',
            'aula', 'trimestre'
        ).order_by('dia_semana', 'hora_inicio')

        if trimestre_id:
            queryset = queryset.filter(trimestre_id=trimestre_id)
        if grupo_id:
            queryset = queryset.filter(grupo_id=grupo_id)
        if profesor_id:
            queryset = queryset.filter(profesor_materia__profesor_id=profesor_id)
        if dia_semana:
            queryset = queryset.filter(dia_semana=dia_semana)

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = HorarioSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = HorarioSerializer(data=request.data)
        if serializer.is_valid():
            # Validar conflictos de horario
            conflictos = validar_conflictos_horario(serializer.validated_data)
            if conflictos:
                return Response(
                    {'error': 'Conflictos de horario detectados', 'conflictos': conflictos},
                    status=status.HTTP_400_BAD_REQUEST
                )

            horario = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'CREAR_HORARIO: {horario.profesor_materia.materia.nombre}',
                request
            )

            return Response(
                HorarioSerializer(horario).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def horario_detail(request, pk):
    """CRUD individual de horarios"""
    try:
        horario = Horario.objects.select_related(
            'profesor_materia__profesor',
            'profesor_materia__materia',
            'grupo', 'aula', 'trimestre'
        ).get(pk=pk)
    except Horario.DoesNotExist:
        return Response(
            {'error': 'Horario no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = HorarioSerializer(horario)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = HorarioSerializer(horario, data=request.data, partial=partial)

        if serializer.is_valid():
            # Validar conflictos (excluyendo el horario actual)
            conflictos = validar_conflictos_horario(serializer.validated_data, excluir_id=pk)
            if conflictos:
                return Response(
                    {'error': 'Conflictos de horario detectados', 'conflictos': conflictos},
                    status=status.HTTP_400_BAD_REQUEST
                )

            horario_updated = serializer.save()

            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_HORARIO: {horario_updated.profesor_materia.materia.nombre}',
                request
            )

            return Response(HorarioSerializer(horario_updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        materia_nombre = horario.profesor_materia.materia.nombre

        horario.delete()

        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_HORARIO: {materia_nombre}',
            request
        )

        return Response(
            {'message': 'Horario eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )

def validar_conflictos_horario(data, excluir_id=None):
    """Función auxiliar para validar conflictos de horario"""
    conflictos = []

    # Conflicto de profesor (no puede estar en dos lugares al mismo tiempo)
    profesor_conflicto = Horario.objects.filter(
        profesor_materia__profesor=data['profesor_materia'].profesor,
        trimestre=data['trimestre'],
        dia_semana=data['dia_semana'],
        hora_inicio__lt=data['hora_fin'],
        hora_fin__gt=data['hora_inicio']
    )

    if excluir_id:
        profesor_conflicto = profesor_conflicto.exclude(pk=excluir_id)

    if profesor_conflicto.exists():
        conflictos.append('El profesor ya tiene clases en este horario')

    # Conflicto de aula
    aula_conflicto = Horario.objects.filter(
        aula=data['aula'],
        trimestre=data['trimestre'],
        dia_semana=data['dia_semana'],
        hora_inicio__lt=data['hora_fin'],
        hora_fin__gt=data['hora_inicio']
    )

    if excluir_id:
        aula_conflicto = aula_conflicto.exclude(pk=excluir_id)

    if aula_conflicto.exists():
        conflictos.append('El aula ya está ocupada en este horario')

    # Conflicto de grupo
    grupo_conflicto = Horario.objects.filter(
        grupo=data['grupo'],
        trimestre=data['trimestre'],
        dia_semana=data['dia_semana'],
        hora_inicio__lt=data['hora_fin'],
        hora_fin__gt=data['hora_inicio']
    )

    if excluir_id:
        grupo_conflicto = grupo_conflicto.exclude(pk=excluir_id)

    if grupo_conflicto.exists():
        conflictos.append('El grupo ya tiene clases en este horario')

    return conflictos

@api_view(['GET'])
@permission_classes([IsDirector])
def horario_vista_semanal(request):
    """Vista de horarios en formato de grid semanal"""
    trimestre_id = request.GET.get('trimestre')
    grupo_id = request.GET.get('grupo')

    if not trimestre_id:
        return Response(
            {'error': 'trimestre_id es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    queryset = Horario.objects.filter(trimestre_id=trimestre_id).select_related(
        'profesor_materia__profesor',
        'profesor_materia__materia',
        'grupo', 'aula'
    )

    if grupo_id:
        queryset = queryset.filter(grupo_id=grupo_id)

    # Organizar por días y horas
    horarios_organizados = {}
    for dia in range(1, 6):  # Lunes a Viernes
        horarios_organizados[dia] = list(
            queryset.filter(dia_semana=dia).order_by('hora_inicio')
        )

    return Response({
        'horarios_por_dia': {
            str(dia): HorarioSerializer(horarios, many=True).data
            for dia, horarios in horarios_organizados.items()
        }
    })
