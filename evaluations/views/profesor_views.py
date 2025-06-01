from rest_framework import status
from authentication.models import Profesor
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from rest_framework.response import Response
from audit.utils import registrar_accion_bitacora
from rest_framework.permissions import IsAuthenticated
from academic.models import ProfesorMateria, Trimestre, Gestion
from rest_framework.decorators import api_view, permission_classes
from ..models import Examen, Tarea, NotaExamen, NotaTarea, Asistencia, Participacion
from ..serializers import (
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
    # Reportes - IMPORTANTE: Verificar que estén importados
    EstadisticasClaseSerializer, ReporteGrupoSerializer, RendimientoAlumnoSerializer,
    ReporteAlumnoSerializer, ReporteMateriaSerializer, PromedioGrupoSerializer
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


# ==========================================
# CALIFICACIÓN DE EXÁMENES
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def examen_alumnos(request, examen_id):
    """Lista de alumnos para calificar un examen específico"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        examen = Examen.objects.select_related(
            'profesor_materia__materia',
            'trimestre'
        ).get(
            pk=examen_id,
            profesor_materia__profesor=profesor
        )
    except Examen.DoesNotExist:
        return Response(
            {'error': 'Examen no encontrado o no tienes permisos para acceder'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener grupos donde se imparte este examen
    from academic.models import Horario, Matriculacion
    grupos_ids = Horario.objects.filter(
        profesor_materia=examen.profesor_materia,
        trimestre=examen.trimestre
    ).values_list('grupo_id', flat=True).distinct()

    # Obtener matriculaciones de alumnos en estos grupos
    matriculaciones = Matriculacion.objects.filter(
        alumno__grupo__in=grupos_ids,
        gestion=examen.trimestre.gestion,
        activa=True
    ).select_related(
        'alumno', 'alumno__usuario', 'alumno__grupo', 'alumno__grupo__nivel'
    ).order_by('alumno__nombres', 'alumno__apellidos')

    # Obtener notas ya registradas
    notas_existentes = NotaExamen.objects.filter(
        examen=examen
    ).select_related('matriculacion')

    notas_dict = {
        nota.matriculacion.id: {
            'nota': nota.nota,
            'fecha': nota.fecha_registro
        }
        for nota in notas_existentes
    }

    # Construir lista de alumnos
    alumnos_data = []
    for matriculacion in matriculaciones:
        alumno = matriculacion.alumno
        ya_calificado = matriculacion.id in notas_dict

        alumno_data = {
            'id_matriculacion': matriculacion.id,
            'alumno_id': alumno.usuario.id,
            'matricula': alumno.matricula,
            'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
            'grupo_nombre': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}",
            'email': alumno.usuario.email,
            'ya_calificado': ya_calificado,
            'nota_actual': notas_dict[matriculacion.id]['nota'] if ya_calificado else None,
            'fecha_calificacion': notas_dict[matriculacion.id]['fecha'] if ya_calificado else None
        }
        alumnos_data.append(alumno_data)

    serializer = AlumnoParaCalificarSerializer(alumnos_data, many=True)

    return Response({
        'examen': {
            'id': examen.id,
            'titulo': examen.titulo,
            'materia': examen.profesor_materia.materia.nombre,
            'fecha_examen': examen.fecha_examen,
            'ponderacion': examen.ponderacion
        },
        'total_alumnos': len(alumnos_data),
        'calificados': len([a for a in alumnos_data if a['ya_calificado']]),
        'pendientes': len([a for a in alumnos_data if not a['ya_calificado']]),
        'alumnos': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calificar_examen(request):
    """Registrar nota de examen para un alumno"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    serializer = CalificarExamenSerializer(data=request.data)

    if serializer.is_valid():
        matriculacion = serializer.validated_data['matriculacion']
        examen = serializer.validated_data['examen']
        nota = serializer.validated_data['nota']
        observaciones = serializer.validated_data.get('observaciones', '')

        # Verificar que el examen pertenece al profesor
        if examen.profesor_materia.profesor != profesor:
            return Response(
                {'error': 'No tienes permisos para calificar este examen'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Crear o actualizar la nota
        nota_examen, created = NotaExamen.objects.update_or_create(
            matriculacion=matriculacion,
            examen=examen,
            defaults={
                'nota': nota,
                'observaciones': observaciones
            }
        )

        # Registrar en bitácora
        accion = 'CREAR_NOTA_EXAMEN' if created else 'ACTUALIZAR_NOTA_EXAMEN'
        registrar_accion_bitacora(
            request.user,
            f'{accion}: {matriculacion.alumno.matricula} - {examen.titulo}',
            request
        )

        return Response(
            NotaExamenSerializer(nota_examen).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def nota_examen_detail(request, pk):
    """Actualizar nota de examen existente"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        nota_examen = NotaExamen.objects.select_related(
            'examen__profesor_materia__profesor',
            'matriculacion__alumno'
        ).get(pk=pk)
    except NotaExamen.DoesNotExist:
        return Response(
            {'error': 'Nota de examen no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar permisos
    if nota_examen.examen.profesor_materia.profesor != profesor:
        return Response(
            {'error': 'No tienes permisos para modificar esta nota'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = NotaExamenSerializer(
        nota_examen,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        nota_updated = serializer.save()

        registrar_accion_bitacora(
            request.user,
            f'MODIFICAR_NOTA_EXAMEN: {nota_updated.matriculacion.alumno.matricula}',
            request
        )

        return Response(NotaExamenSerializer(nota_updated).data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calificar_masivo(request):
    """Calificar múltiples alumnos de un examen"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    serializer = CalificarMasivoSerializer(data=request.data)

    if serializer.is_valid():
        examen_id = serializer.validated_data['examen_id']
        calificaciones = serializer.validated_data['calificaciones']

        try:
            examen = Examen.objects.get(
                pk=examen_id,
                profesor_materia__profesor=profesor
            )
        except Examen.DoesNotExist:
            return Response(
                {'error': 'Examen no encontrado o no tienes permisos'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Procesar calificaciones
        resultados = []
        errores = []

        for calificacion_data in calificaciones:
            try:
                from academic.models import Matriculacion
                matriculacion = Matriculacion.objects.get(
                    id=calificacion_data['matriculacion_id']
                )

                nota_examen, created = NotaExamen.objects.update_or_create(
                    matriculacion=matriculacion,
                    examen=examen,
                    defaults={
                        'nota': float(calificacion_data['nota']),
                        'observaciones': calificacion_data.get('observaciones', '')
                    }
                )

                resultados.append({
                    'matriculacion_id': matriculacion.id,
                    'alumno': f"{matriculacion.alumno.nombres} {matriculacion.alumno.apellidos}",
                    'nota': nota_examen.nota,
                    'accion': 'creada' if created else 'actualizada'
                })

            except Exception as e:
                errores.append({
                    'matriculacion_id': calificacion_data.get('matriculacion_id'),
                    'error': str(e)
                })

        registrar_accion_bitacora(
            request.user,
            f'CALIFICACION_MASIVA: {len(resultados)} notas - {examen.titulo}',
            request
        )

        return Response({
            'exito': len(resultados),
            'errores': len(errores),
            'resultados': resultados,
            'errores_detalle': errores
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# CALIFICACIÓN DE TAREAS
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tarea_entregas(request, tarea_id):
    """Ver entregas de una tarea (alumnos que deben ser calificados)"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        tarea = Tarea.objects.select_related(
            'profesor_materia__materia',
            'trimestre'
        ).get(
            pk=tarea_id,
            profesor_materia__profesor=profesor
        )
    except Tarea.DoesNotExist:
        return Response(
            {'error': 'Tarea no encontrada o no tienes permisos para acceder'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener grupos donde se imparte esta tarea
    from academic.models import Horario, Matriculacion
    grupos_ids = Horario.objects.filter(
        profesor_materia=tarea.profesor_materia,
        trimestre=tarea.trimestre
    ).values_list('grupo_id', flat=True).distinct()

    # Obtener matriculaciones de alumnos en estos grupos
    matriculaciones = Matriculacion.objects.filter(
        alumno__grupo__in=grupos_ids,
        gestion=tarea.trimestre.gestion,
        activa=True
    ).select_related(
        'alumno', 'alumno__usuario', 'alumno__grupo', 'alumno__grupo__nivel'
    ).order_by('alumno__nombres', 'alumno__apellidos')

    # Obtener notas ya registradas
    notas_existentes = NotaTarea.objects.filter(
        tarea=tarea
    ).select_related('matriculacion')

    notas_dict = {
        nota.matriculacion.id: {
            'nota': nota.nota,
            'fecha': nota.fecha_registro
        }
        for nota in notas_existentes
    }

    # Construir lista de alumnos
    alumnos_data = []
    for matriculacion in matriculaciones:
        alumno = matriculacion.alumno
        ya_calificado = matriculacion.id in notas_dict

        alumno_data = {
            'id_matriculacion': matriculacion.id,
            'alumno_id': alumno.usuario.id,
            'matricula': alumno.matricula,
            'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
            'grupo_nombre': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}",
            'email': alumno.usuario.email,
            'ya_calificado': ya_calificado,
            'nota_actual': notas_dict[matriculacion.id]['nota'] if ya_calificado else None,
            'fecha_calificacion': notas_dict[matriculacion.id]['fecha'] if ya_calificado else None
        }
        alumnos_data.append(alumno_data)

    serializer = AlumnoParaCalificarSerializer(alumnos_data, many=True)

    return Response({
        'tarea': {
            'id': tarea.id,
            'titulo': tarea.titulo,
            'materia': tarea.profesor_materia.materia.nombre,
            'fecha_entrega': tarea.fecha_entrega,
            'ponderacion': tarea.ponderacion
        },
        'total_alumnos': len(alumnos_data),
        'calificados': len([a for a in alumnos_data if a['ya_calificado']]),
        'pendientes': len([a for a in alumnos_data if not a['ya_calificado']]),
        'alumnos': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calificar_tarea(request):
    """Registrar calificación de tarea para un alumno"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    serializer = CalificarTareaSerializer(data=request.data)

    if serializer.is_valid():
        matriculacion = serializer.validated_data['matriculacion']
        tarea = serializer.validated_data['tarea']
        nota = serializer.validated_data['nota']
        observaciones = serializer.validated_data.get('observaciones', '')

        # Verificar que la tarea pertenece al profesor
        if tarea.profesor_materia.profesor != profesor:
            return Response(
                {'error': 'No tienes permisos para calificar esta tarea'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Crear o actualizar la nota
        nota_tarea, created = NotaTarea.objects.update_or_create(
            matriculacion=matriculacion,
            tarea=tarea,
            defaults={
                'nota': nota,
                'observaciones': observaciones
            }
        )

        # Registrar en bitácora
        accion = 'CREAR_NOTA_TAREA' if created else 'ACTUALIZAR_NOTA_TAREA'
        registrar_accion_bitacora(
            request.user,
            f'{accion}: {matriculacion.alumno.matricula} - {tarea.titulo}',
            request
        )

        return Response(
            NotaTareaSerializer(nota_tarea).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def nota_tarea_detail(request, pk):
    """Modificar calificación de tarea existente"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        nota_tarea = NotaTarea.objects.select_related(
            'tarea__profesor_materia__profesor',
            'matriculacion__alumno'
        ).get(pk=pk)
    except NotaTarea.DoesNotExist:
        return Response(
            {'error': 'Nota de tarea no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar permisos
    if nota_tarea.tarea.profesor_materia.profesor != profesor:
        return Response(
            {'error': 'No tienes permisos para modificar esta nota'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = NotaTareaSerializer(
        nota_tarea,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        nota_updated = serializer.save()

        registrar_accion_bitacora(
            request.user,
            f'MODIFICAR_NOTA_TAREA: {nota_updated.matriculacion.alumno.matricula}',
            request
        )

        return Response(NotaTareaSerializer(nota_updated).data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tareas_pendientes(request):
    """Tareas pendientes de calificación del profesor"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    from datetime import date

    # Obtener tareas del profesor que tienen entregas pendientes
    tareas = Tarea.objects.filter(
        profesor_materia__profesor=profesor
    ).select_related(
        'profesor_materia__materia',
        'trimestre'
    ).order_by('fecha_entrega')

    # Filtrar solo las que tienen pendientes
    tareas_con_pendientes = []
    for tarea in tareas:
        # Calcular total de entregas esperadas
        from academic.models import Horario, Matriculacion
        grupos_ids = Horario.objects.filter(
            profesor_materia=tarea.profesor_materia,
            trimestre=tarea.trimestre
        ).values_list('grupo_id', flat=True).distinct()

        total_esperadas = Matriculacion.objects.filter(
            alumno__grupo__in=grupos_ids,
            gestion=tarea.trimestre.gestion,
            activa=True
        ).count()

        calificadas = NotaTarea.objects.filter(tarea=tarea).count()

        if calificadas < total_esperadas:
            tareas_con_pendientes.append(tarea)

    serializer = TareasPendientesSerializer(tareas_con_pendientes, many=True)

    return Response({
        'total_tareas_pendientes': len(tareas_con_pendientes),
        'tareas': serializer.data
    })


# ==========================================
# GESTIÓN DE ASISTENCIAS
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_asistencias(request):
    """Historial de asistencias tomadas por el profesor"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    # Parámetros de consulta
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    materia_id = request.GET.get('materia', '')
    grupo_id = request.GET.get('grupo', '')

    from django.db.models import Count, Q as DQ
    from datetime import date, timedelta

    # Obtener fechas donde se tomó asistencia
    queryset = Asistencia.objects.filter(
        horario__profesor_materia__profesor=profesor
    ).values('horario', 'fecha').annotate(
        total_alumnos=Count('id'),
        presentes=Count('id', filter=DQ(estado='P')),
        faltas=Count('id', filter=DQ(estado='F')),
        tardanzas=Count('id', filter=DQ(estado='T')),
        justificadas=Count('id', filter=DQ(estado='J'))
    ).order_by('-fecha')

    # Aplicar filtros
    if fecha_desde:
        queryset = queryset.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        queryset = queryset.filter(fecha__lte=fecha_hasta)

    if materia_id:
        queryset = queryset.filter(horario__profesor_materia__materia_id=materia_id)

    if grupo_id:
        queryset = queryset.filter(horario__grupo_id=grupo_id)

    # Obtener objetos Horario con las estadísticas
    horarios_con_stats = []
    for item in queryset:
        try:
            from academic.models import Horario
            horario = Horario.objects.select_related(
                'profesor_materia__materia',
                'grupo', 'grupo__nivel'
            ).get(id=item['horario'])

            # Agregar estadísticas al objeto
            horario.fecha = item['fecha']
            horario.total_alumnos = item['total_alumnos']
            horario.presentes = item['presentes']
            horario.faltas = item['faltas']
            horario.tardanzas = item['tardanzas']
            horario.justificadas = item['justificadas']

            horarios_con_stats.append(horario)
        except:
            continue

    # Paginar
    paginator = Paginator(horarios_con_stats, page_size)
    page_obj = paginator.get_page(page)

    serializer = MisAsistenciasSerializer(page_obj.object_list, many=True)

    registrar_accion_bitacora(
        request.user,
        'VER_MIS_ASISTENCIAS',
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def tomar_asistencia(request):
    """Tomar asistencia para una clase específica"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    serializer = TomarAsistenciaSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        horario_id = serializer.validated_data['horario_id']
        fecha = serializer.validated_data['fecha']
        asistencias_data = serializer.validated_data['asistencias']

        from academic.models import Horario
        horario = Horario.objects.get(id=horario_id)

        # Procesar asistencias
        resultados = []
        errores = []

        for asistencia_data in asistencias_data:
            try:
                from academic.models import Matriculacion
                matriculacion = Matriculacion.objects.get(
                    id=asistencia_data['matriculacion_id']
                )

                # Verificar que el alumno pertenece al grupo correcto
                if matriculacion.alumno.grupo != horario.grupo:
                    errores.append({
                        'matriculacion_id': asistencia_data['matriculacion_id'],
                        'error': 'El alumno no pertenece a este grupo'
                    })
                    continue

                # Crear o actualizar asistencia
                asistencia, created = Asistencia.objects.update_or_create(
                    matriculacion=matriculacion,
                    horario=horario,
                    fecha=fecha,
                    defaults={
                        'estado': asistencia_data['estado']
                    }
                )

                resultados.append({
                    'matriculacion_id': matriculacion.id,
                    'alumno': f"{matriculacion.alumno.nombres} {matriculacion.alumno.apellidos}",
                    'estado': asistencia.estado,
                    'accion': 'creada' if created else 'actualizada'
                })

            except Exception as e:
                errores.append({
                    'matriculacion_id': asistencia_data.get('matriculacion_id'),
                    'error': str(e)
                })

        registrar_accion_bitacora(
            request.user,
            f'TOMAR_ASISTENCIA: {len(resultados)} registros - {fecha}',
            request
        )

        return Response({
            'exito': len(resultados),
            'errores': len(errores),
            'fecha': fecha,
            'horario': {
                'id': horario.id,
                'materia': horario.profesor_materia.materia.nombre,
                'grupo': f"{horario.grupo.nivel.numero}° {horario.grupo.letra}"
            },
            'resultados': resultados,
            'errores_detalle': errores
        })

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def asistencia_clase(request, horario_id):
    """Ver asistencia de una clase/horario específico"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    fecha = request.GET.get('fecha')
    if not fecha:
        from datetime import date
        fecha = date.today()
    else:
        from datetime import datetime
        try:
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Usar YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

    try:
        from academic.models import Horario
        horario = Horario.objects.select_related(
            'profesor_materia__materia',
            'grupo', 'grupo__nivel'
        ).get(
            pk=horario_id,
            profesor_materia__profesor=profesor
        )
    except Horario.DoesNotExist:
        return Response(
            {'error': 'Horario no encontrado o no tienes permisos para acceder'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener asistencias de esa fecha
    asistencias = Asistencia.objects.filter(
        horario=horario,
        fecha=fecha
    ).select_related('matriculacion__alumno')

    serializer = AsistenciaSerializer(asistencias, many=True)

    return Response({
        'horario': {
            'id': horario.id,
            'materia': horario.profesor_materia.materia.nombre,
            'grupo': f"{horario.grupo.nivel.numero}° {horario.grupo.letra}",
            'dia_semana': horario.dia_semana,
            'hora_inicio': horario.hora_inicio,
            'hora_fin': horario.hora_fin
        },
        'fecha': fecha,
        'total_registros': len(asistencias),
        'asistencias': serializer.data
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def asistencia_detail(request, pk):
    """Modificar registro de asistencia"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        asistencia = Asistencia.objects.select_related(
            'horario__profesor_materia__profesor',
            'matriculacion__alumno'
        ).get(pk=pk)
    except Asistencia.DoesNotExist:
        return Response(
            {'error': 'Registro de asistencia no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar permisos
    if asistencia.horario.profesor_materia.profesor != profesor:
        return Response(
            {'error': 'No tienes permisos para modificar este registro'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = AsistenciaSerializer(
        asistencia,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        asistencia_updated = serializer.save()

        registrar_accion_bitacora(
            request.user,
            f'MODIFICAR_ASISTENCIA: {asistencia_updated.matriculacion.alumno.matricula}',
            request
        )

        return Response(AsistenciaSerializer(asistencia_updated).data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_clase(request):
    """Lista de alumnos para tomar asistencia"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    horario_id = request.GET.get('horario_id')
    fecha = request.GET.get('fecha')

    if not horario_id:
        return Response(
            {'error': 'horario_id es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not fecha:
        from datetime import date
        fecha = date.today()
    else:
        from datetime import datetime
        try:
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Usar YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

    try:
        from academic.models import Horario
        horario = Horario.objects.select_related(
            'profesor_materia__materia',
            'grupo', 'grupo__nivel'
        ).get(
            pk=horario_id,
            profesor_materia__profesor=profesor
        )
    except Horario.DoesNotExist:
        return Response(
            {'error': 'Horario no encontrado o no tienes permisos'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener alumnos matriculados en el grupo
    from academic.models import Matriculacion
    matriculaciones = Matriculacion.objects.filter(
        alumno__grupo=horario.grupo,
        gestion=horario.trimestre.gestion,
        activa=True
    ).select_related(
        'alumno', 'alumno__usuario'
    ).order_by('alumno__nombres', 'alumno__apellidos')

    # Obtener asistencias ya registradas para esta fecha
    asistencias_existentes = Asistencia.objects.filter(
        horario=horario,
        fecha=fecha
    ).select_related('matriculacion')

    asistencias_dict = {
        asist.matriculacion.id: {
            'id': asist.id,
            'estado': asist.estado,
            'fecha_registro': asist.created_at
        }
        for asist in asistencias_existentes
    }

    # Construir lista de alumnos
    alumnos_data = []
    for matriculacion in matriculaciones:
        alumno = matriculacion.alumno

        alumno_data = {
            'id_matriculacion': matriculacion.id,
            'alumno_id': alumno.usuario.id,
            'matricula': alumno.matricula,
            'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
            'grupo_nombre': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}",
            'foto_url': None,  # Implementar si se tiene sistema de fotos
            'asistencia_actual': asistencias_dict.get(matriculacion.id)
        }
        alumnos_data.append(alumno_data)

    serializer = ListaClaseSerializer(alumnos_data, many=True)

    return Response({
        'horario': {
            'id': horario.id,
            'materia': horario.profesor_materia.materia.nombre,
            'grupo': f"{horario.grupo.nivel.numero}° {horario.grupo.letra}",
            'dia_semana': horario.dia_semana,
            'hora_inicio': horario.hora_inicio,
            'hora_fin': horario.hora_fin
        },
        'fecha': fecha,
        'total_alumnos': len(alumnos_data),
        'ya_registrados': len([a for a in alumnos_data if a['asistencia_actual']]),
        'alumnos': serializer.data
    })


# ==========================================
# GESTIÓN DE PARTICIPACIONES
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_participaciones(request):
    """Historial de participaciones registradas por el profesor"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    # Parámetros de consulta
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    materia_id = request.GET.get('materia', '')
    grupo_id = request.GET.get('grupo', '')

    # Obtener participaciones del profesor
    queryset = Participacion.objects.filter(
        horario__profesor_materia__profesor=profesor
    ).select_related(
        'matriculacion__alumno',
        'horario__profesor_materia__materia',
        'horario__grupo', 'horario__grupo__nivel'
    ).order_by('-fecha', '-created_at')

    # Aplicar filtros
    if fecha_desde:
        queryset = queryset.filter(fecha__gte=fecha_desde)

    if fecha_hasta:
        queryset = queryset.filter(fecha__lte=fecha_hasta)

    if materia_id:
        queryset = queryset.filter(horario__profesor_materia__materia_id=materia_id)

    if grupo_id:
        queryset = queryset.filter(horario__grupo_id=grupo_id)

    # Paginar
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)

    serializer = ParticipacionSerializer(page_obj.object_list, many=True)

    registrar_accion_bitacora(
        request.user,
        'VER_MIS_PARTICIPACIONES',
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_participacion(request):
    """Registrar participación de un alumno en clase"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    serializer = RegistrarParticipacionSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        matriculacion = serializer.validated_data['matriculacion']
        horario = serializer.validated_data['horario']
        fecha = serializer.validated_data['fecha']
        descripcion = serializer.validated_data['descripcion']
        valor = serializer.validated_data['valor']

        # Crear participación
        participacion = Participacion.objects.create(
            matriculacion=matriculacion,
            horario=horario,
            fecha=fecha,
            descripcion=descripcion,
            valor=valor
        )

        registrar_accion_bitacora(
            request.user,
            f'REGISTRAR_PARTICIPACION: {matriculacion.alumno.matricula} - {descripcion}',
            request
        )

        return Response(
            ParticipacionSerializer(participacion).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def participacion_detail(request, pk):
    """Modificar registro de participación"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        participacion = Participacion.objects.select_related(
            'horario__profesor_materia__profesor',
            'matriculacion__alumno'
        ).get(pk=pk)
    except Participacion.DoesNotExist:
        return Response(
            {'error': 'Participación no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar permisos
    if participacion.horario.profesor_materia.profesor != profesor:
        return Response(
            {'error': 'No tienes permisos para modificar esta participación'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = ParticipacionSerializer(
        participacion,
        data=request.data,
        partial=True
    )

    if serializer.is_valid():
        participacion_updated = serializer.save()

        registrar_accion_bitacora(
            request.user,
            f'MODIFICAR_PARTICIPACION: {participacion_updated.matriculacion.alumno.matricula}',
            request
        )

        return Response(ParticipacionSerializer(participacion_updated).data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def participaciones_clase(request):
    """Ver participaciones de una clase específica"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    horario_id = request.GET.get('horario_id')
    fecha = request.GET.get('fecha')

    if not horario_id:
        return Response(
            {'error': 'horario_id es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not fecha:
        from datetime import date
        fecha = date.today()
    else:
        from datetime import datetime
        try:
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Usar YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

    try:
        from academic.models import Horario
        horario = Horario.objects.select_related(
            'profesor_materia__materia',
            'grupo', 'grupo__nivel'
        ).get(
            pk=horario_id,
            profesor_materia__profesor=profesor
        )
    except Horario.DoesNotExist:
        return Response(
            {'error': 'Horario no encontrado o no tienes permisos'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Obtener participaciones de esa fecha
    participaciones = Participacion.objects.filter(
        horario=horario,
        fecha=fecha
    ).select_related('matriculacion__alumno').order_by('-valor', 'matriculacion__alumno__nombres')

    serializer = ParticipacionSerializer(participaciones, many=True)

    response_data = {
        'horario_id': horario.id,
        'fecha': fecha,
        'materia_nombre': horario.profesor_materia.materia.nombre,
        'grupo_nombre': f"{horario.grupo.nivel.numero}° {horario.grupo.letra}",
        'total_participaciones': participaciones.count(),
        'participaciones': serializer.data
    }

    return Response(response_data)


# ==========================================
# REPORTES Y ANÁLISIS
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_mis_clases(request):
    """Estadísticas generales de las clases del profesor"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    #from django.db.models import Avg, Count

    # Obtener trimestre actual o parámetro
    trimestre_id = request.GET.get('trimestre')
    if trimestre_id:
        try:
            trimestre = Trimestre.objects.get(id=trimestre_id)
        except Trimestre.DoesNotExist:
            return Response(
                {'error': 'Trimestre no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    else:
        # Usar trimestre de gestión activa
        gestion_activa = Gestion.objects.filter(activa=True).first()
        if not gestion_activa:
            return Response({'error': 'No hay gestión activa'}, status=400)

        from datetime import date
        hoy = date.today()
        trimestre = Trimestre.objects.filter(
            gestion=gestion_activa,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).first()

        if not trimestre:
            # Usar el primer trimestre de la gestión activa
            trimestre = Trimestre.objects.filter(gestion=gestion_activa).first()

    if not trimestre:
        return Response({'error': 'No hay trimestre disponible'}, status=400)

    # Estadísticas básicas
    total_examenes = Examen.objects.filter(
        profesor_materia__profesor=profesor,
        trimestre=trimestre
    ).count()

    total_tareas = Tarea.objects.filter(
        profesor_materia__profesor=profesor,
        trimestre=trimestre
    ).count()

    total_asistencias = Asistencia.objects.filter(
        horario__profesor_materia__profesor=profesor,
        horario__trimestre=trimestre
    ).values('fecha', 'horario').distinct().count()

    total_participaciones = Participacion.objects.filter(
        horario__profesor_materia__profesor=profesor,
        horario__trimestre=trimestre
    ).count()

    # Promedios
    promedio_examenes = NotaExamen.objects.filter(
        examen__profesor_materia__profesor=profesor,
        examen__trimestre=trimestre
    ).aggregate(promedio=Avg('nota'))['promedio']

    promedio_tareas = NotaTarea.objects.filter(
        tarea__profesor_materia__profesor=profesor,
        tarea__trimestre=trimestre
    ).aggregate(promedio=Avg('nota'))['promedio']

    # Promedio de asistencia
    from django.db.models import Q as DQ, Case, When, IntegerField
    asistencias_stats = Asistencia.objects.filter(
        horario__profesor_materia__profesor=profesor,
        horario__trimestre=trimestre
    ).aggregate(
        total=Count('id'),
        presentes=Count('id', filter=DQ(estado='P')),
        tardanzas=Count('id', filter=DQ(estado='T'))
    )

    porcentaje_asistencia = None
    if asistencias_stats['total'] > 0:
        efectivos = asistencias_stats['presentes'] + asistencias_stats['tardanzas']
        porcentaje_asistencia = (efectivos / asistencias_stats['total']) * 100

    # Promedio de participaciones
    participacion_promedio = Participacion.objects.filter(
        horario__profesor_materia__profesor=profesor,
        horario__trimestre=trimestre
    ).aggregate(promedio=Avg('valor'))['promedio']

    estadisticas = {
        'total_examenes': total_examenes,
        'total_tareas': total_tareas,
        'total_asistencias_tomadas': total_asistencias,
        'total_participaciones': total_participaciones,
        'promedio_examenes': promedio_examenes,
        'promedio_tareas': promedio_tareas,
        'porcentaje_asistencia_promedio': porcentaje_asistencia,
        'participacion_promedio': participacion_promedio
    }

    serializer = EstadisticasClaseSerializer(estadisticas)

    registrar_accion_bitacora(
        request.user,
        'VER_ESTADISTICAS_CLASES',
        request
    )

    return Response({
        'trimestre': {
            'id': trimestre.id,
            'nombre': trimestre.nombre,
            'gestion': trimestre.gestion.anio
        },
        'estadisticas': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_grupo(request, grupo_id):
    """Reporte completo de rendimiento de un grupo"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        from academic.models import Grupo
        grupo = Grupo.objects.select_related('nivel').get(pk=grupo_id)
    except Grupo.DoesNotExist:
        return Response(
            {'error': 'Grupo no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar que el profesor enseña a este grupo
    from academic.models import Horario
    horarios_profesor = Horario.objects.filter(
        profesor_materia__profesor=profesor,
        grupo=grupo
    ).exists()

    if not horarios_profesor:
        return Response(
            {'error': 'No tienes permisos para ver este grupo'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Información del grupo
    grupo_info = {
        'id': grupo.id,
        'nombre': f"{grupo.nivel.numero}° {grupo.letra}",
        'nivel': grupo.nivel.numero,
        'letra': grupo.letra,
        'capacidad_maxima': grupo.capacidad_maxima
    }

    # Obtener alumnos del grupo
    from academic.models import Matriculacion
    gestion_activa = Gestion.objects.filter(activa=True).first()

    matriculaciones = Matriculacion.objects.filter(
        alumno__grupo=grupo,
        gestion=gestion_activa,
        activa=True
    ).select_related('alumno')

    # Materias que imparte el profesor en este grupo
    materias_profesor = Horario.objects.filter(
        profesor_materia__profesor=profesor,
        grupo=grupo
    ).select_related('profesor_materia__materia').values(
        'profesor_materia__materia__id',
        'profesor_materia__materia__nombre',
        'profesor_materia__materia__codigo'
    ).distinct()

    # Estadísticas por alumno
    alumnos_rendimiento = []
    for matriculacion in matriculaciones:
        alumno = matriculacion.alumno

        # Promedios de exámenes del profesor
        promedio_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__profesor_materia__profesor=profesor
        ).aggregate(promedio=Avg('nota'))['promedio']

        # Promedios de tareas del profesor
        promedio_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__profesor_materia__profesor=profesor
        ).aggregate(promedio=Avg('nota'))['promedio']

        # Asistencia
        total_asistencias = Asistencia.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__profesor=profesor
        ).count()

        presentes = Asistencia.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__profesor=profesor,
            estado__in=['P', 'T']
        ).count()

        porcentaje_asistencia = None
        if total_asistencias > 0:
            porcentaje_asistencia = (presentes / total_asistencias) * 100

        # Participaciones
        participaciones = Participacion.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__profesor=profesor
        )

        total_participaciones = participaciones.count()
        promedio_participaciones = participaciones.aggregate(
            promedio=Avg('valor')
        )['promedio']

        alumno_data = {
            'id_alumno': alumno.usuario.id,
            'matricula': alumno.matricula,
            'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
            'promedio_examenes': promedio_examenes,
            'promedio_tareas': promedio_tareas,
            'porcentaje_asistencia': porcentaje_asistencia,
            'total_participaciones': total_participaciones,
            'promedio_participaciones': promedio_participaciones
        }
        alumnos_rendimiento.append(alumno_data)

    # Estadísticas generales del grupo
    #from django.db.models import Avg
    estadisticas_generales = {
        'total_alumnos': len(alumnos_rendimiento),
        'promedio_grupo_examenes': NotaExamen.objects.filter(
            matriculacion__alumno__grupo=grupo,
            examen__profesor_materia__profesor=profesor
        ).aggregate(promedio=Avg('nota'))['promedio'],
        'promedio_grupo_tareas': NotaTarea.objects.filter(
            matriculacion__alumno__grupo=grupo,
            tarea__profesor_materia__profesor=profesor
        ).aggregate(promedio=Avg('nota'))['promedio']
    }

    reporte_data = {
        'grupo_info': grupo_info,
        'estadisticas_generales': estadisticas_generales,
        'alumnos_rendimiento': alumnos_rendimiento,
        'materias_impartidas': list(materias_profesor)
    }

    serializer = ReporteGrupoSerializer(reporte_data)

    registrar_accion_bitacora(
        request.user,
        f'REPORTE_GRUPO: {grupo.nivel.numero}°{grupo.letra}',
        request
    )

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_alumno(request, alumno_id):
    """Reporte individual de un alumno en materias del profesor"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        from authentication.models import Alumno
        alumno = Alumno.objects.select_related('usuario', 'grupo', 'grupo__nivel').get(
            usuario_id=alumno_id
        )
    except Alumno.DoesNotExist:
        return Response(
            {'error': 'Alumno no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar que el profesor enseña a este alumno
    from academic.models import Horario
    horarios_profesor = Horario.objects.filter(
        profesor_materia__profesor=profesor,
        grupo=alumno.grupo
    ).exists()

    if not horarios_profesor:
        return Response(
            {'error': 'No tienes permisos para ver este alumno'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Información del alumno
    alumno_info = {
        'id': alumno.usuario.id,
        'matricula': alumno.matricula,
        'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
        'grupo': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}",
        'email': alumno.usuario.email
    }

    # Obtener matriculación activa
    from academic.models import Matriculacion
    gestion_activa = Gestion.objects.filter(activa=True).first()

    try:
        matriculacion = Matriculacion.objects.get(
            alumno=alumno,
            gestion=gestion_activa,
            activa=True
        )
    except Matriculacion.DoesNotExist:
        return Response(
            {'error': 'El alumno no está matriculado en la gestión activa'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Materias del profesor con este alumno
    materias_profesor = []
    horarios = Horario.objects.filter(
        profesor_materia__profesor=profesor,
        grupo=alumno.grupo
    ).select_related('profesor_materia__materia')

    resumen_total = {
        'total_examenes': 0,
        'total_tareas': 0,
        'promedio_general_examenes': 0,
        'promedio_general_tareas': 0,
        'total_asistencias': 0,
        'porcentaje_asistencia_general': 0,
        'total_participaciones': 0
    }

    for horario in horarios:
        materia = horario.profesor_materia.materia

        # Exámenes
        notas_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__profesor_materia__materia=materia
        )

        # Tareas
        notas_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__profesor_materia__materia=materia
        )

        # Asistencias
        asistencias = Asistencia.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__materia=materia
        )

        presentes = asistencias.filter(estado__in=['P', 'T']).count()
        total_asist = asistencias.count()
        porcentaje_asist = (presentes / total_asist * 100) if total_asist > 0 else 0

        # Participaciones
        participaciones = Participacion.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__materia=materia
        )

        materia_data = {
            'codigo': materia.codigo,
            'nombre': materia.nombre,
            'notas_examenes': [n.nota for n in notas_examenes],
            'promedio_examenes': notas_examenes.aggregate(Avg('nota'))['nota__avg'],
            'notas_tareas': [n.nota for n in notas_tareas],
            'promedio_tareas': notas_tareas.aggregate(Avg('nota'))['nota__avg'],
            'total_asistencias': total_asist,
            'porcentaje_asistencia': porcentaje_asist,
            'total_participaciones': participaciones.count(),
            'promedio_participaciones': participaciones.aggregate(Avg('valor'))['valor__avg']
        }
        materias_profesor.append(materia_data)

    # Calcular resumen general
    todas_notas_examenes = NotaExamen.objects.filter(
        matriculacion=matriculacion,
        examen__profesor_materia__profesor=profesor
    )

    todas_notas_tareas = NotaTarea.objects.filter(
        matriculacion=matriculacion,
        tarea__profesor_materia__profesor=profesor
    )

    todas_asistencias = Asistencia.objects.filter(
        matriculacion=matriculacion,
        horario__profesor_materia__profesor=profesor
    )

    todas_participaciones = Participacion.objects.filter(
        matriculacion=matriculacion,
        horario__profesor_materia__profesor=profesor
    )

    presentes_total = todas_asistencias.filter(estado__in=['P', 'T']).count()

    resumen_rendimiento = {
        'total_examenes': todas_notas_examenes.count(),
        'total_tareas': todas_notas_tareas.count(),
        'promedio_general_examenes': todas_notas_examenes.aggregate(Avg('nota'))['nota__avg'],
        'promedio_general_tareas': todas_notas_tareas.aggregate(Avg('nota'))['nota__avg'],
        'total_asistencias': todas_asistencias.count(),
        'porcentaje_asistencia_general': (
                    presentes_total / todas_asistencias.count() * 100) if todas_asistencias.count() > 0 else 0,
        'total_participaciones': todas_participaciones.count(),
        'promedio_participaciones': todas_participaciones.aggregate(Avg('valor'))['valor__avg']
    }

    reporte_data = {
        'alumno_info': alumno_info,
        'materias_profesor': materias_profesor,
        'resumen_rendimiento': resumen_rendimiento
    }

    serializer = ReporteAlumnoSerializer(reporte_data)

    registrar_accion_bitacora(
        request.user,
        f'REPORTE_ALUMNO: {alumno.matricula}',
        request
    )

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reporte_materia(request, materia_id):
    """Análisis de rendimiento por materia"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    try:
        from academic.models import Materia
        materia = Materia.objects.get(pk=materia_id)
    except Materia.DoesNotExist:
        return Response(
            {'error': 'Materia no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar que el profesor enseña esta materia
    from academic.models import ProfesorMateria
    profesor_materia = ProfesorMateria.objects.filter(
        profesor=profesor,
        materia=materia
    ).first()

    if not profesor_materia:
        return Response(
            {'error': 'No tienes permisos para ver esta materia'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Información de la materia
    materia_info = {
        'id': materia.id,
        'codigo': materia.codigo,
        'nombre': materia.nombre,
        'horas_semanales': materia.horas_semanales
    }

    # Grupos donde se enseña
    from academic.models import Horario
    horarios = Horario.objects.filter(
        profesor_materia=profesor_materia
    ).select_related('grupo', 'grupo__nivel', 'trimestre')

    grupos_atendidos = []
    for horario in horarios:
        grupo_data = {
            'id': horario.grupo.id,
            'nombre': f"{horario.grupo.nivel.numero}° {horario.grupo.letra}",
            'trimestre': horario.trimestre.nombre,
            'dia_semana': horario.dia_semana,
            'hora_inicio': horario.hora_inicio,
            'hora_fin': horario.hora_fin
        }
        grupos_atendidos.append(grupo_data)

    # Estadísticas generales
    examenes = Examen.objects.filter(profesor_materia=profesor_materia)
    tareas = Tarea.objects.filter(profesor_materia=profesor_materia)
    notas_examenes = NotaExamen.objects.filter(examen__profesor_materia=profesor_materia)
    notas_tareas = NotaTarea.objects.filter(tarea__profesor_materia=profesor_materia)

    estadisticas_generales = {
        'total_examenes': examenes.count(),
        'total_tareas': tareas.count(),
        'total_notas_examenes': notas_examenes.count(),
        'total_notas_tareas': notas_tareas.count(),
        'promedio_examenes': notas_examenes.aggregate(Avg('nota'))['nota__avg'],
        'promedio_tareas': notas_tareas.aggregate(Avg('nota'))['nota__avg']
    }

    # Distribución de notas (rangos)
    distribucion_examenes = {
        '0-50': notas_examenes.filter(nota__lt=50).count(),
        '50-70': notas_examenes.filter(nota__gte=50, nota__lt=70).count(),
        '70-85': notas_examenes.filter(nota__gte=70, nota__lt=85).count(),
        '85-100': notas_examenes.filter(nota__gte=85).count()
    }

    distribucion_tareas = {
        '0-50': notas_tareas.filter(nota__lt=50).count(),
        '50-70': notas_tareas.filter(nota__gte=50, nota__lt=70).count(),
        '70-85': notas_tareas.filter(nota__gte=70, nota__lt=85).count(),
        '85-100': notas_tareas.filter(nota__gte=85).count()
    }

    distribucion_notas = {
        'examenes': distribucion_examenes,
        'tareas': distribucion_tareas
    }

    reporte_data = {
        'materia_info': materia_info,
        'grupos_atendidos': grupos_atendidos,
        'estadisticas_generales': estadisticas_generales,
        'distribucion_notas': distribucion_notas
    }

    serializer = ReporteMateriaSerializer(reporte_data)

    registrar_accion_bitacora(
        request.user,
        f'REPORTE_MATERIA: {materia.codigo}',
        request
    )

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def promedio_grupo(request, grupo_id):
    """Cálculo de promedios por grupo y materia"""
    profesor, error_response = validar_profesor_autenticado(request)
    if error_response:
        return error_response

    materia_id = request.GET.get('materia')
    if not materia_id:
        return Response(
            {'error': 'materia_id es requerido como parámetro'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from academic.models import Grupo, Materia
        grupo = Grupo.objects.select_related('nivel').get(pk=grupo_id)
        materia = Materia.objects.get(pk=materia_id)
    except (Grupo.DoesNotExist, Materia.DoesNotExist):
        return Response(
            {'error': 'Grupo o materia no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Verificar permisos
    from academic.models import ProfesorMateria, Horario
    profesor_materia = ProfesorMateria.objects.filter(
        profesor=profesor,
        materia=materia
    ).first()

    if not profesor_materia:
        return Response(
            {'error': 'No enseñas esta materia'},
            status=status.HTTP_403_FORBIDDEN
        )

    horario_existe = Horario.objects.filter(
        profesor_materia=profesor_materia,
        grupo=grupo
    ).exists()

    if not horario_existe:
        return Response(
            {'error': 'No enseñas esta materia a este grupo'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Información básica
    grupo_info = {
        'id': grupo.id,
        'nombre': f"{grupo.nivel.numero}° {grupo.letra}"
    }

    materia_info = {
        'id': materia.id,
        'codigo': materia.codigo,
        'nombre': materia.nombre
    }

    # Obtener alumnos del grupo
    from academic.models import Matriculacion
    gestion_activa = Gestion.objects.filter(activa=True).first()

    matriculaciones = Matriculacion.objects.filter(
        alumno__grupo=grupo,
        gestion=gestion_activa,
        activa=True
    ).select_related('alumno')

    # Calcular estadísticas y detalles por alumno
    alumnos_detalle = []
    promedio_total_examenes = 0
    promedio_total_tareas = 0
    contador_examenes = 0
    contador_tareas = 0

    for matriculacion in matriculaciones:
        alumno = matriculacion.alumno

        # Notas de exámenes
        notas_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__profesor_materia=profesor_materia
        )

        # Notas de tareas
        notas_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__profesor_materia=profesor_materia
        )

        promedio_examenes = notas_examenes.aggregate(Avg('nota'))['nota__avg']
        promedio_tareas = notas_tareas.aggregate(Avg('nota'))['nota__avg']

        # Acumular para promedio general
        if promedio_examenes:
            promedio_total_examenes += promedio_examenes
            contador_examenes += 1

        if promedio_tareas:
            promedio_total_tareas += promedio_tareas
            contador_tareas += 1

        alumno_data = {
            'id': alumno.usuario.id,
            'matricula': alumno.matricula,
            'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
            'total_examenes': notas_examenes.count(),
            'promedio_examenes': promedio_examenes,
            'total_tareas': notas_tareas.count(),
            'promedio_tareas': promedio_tareas,
            'promedio_general': None
        }

        # Calcular promedio general (si tiene ambos)
        if promedio_examenes and promedio_tareas:
            alumno_data['promedio_general'] = (promedio_examenes + promedio_tareas) / 2
        elif promedio_examenes:
            alumno_data['promedio_general'] = promedio_examenes
        elif promedio_tareas:
            alumno_data['promedio_general'] = promedio_tareas

        alumnos_detalle.append(alumno_data)

    # Estadísticas generales del grupo
    promedio_grupo_examenes = promedio_total_examenes / contador_examenes if contador_examenes > 0 else None
    promedio_grupo_tareas = promedio_total_tareas / contador_tareas if contador_tareas > 0 else None

    # Calcular promedio general del grupo
    promedio_general_grupo = None
    if promedio_grupo_examenes and promedio_grupo_tareas:
        promedio_general_grupo = (promedio_grupo_examenes + promedio_grupo_tareas) / 2
    elif promedio_grupo_examenes:
        promedio_general_grupo = promedio_grupo_examenes
    elif promedio_grupo_tareas:
        promedio_general_grupo = promedio_grupo_tareas

    # Contar distribución de rendimiento
    alumnos_con_promedio = [a for a in alumnos_detalle if a['promedio_general']]

    excelente = len([a for a in alumnos_con_promedio if a['promedio_general'] >= 85])
    bueno = len([a for a in alumnos_con_promedio if 70 <= a['promedio_general'] < 85])
    regular = len([a for a in alumnos_con_promedio if 50 <= a['promedio_general'] < 70])
    deficiente = len([a for a in alumnos_con_promedio if a['promedio_general'] < 50])

    estadisticas = {
        'total_alumnos': len(alumnos_detalle),
        'promedio_grupo_examenes': promedio_grupo_examenes,
        'promedio_grupo_tareas': promedio_grupo_tareas,
        'promedio_general_grupo': promedio_general_grupo,
        'distribucion_rendimiento': {
            'excelente': excelente,  # 85-100
            'bueno': bueno,  # 70-84
            'regular': regular,  # 50-69
            'deficiente': deficiente  # 0-49
        }
    }

    promedio_data = {
        'grupo_info': grupo_info,
        'materia_info': materia_info,
        'estadisticas': estadisticas,
        'alumnos_detalle': alumnos_detalle
    }

    serializer = PromedioGrupoSerializer(promedio_data)

    registrar_accion_bitacora(
        request.user,
        f'PROMEDIO_GRUPO: {grupo.nivel.numero}°{grupo.letra} - {materia.codigo}',
        request
    )

    return Response(serializer.data)

