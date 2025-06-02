import json
from datetime import date
from django.db.models import Q
from rest_framework import status
from django.db.models import Count
from shared.permissions import IsDirector
from django.core.paginator import Paginator
from rest_framework.response import Response
from ..models import Profesor, Alumno, Usuario
from audit.utils import registrar_accion_bitacora
from academic.models import Materia, Aula, Gestion, Trimestre, Horario, Matriculacion
from rest_framework.decorators import api_view, permission_classes
from ..serializers.director_serializers import (
    ProfesorSerializer, ProfesorListSerializer,
    AlumnoSerializer, AlumnoListSerializer
)


@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def profesor_list_create(request):
    """
    GET: Listar profesores con paginación y filtros
    POST: Crear nuevo profesor
    """

    if request.method == 'POST':
        print(f"\n{'=' * 50}")
        print(f"🔍 PAYLOAD RECIBIDO - Método: {request.method}")
        print(f"📍 Endpoint: {request.path}")
        print(f"📦 Data recibida:")
        print(json.dumps(request.data, indent=2, ensure_ascii=False, default=str))
        print(f"{'=' * 50}\n")

    if request.method == 'GET':
        # Parámetros de consulta
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        search = request.GET.get('search', '')
        especialidad = request.GET.get('especialidad', '')
        activo = request.GET.get('activo', '')

        # Filtrar profesores
        queryset = Profesor.objects.all().select_related('usuario').order_by('-created_at')

        if search:
            queryset = queryset.filter(
                Q(nombres__icontains=search) |
                Q(apellidos__icontains=search) |
                Q(usuario__email__icontains=search) |
                Q(cedula_identidad__icontains=search)
            )

        if especialidad:
            queryset = queryset.filter(especialidad__icontains=especialidad)

        if activo:
            activo_bool = activo.lower() == 'true'
            queryset = queryset.filter(usuario__activo=activo_bool)

        # Paginar
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        registrar_accion_bitacora(
            request.user,
            f'LISTAR_PROFESORES',
            request
        )

        # Serializar
        serializer = ProfesorListSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = ProfesorSerializer(data=request.data)
        if serializer.is_valid():
            print(f"✅ Datos validados correctamente para creación")
            try:
                profesor = serializer.save()
                print(f"✅ Profesor creado exitosamente: {profesor.nombres} {profesor.apellidos}")

                # Registrar en bitácora
                registrar_accion_bitacora(
                    request.user,
                    f'CREAR_PROFESOR',
                    request
                )

                return Response(
                    ProfesorSerializer(profesor).data,
                    status=status.HTTP_201_CREATED
                )

            except Exception as e:
                print(f"❌ Error al crear profesor: {str(e)}")
                return Response(
                    {'error': f'Error al crear: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        else:
            print(f"❌ Errores de validación en creación:")
            print(json.dumps(serializer.errors, indent=2, ensure_ascii=False))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def profesor_detail(request, pk):
    """
    GET: Ver detalle de profesor
    PUT: Actualizar profesor completo
    PATCH: Actualizar profesor parcial
    DELETE: Eliminar profesor
    """
    if request.method in ['PUT', 'PATCH', 'POST']:
        print(f"\n{'=' * 50}")
        print(f"🔍 PAYLOAD RECIBIDO - Método: {request.method}")
        print(f"📍 Endpoint: {request.path}")
        print(f"📋 Content-Type: {request.content_type}")
        print(f"📦 Data recibida:")
        print(json.dumps(request.data, indent=2, ensure_ascii=False, default=str))
        print(f"{'=' * 50}\n")

    try:
        profesor = Profesor.objects.select_related('usuario').get(pk=pk)
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = ProfesorSerializer(profesor)
        return Response(serializer.data)


    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ProfesorSerializer(profesor, data=request.data, partial=partial)

        if serializer.is_valid():
            print(f"✅ Datos validados correctamente")
            try:
                profesor_updated = serializer.save()
                print(f"✅ Profesor actualizado exitosamente")

                # Registrar en bitácora
                registrar_accion_bitacora(
                    request.user,
                    f'ACTUALIZAR_PROFESOR: {profesor_updated.nombres} {profesor_updated.apellidos}',
                    request
                )

                return Response(ProfesorSerializer(profesor_updated).data)

            except Exception as e:
                print(f"❌ Error al guardar: {str(e)}")
                return Response(
                    {'error': f'Error al guardar: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR

                )

        else:
            print(f"❌ Errores de validación:")
            print(json.dumps(serializer.errors, indent=2, ensure_ascii=False))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        nombre_completo = f"{profesor.nombres} {profesor.apellidos}"
        email = profesor.usuario.email

        # Eliminar profesor (cascade eliminará usuario)
        profesor.delete()

        # Registrar en bitácora
        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_PROFESOR',
            request
        )

        return Response(
            {'message': 'Profesor eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )


# Vistas CRUD para Alumnos
@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def alumno_list_create(request):
    """
    GET: Listar alumnos con paginación y filtros
    POST: Crear nuevo alumno
    """
    if request.method == 'GET':
        # Parámetros de consulta
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        search = request.GET.get('search', '')
        grupo = request.GET.get('grupo', '')
        nivel = request.GET.get('nivel', '')
        activo = request.GET.get('activo', '')

        # Filtrar alumnos
        queryset = Alumno.objects.all().select_related(
            'usuario', 'grupo', 'grupo__nivel'
        ).order_by('-created_at')

        if search:
            queryset = queryset.filter(
                Q(nombres__icontains=search) |
                Q(apellidos__icontains=search) |
                Q(usuario__email__icontains=search) |
                Q(matricula__icontains=search)
            )

        if grupo:
            queryset = queryset.filter(grupo_id=grupo)

        if nivel:
            queryset = queryset.filter(grupo__nivel__numero=nivel)

        if activo:
            activo_bool = activo.lower() == 'true'
            queryset = queryset.filter(usuario__activo=activo_bool)

        # Paginar
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Serializar
        serializer = AlumnoListSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = AlumnoSerializer(data=request.data)
        if serializer.is_valid():
            alumno = serializer.save()

            # Registrar en bitácora
            registrar_accion_bitacora(
                request.user,
                f'CREAR_ALUMNO: {alumno.matricula}',
                request
            )

            return Response(
                AlumnoSerializer(alumno).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def alumno_detail(request, pk):
    """
    GET: Ver detalle de alumno
    PUT: Actualizar alumno completo
    PATCH: Actualizar alumno parcial
    DELETE: Eliminar alumno
    """
    try:
        alumno = Alumno.objects.select_related(
            'usuario', 'grupo', 'grupo__nivel'
        ).get(pk=pk)
    except Alumno.DoesNotExist:
        return Response(
            {'error': 'Alumno no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = AlumnoSerializer(alumno)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = AlumnoSerializer(alumno, data=request.data, partial=partial)

        if serializer.is_valid():
            alumno_updated = serializer.save()

            # Registrar en bitácora
            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_ALUMNO',
                request
            )

            return Response(AlumnoSerializer(alumno_updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        nombre_completo = f"{alumno.nombres} {alumno.apellidos}"
        matricula = alumno.matricula
        email = alumno.usuario.email

        # Eliminar alumno (cascade eliminará usuario)
        alumno.delete()

        # Registrar en bitácora
        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_ALUMNO: {matricula}',
            request
        )

        return Response(
            {'message': 'Alumno eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )


# Vista de estadísticas básicas
@api_view(['GET'])
@permission_classes([IsDirector])
def dashboard_director(request):
    """Dashboard completo para directores"""
    # Estadísticas básicas (ya existentes)
    stats = {
        'total_profesores': Profesor.objects.count(),
        'profesores_activos': Profesor.objects.filter(usuario__activo=True).count(),
        'total_alumnos': Alumno.objects.count(),
        'alumnos_activos': Alumno.objects.filter(usuario__activo=True).count(),
        'total_materias': Materia.objects.count(),
        'total_aulas': Aula.objects.count(),
        'usuarios_total': Usuario.objects.count(),
        'usuarios_activos': Usuario.objects.filter(activo=True).count(),
    }

    # ===== NUEVAS ESTADÍSTICAS =====

    # Gestión académica actual
    gestion_activa = Gestion.objects.filter(activa=True).first()
    if gestion_activa:
        stats.update({
            'gestion_activa': {
                'id': gestion_activa.id,
                'anio': gestion_activa.anio,
                'nombre': gestion_activa.nombre
            },
            'total_matriculaciones': Matriculacion.objects.filter(
                gestion=gestion_activa, activa=True
            ).count(),
            'trimestres_gestion': Trimestre.objects.filter(
                gestion=gestion_activa
            ).count()
        })

        # Trimestre actual (basado en fecha)
        hoy = date.today()
        trimestre_actual = Trimestre.objects.filter(
            gestion=gestion_activa,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).first()

        if trimestre_actual:
            stats['trimestre_actual'] = {
                'id': trimestre_actual.id,
                'numero': trimestre_actual.numero,
                'nombre': trimestre_actual.nombre
            }

            # Horarios del trimestre actual
            stats['horarios_activos'] = Horario.objects.filter(
                trimestre=trimestre_actual
            ).count()
    else:
        stats.update({
            'gestion_activa': None,
            'total_matriculaciones': 0,
            'trimestres_gestion': 0,
            'trimestre_actual': None,
            'horarios_activos': 0
        })

    # Estadísticas adicionales
    stats.update({
        'materias_sin_profesor': Materia.objects.filter(
            profesormateria__isnull=True
        ).count(),
        'profesores_sin_materia': Profesor.objects.filter(
            profesormateria__isnull=True
        ).count(),
        'aulas_sin_horario': Aula.objects.filter(
            horario__isnull=True
        ).count() if gestion_activa else Aula.objects.count(),
        'alumnos_sin_matricular': Alumno.objects.filter(
            matriculacion__isnull=True
        ).count() if gestion_activa else Alumno.objects.count()
    })

    # Datos para gráficos
    ultimos_profesores = Profesor.objects.select_related('usuario').order_by('-created_at')[:5]
    ultimos_alumnos = Alumno.objects.select_related('usuario').order_by('-created_at')[:5]

    # Distribución de alumnos por nivel
    distribucion_niveles = Alumno.objects.values(
        'grupo__nivel__numero', 'grupo__nivel__nombre'
    ).annotate(
        total_alumnos=Count('id')
    ).order_by('grupo__nivel__numero')

    return Response({
        'estadisticas': stats,
        'ultimos_profesores': ProfesorListSerializer(ultimos_profesores, many=True).data,
        'ultimos_alumnos': AlumnoListSerializer(ultimos_alumnos, many=True).data,
        'distribucion_por_nivel': list(distribucion_niveles),
        'alertas': [
            f"{stats['materias_sin_profesor']} materias sin profesor asignado" if stats[
                                                                                      'materias_sin_profesor'] > 0 else None,
            f"{stats['profesores_sin_materia']} profesores sin materias asignadas" if stats[
                                                                                          'profesores_sin_materia'] > 0 else None,
            f"{stats['alumnos_sin_matricular']} alumnos sin matricular" if stats[
                                                                               'alumnos_sin_matricular'] > 0 else None,
            "No hay gestión académica activa" if not gestion_activa else None
        ]
    })
