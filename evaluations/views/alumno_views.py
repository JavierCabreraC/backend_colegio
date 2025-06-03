from rest_framework import status
from datetime import datetime, date

from authentication.models import Alumno
from shared.permissions import IsAlumno
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from academic.models import Matriculacion, Trimestre, Gestion, Materia
from ..models import NotaExamen, NotaTarea, Asistencia, EstadoAsistencia, Participacion, HistoricoTrimestral
from ..serializers import (
    NotaExamenSerializer, NotaTareaSerializer, AsistenciaSerializer,
    PromedioTrimestreSerializer, ResumenAsistenciaSerializer
)
from ..serializers.alumno_serializers import (
    ParticipacionAlumnoSerializer, EstadisticasParticipacionSerializer,
    DashboardRendimientoSerializer, RendimientoMateriaSerializer,
    TendenciaTrimestreSerializer, AlertaRendimientoSerializer
)
from django.db.models import Avg, Max


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mis_notas(request):
    """
    Endpoint para obtener todas las notas del alumno
    Query params opcionales:
    - trimestre: ID del trimestre
    - materia: ID de la materia
    - tipo: 'examenes' o 'tareas'
    """
    try:
        alumno = request.user.alumno

        # Obtener matriculación activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=gestion_activa,
                activa=True
            )
        except (Gestion.DoesNotExist, Matriculacion.DoesNotExist):
            return Response(
                {'error': 'No hay matriculación activa para el alumno'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filtros opcionales
        trimestre_id = request.query_params.get('trimestre')
        materia_id = request.query_params.get('materia')
        tipo = request.query_params.get('tipo')

        # Base queryset para notas de exámenes
        notas_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion
        ).select_related('examen__profesor_materia__materia', 'examen__profesor_materia__profesor')

        # Base queryset para notas de tareas
        notas_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion
        ).select_related('tarea__profesor_materia__materia', 'tarea__profesor_materia__profesor')

        # Aplicar filtros
        if trimestre_id:
            notas_examenes = notas_examenes.filter(examen__trimestre_id=trimestre_id)
            notas_tareas = notas_tareas.filter(tarea__trimestre_id=trimestre_id)

        if materia_id:
            notas_examenes = notas_examenes.filter(examen__profesor_materia__materia_id=materia_id)
            notas_tareas = notas_tareas.filter(tarea__profesor_materia__materia_id=materia_id)

        response_data = {}

        if not tipo or tipo == 'examenes':
            examenes_serializer = NotaExamenSerializer(notas_examenes, many=True)
            response_data['notas_examenes'] = examenes_serializer.data

        if not tipo or tipo == 'tareas':
            tareas_serializer = NotaTareaSerializer(notas_tareas, many=True)
            response_data['notas_tareas'] = tareas_serializer.data

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mis_notas_promedio_trimestral(request):
    """
    Endpoint para obtener promedios trimestrales por materia
    Query params opcionales:
    - trimestre: ID del trimestre (por defecto el activo)
    """
    try:
        alumno = request.user.alumno

        # Obtener trimestre
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
            try:
                gestion_activa = Gestion.objects.get(activa=True)
                trimestre = Trimestre.objects.filter(
                    gestion=gestion_activa,
                    fecha_inicio__lte=date.today(),
                    fecha_fin__gte=date.today()
                ).first()

                if not trimestre:
                    trimestre = Trimestre.objects.filter(
                        gestion=gestion_activa
                    ).order_by('-numero').first()

            except Gestion.DoesNotExist:
                return Response(
                    {'error': 'No hay gestión académica activa'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Obtener matriculación
        try:
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=trimestre.gestion,
                activa=True
            )
        except Matriculacion.DoesNotExist:
            return Response(
                {'error': 'No hay matriculación para este período'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calcular promedios por materia
        materias_con_notas = set()

        # Obtener materias con exámenes
        materias_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__trimestre=trimestre
        ).values_list('examen__profesor_materia__materia', flat=True).distinct()

        # Obtener materias con tareas
        materias_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__trimestre=trimestre
        ).values_list('tarea__profesor_materia__materia', flat=True).distinct()

        materias_con_notas.update(materias_examenes)
        materias_con_notas.update(materias_tareas)

        promedios = []

        for materia_id in materias_con_notas:
            materia = Materia.objects.get(id=materia_id)

            # Promedio exámenes
            avg_examenes = NotaExamen.objects.filter(
                matriculacion=matriculacion,
                examen__trimestre=trimestre,
                examen__profesor_materia__materia=materia
            ).aggregate(promedio=Avg('nota'))['promedio']

            # Promedio tareas
            avg_tareas = NotaTarea.objects.filter(
                matriculacion=matriculacion,
                tarea__trimestre=trimestre,
                tarea__profesor_materia__materia=materia
            ).aggregate(promedio=Avg('nota'))['promedio']

            # Conteos
            total_examenes = NotaExamen.objects.filter(
                matriculacion=matriculacion,
                examen__trimestre=trimestre,
                examen__profesor_materia__materia=materia
            ).count()

            total_tareas = NotaTarea.objects.filter(
                matriculacion=matriculacion,
                tarea__trimestre=trimestre,
                tarea__profesor_materia__materia=materia
            ).count()

            # Promedio general (60% exámenes, 40% tareas)
            promedio_general = None
            if avg_examenes and avg_tareas:
                promedio_general = round(avg_examenes * 0.6 + avg_tareas * 0.4, 2)
            elif avg_examenes:
                promedio_general = avg_examenes
            elif avg_tareas:
                promedio_general = avg_tareas

            promedios.append({
                'materia': materia.nombre,
                'promedio_examenes': avg_examenes,
                'promedio_tareas': avg_tareas,
                'promedio_general': promedio_general,
                'total_examenes': total_examenes,
                'total_tareas': total_tareas
            })

        serializer = PromedioTrimestreSerializer(promedios, many=True)

        return Response({
            'promedios': serializer.data,
            'trimestre': {
                'id': trimestre.id,
                'nombre': trimestre.nombre,
                'gestion': trimestre.gestion.nombre
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mis_asistencias(request):
    """
    Endpoint para obtener asistencias del alumno
    Query params opcionales:
    - fecha_inicio: YYYY-MM-DD
    - fecha_fin: YYYY-MM-DD
    - materia: ID de la materia
    """
    try:
        alumno = request.user.alumno

        # Obtener matriculación activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=gestion_activa,
                activa=True
            )
        except (Gestion.DoesNotExist, Matriculacion.DoesNotExist):
            return Response(
                {'error': 'No hay matriculación activa para el alumno'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Base queryset
        asistencias = Asistencia.objects.filter(
            matriculacion=matriculacion
        ).select_related(
            'horario__profesor_materia__materia',
            'horario__profesor_materia__profesor'
        ).order_by('-fecha', 'horario__hora_inicio')

        # Filtros opcionales
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        materia_id = request.query_params.get('materia')

        if fecha_inicio:
            try:
                fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                asistencias = asistencias.filter(fecha__gte=fecha_inicio_obj)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_inicio inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if fecha_fin:
            try:
                fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                asistencias = asistencias.filter(fecha__lte=fecha_fin_obj)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_fin inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if materia_id:
            asistencias = asistencias.filter(
                horario__profesor_materia__materia_id=materia_id
            )

        serializer = AsistenciaSerializer(asistencias, many=True)

        return Response({
            'asistencias': serializer.data,
            'total_registros': asistencias.count()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mis_asistencias_resumen(request):
    """
    Endpoint para obtener resumen estadístico de asistencias por materia
    """
    try:
        alumno = request.user.alumno

        # Obtener matriculación activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=gestion_activa,
                activa=True
            )
        except (Gestion.DoesNotExist, Matriculacion.DoesNotExist):
            return Response(
                {'error': 'No hay matriculación activa para el alumno'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener materias con asistencias registradas
        materias_ids = Asistencia.objects.filter(
            matriculacion=matriculacion
        ).values_list(
            'horario__profesor_materia__materia', flat=True
        ).distinct()

        resumenes = []

        for materia_id in materias_ids:
            materia = Materia.objects.get(id=materia_id)

            # Contar asistencias por estado
            asistencias_materia = Asistencia.objects.filter(
                matriculacion=matriculacion,
                horario__profesor_materia__materia=materia
            )

            total_clases = asistencias_materia.count()
            presentes = asistencias_materia.filter(estado=EstadoAsistencia.PRESENTE).count()
            faltas = asistencias_materia.filter(estado=EstadoAsistencia.FALTA).count()
            tardanzas = asistencias_materia.filter(estado=EstadoAsistencia.TARDANZA).count()
            justificadas = asistencias_materia.filter(estado=EstadoAsistencia.JUSTIFICADA).count()

            # Calcular porcentaje (presente + tardanza = asistió)
            asistencias_efectivas = presentes + tardanzas
            porcentaje_asistencia = round(
                (asistencias_efectivas / total_clases * 100) if total_clases > 0 else 0, 2
            )

            resumenes.append({
                'materia': materia.nombre,
                'total_clases': total_clases,
                'presentes': presentes,
                'faltas': faltas,
                'tardanzas': tardanzas,
                'justificadas': justificadas,
                'porcentaje_asistencia': porcentaje_asistencia
            })

        # Ordenar por porcentaje de asistencia descendente
        resumenes.sort(key=lambda x: x['porcentaje_asistencia'], reverse=True)

        serializer = ResumenAsistenciaSerializer(resumenes, many=True)

        return Response({
            'resumen_por_materia': serializer.data,
            'gestion': gestion_activa.nombre
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mis_participaciones(request):
    """
    Endpoint para obtener participaciones del alumno
    Query params opcionales:
    - materia: ID de la materia
    - trimestre: ID del trimestre
    - fecha_inicio: YYYY-MM-DD
    - fecha_fin: YYYY-MM-DD
    """
    try:
        alumno = request.user.alumno

        # Obtener matriculación activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=gestion_activa,
                activa=True
            )
        except (Gestion.DoesNotExist, Matriculacion.DoesNotExist):
            return Response(
                {'error': 'No hay matriculación activa para el alumno'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Base queryset
        participaciones = Participacion.objects.filter(
            matriculacion=matriculacion
        ).select_related(
            'horario__profesor_materia__materia',
            'horario__profesor_materia__profesor'
        ).order_by('-fecha', '-created_at')

        # Filtros opcionales
        materia_id = request.query_params.get('materia')
        trimestre_id = request.query_params.get('trimestre')
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        if materia_id:
            participaciones = participaciones.filter(
                horario__profesor_materia__materia_id=materia_id
            )

        if trimestre_id:
            participaciones = participaciones.filter(
                horario__trimestre_id=trimestre_id
            )

        if fecha_inicio:
            try:
                fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                participaciones = participaciones.filter(fecha__gte=fecha_inicio_obj)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_inicio inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if fecha_fin:
            try:
                fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                participaciones = participaciones.filter(fecha__lte=fecha_fin_obj)
            except ValueError:
                return Response(
                    {'error': 'Formato de fecha_fin inválido. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        serializer = ParticipacionAlumnoSerializer(participaciones, many=True)

        return Response({
            'participaciones': serializer.data,
            'total_registros': participaciones.count()
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mis_participaciones_estadisticas(request):
    """
    Endpoint para obtener estadísticas de participaciones por materia
    """
    try:
        alumno = request.user.alumno

        # Obtener matriculación activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=gestion_activa,
                activa=True
            )
        except (Gestion.DoesNotExist, Matriculacion.DoesNotExist):
            return Response(
                {'error': 'No hay matriculación activa para el alumno'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener materias con participaciones
        materias_ids = Participacion.objects.filter(
            matriculacion=matriculacion
        ).values_list(
            'horario__profesor_materia__materia', flat=True
        ).distinct()

        estadisticas = []

        for materia_id in materias_ids:
            materia = Materia.objects.get(id=materia_id)

            participaciones_materia = Participacion.objects.filter(
                matriculacion=matriculacion,
                horario__profesor_materia__materia=materia
            )

            # Calcular estadísticas
            total = participaciones_materia.count()
            promedio = participaciones_materia.aggregate(Avg('valor'))['valor__avg'] or 0
            mejor = participaciones_materia.aggregate(Max('valor'))['valor__max'] or 0
            mas_reciente = participaciones_materia.aggregate(Max('fecha'))['fecha__max']

            # Distribución de valores
            distribucion = {}
            for i in range(1, 6):
                count = participaciones_materia.filter(valor=i).count()
                distribucion[str(i)] = count

            estadisticas.append({
                'materia': materia.nombre,
                'codigo_materia': materia.codigo,
                'total_participaciones': total,
                'promedio_valor': round(promedio, 2),
                'mejor_participacion': mejor,
                'participacion_mas_reciente': mas_reciente,
                'distribucion_valores': distribucion
            })

        # Ordenar por promedio descendente
        estadisticas.sort(key=lambda x: x['promedio_valor'], reverse=True)

        serializer = EstadisticasParticipacionSerializer(estadisticas, many=True)

        return Response({
            'estadisticas_por_materia': serializer.data,
            'gestion': gestion_activa.nombre
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mi_dashboard_rendimiento(request):
    """
    Endpoint principal para el dashboard de rendimiento del alumno
    """
    try:
        alumno = request.user.alumno

        # Obtener gestión activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=gestion_activa,
                activa=True
            )
        except (Gestion.DoesNotExist, Matriculacion.DoesNotExist):
            return Response(
                {'error': 'No hay matriculación activa para el alumno'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. RESUMEN GENERAL
        resumen_general = _calcular_resumen_general(matriculacion, gestion_activa)

        # 2. RENDIMIENTO POR MATERIA
        rendimiento_materias = _calcular_rendimiento_por_materia(matriculacion, gestion_activa)

        # 3. TENDENCIAS TRIMESTRALES
        tendencias = _calcular_tendencias_trimestrales(alumno, gestion_activa)

        # 4. ALERTAS DE RENDIMIENTO
        alertas = _generar_alertas_rendimiento(rendimiento_materias)

        # 5. COMPARATIVO CON EL GRUPO
        comparativo_grupo = _calcular_comparativo_grupo(alumno, gestion_activa)

        dashboard_data = {
            'resumen_general': resumen_general,
            'rendimiento_por_materia': rendimiento_materias,
            'tendencias_trimestrales': tendencias,
            'alertas': alertas,
            'comparativo_grupo': comparativo_grupo
        }

        serializer = DashboardRendimientoSerializer(dashboard_data)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mi_rendimiento_detallado(request):
    """
    Endpoint para obtener rendimiento detallado por materia
    Query params opcionales:
    - materia: ID de materia específica
    """
    try:
        alumno = request.user.alumno
        materia_id = request.query_params.get('materia')

        # Obtener gestión activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=gestion_activa,
                activa=True
            )
        except (Gestion.DoesNotExist, Matriculacion.DoesNotExist):
            return Response(
                {'error': 'No hay matriculación activa para el alumno'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if materia_id:
            # Rendimiento de una materia específica
            try:
                materia = Materia.objects.get(id=materia_id)
                rendimiento = _calcular_rendimiento_materia_detallado(matriculacion, materia, gestion_activa)
                return Response(rendimiento, status=status.HTTP_200_OK)
            except Materia.DoesNotExist:
                return Response(
                    {'error': 'Materia no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Rendimiento de todas las materias
            rendimiento_materias = _calcular_rendimiento_por_materia(matriculacion, gestion_activa)
            serializer = RendimientoMateriaSerializer(rendimiento_materias, many=True)

            return Response({
                'rendimiento_materias': serializer.data,
                'gestion': gestion_activa.nombre
            }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =====================================
# FUNCIONES AUXILIARES PARA CÁLCULOS
# =====================================

def _calcular_resumen_general(matriculacion, gestion):
    """Calcula el resumen general de rendimiento"""
    alumno = matriculacion.alumno

    # Promedios de notas
    notas_examenes = NotaExamen.objects.filter(
        matriculacion=matriculacion,
        examen__trimestre__gestion=gestion
    ).aggregate(promedio=Avg('nota'))['promedio'] or 0

    notas_tareas = NotaTarea.objects.filter(
        matriculacion=matriculacion,
        tarea__trimestre__gestion=gestion
    ).aggregate(promedio=Avg('nota'))['promedio'] or 0

    promedio_general = round((notas_examenes * 0.6 + notas_tareas * 0.4), 2) if notas_examenes and notas_tareas else 0

    # Asistencia
    total_asistencias = Asistencia.objects.filter(
        matriculacion=matriculacion
    ).count()

    asistencias_efectivas = Asistencia.objects.filter(
        matriculacion=matriculacion,
        estado__in=['P', 'T']
    ).count()

    porcentaje_asistencia = round((asistencias_efectivas / total_asistencias * 100), 2) if total_asistencias > 0 else 0

    # Participaciones
    total_participaciones = Participacion.objects.filter(
        matriculacion=matriculacion
    ).count()

    promedio_participaciones = Participacion.objects.filter(
        matriculacion=matriculacion
    ).aggregate(promedio=Avg('valor'))['promedio'] or 0

    # Materias por estado
    materias_con_notas = set()
    materias_con_notas.update(
        NotaExamen.objects.filter(matriculacion=matriculacion).values_list(
            'examen__profesor_materia__materia', flat=True
        )
    )
    materias_con_notas.update(
        NotaTarea.objects.filter(matriculacion=matriculacion).values_list(
            'tarea__profesor_materia__materia', flat=True
        )
    )

    materias_aprobadas = 0
    materias_en_riesgo = 0

    for materia_id in materias_con_notas:
        promedio_materia = _calcular_promedio_materia(matriculacion, materia_id)
        if promedio_materia >= 70:
            materias_aprobadas += 1
        elif promedio_materia < 60:
            materias_en_riesgo += 1

    return {
        'promedio_general': promedio_general,
        'promedio_examenes': round(notas_examenes, 2),
        'promedio_tareas': round(notas_tareas, 2),
        'porcentaje_asistencia': porcentaje_asistencia,
        'total_participaciones': total_participaciones,
        'promedio_participaciones': round(promedio_participaciones, 2),
        'materias_aprobadas': materias_aprobadas,
        'materias_en_riesgo': materias_en_riesgo,
        'total_materias': len(materias_con_notas)
    }


def _calcular_rendimiento_por_materia(matriculacion, gestion):
    """Calcula rendimiento detallado por materia"""
    # Obtener todas las materias con evaluaciones
    materias_examenes = set(
        NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__trimestre__gestion=gestion
        ).values_list('examen__profesor_materia__materia', flat=True)
    )

    materias_tareas = set(
        NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__trimestre__gestion=gestion
        ).values_list('tarea__profesor_materia__materia', flat=True)
    )

    materias_con_evaluaciones = materias_examenes.union(materias_tareas)

    rendimiento_materias = []

    for materia_id in materias_con_evaluaciones:
        materia = Materia.objects.get(id=materia_id)

        # Promedios
        promedio_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__profesor_materia__materia=materia,
            examen__trimestre__gestion=gestion
        ).aggregate(promedio=Avg('nota'))['promedio']

        promedio_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__profesor_materia__materia=materia,
            tarea__trimestre__gestion=gestion
        ).aggregate(promedio=Avg('nota'))['promedio']

        # Promedio general ponderado
        promedio_notas = None
        if promedio_examenes and promedio_tareas:
            promedio_notas = round(promedio_examenes * 0.6 + promedio_tareas * 0.4, 2)
        elif promedio_examenes:
            promedio_notas = round(promedio_examenes, 2)
        elif promedio_tareas:
            promedio_notas = round(promedio_tareas, 2)

        # Asistencia
        asistencias_materia = Asistencia.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__materia=materia
        )
        total_clases = asistencias_materia.count()
        asistencias_efectivas = asistencias_materia.filter(estado__in=['P', 'T']).count()
        porcentaje_asistencia = round((asistencias_efectivas / total_clases * 100), 2) if total_clases > 0 else None

        # Participaciones
        participaciones_materia = Participacion.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__materia=materia
        )
        total_participaciones = participaciones_materia.count()
        promedio_participaciones = participaciones_materia.aggregate(
            promedio=Avg('valor')
        )['promedio']

        # Estado y tendencia
        estado = 'sin_datos'
        tendencia = 'estable'
        color_estado = '#gray'

        if promedio_notas:
            if promedio_notas >= 80:
                estado = 'excelente'
                color_estado = '#22c55e'  # green
            elif promedio_notas >= 70:
                estado = 'aprobado'
                color_estado = '#3b82f6'  # blue
            elif promedio_notas >= 60:
                estado = 'en_riesgo'
                color_estado = '#f59e0b'  # yellow
            else:
                estado = 'reprobado'
                color_estado = '#ef4444'  # red

        rendimiento_materias.append({
            'materia': materia.nombre,
            'codigo_materia': materia.codigo,
            'promedio_notas': promedio_notas,
            'promedio_examenes': round(promedio_examenes, 2) if promedio_examenes else None,
            'promedio_tareas': round(promedio_tareas, 2) if promedio_tareas else None,
            'porcentaje_asistencia': porcentaje_asistencia,
            'total_participaciones': total_participaciones,
            'promedio_participaciones': round(promedio_participaciones, 2) if promedio_participaciones else None,
            'estado': estado,
            'tendencia': tendencia,
            'color_estado': color_estado
        })

    # Ordenar por promedio descendente
    rendimiento_materias.sort(key=lambda x: x['promedio_notas'] or 0, reverse=True)

    return rendimiento_materias


def _calcular_tendencias_trimestrales(alumno, gestion):
    """Calcula tendencias por trimestre"""
    trimestres = Trimestre.objects.filter(gestion=gestion).order_by('numero')
    tendencias = []

    try:
        matriculacion = Matriculacion.objects.get(alumno=alumno, gestion=gestion, activa=True)

        for trimestre in trimestres:
            # Promedio de notas del trimestre
            notas_examenes = NotaExamen.objects.filter(
                matriculacion=matriculacion,
                examen__trimestre=trimestre
            ).aggregate(promedio=Avg('nota'))['promedio'] or 0

            # CORRECCIÓN: Agregar filtro por trimestre a las tareas
            notas_tareas = NotaTarea.objects.filter(
                matriculacion=matriculacion,
                tarea__trimestre=trimestre  # <- FALTABA ESTE FILTRO
            ).aggregate(promedio=Avg('nota'))['promedio'] or 0

            promedio_general = round((notas_examenes * 0.6 + notas_tareas * 0.4),
                                     2) if notas_examenes and notas_tareas else None

            # Asistencia del trimestre
            asistencias_trimestre = Asistencia.objects.filter(
                matriculacion=matriculacion,
                horario__trimestre=trimestre
            )
            total_clases = asistencias_trimestre.count()
            asistencias_efectivas = asistencias_trimestre.filter(estado__in=['P', 'T']).count()
            porcentaje_asistencia = round((asistencias_efectivas / total_clases * 100), 2) if total_clases > 0 else None

            # Participaciones del trimestre
            total_participaciones = Participacion.objects.filter(
                matriculacion=matriculacion,
                horario__trimestre=trimestre
            ).count()

            # Materias aprobadas/en riesgo
            materias_trimestre = set()
            materias_trimestre.update(
                NotaExamen.objects.filter(
                    matriculacion=matriculacion,
                    examen__trimestre=trimestre
                ).values_list('examen__profesor_materia__materia', flat=True)
            )

            materias_aprobadas = 0
            materias_en_riesgo = 0

            for materia_id in materias_trimestre:
                promedio_materia = _calcular_promedio_materia_trimestre(matriculacion, materia_id, trimestre)
                if promedio_materia >= 70:
                    materias_aprobadas += 1
                elif promedio_materia < 60:
                    materias_en_riesgo += 1

            tendencias.append({
                'trimestre': trimestre.nombre,
                'promedio_general': promedio_general,
                'porcentaje_asistencia': porcentaje_asistencia,
                'total_participaciones': total_participaciones,
                'materias_aprobadas': materias_aprobadas,
                'materias_en_riesgo': materias_en_riesgo
            })

    except Matriculacion.DoesNotExist:
        pass

    return tendencias


def _calcular_promedio_materia(matriculacion, materia_id):
    """Calcula el promedio de una materia específica"""
    promedio_examenes = NotaExamen.objects.filter(
        matriculacion=matriculacion,
        examen__profesor_materia__materia_id=materia_id
    ).aggregate(promedio=Avg('nota'))['promedio']

    promedio_tareas = NotaTarea.objects.filter(
        matriculacion=matriculacion,
        tarea__profesor_materia__materia_id=materia_id
    ).aggregate(promedio=Avg('nota'))['promedio']

    if promedio_examenes and promedio_tareas:
        return promedio_examenes * 0.6 + promedio_tareas * 0.4
    elif promedio_examenes:
        return promedio_examenes
    elif promedio_tareas:
        return promedio_tareas
    else:
        return 0


def _calcular_promedio_materia_trimestre(matriculacion, materia_id, trimestre):
    """Calcula el promedio de una materia en un trimestre específico"""
    promedio_examenes = NotaExamen.objects.filter(
        matriculacion=matriculacion,
        examen__profesor_materia__materia_id=materia_id,
        examen__trimestre=trimestre
    ).aggregate(promedio=Avg('nota'))['promedio']

    promedio_tareas = NotaTarea.objects.filter(
        matriculacion=matriculacion,
        tarea__profesor_materia__materia_id=materia_id,
        tarea__trimestre=trimestre
    ).aggregate(promedio=Avg('nota'))['promedio']

    if promedio_examenes and promedio_tareas:
        return promedio_examenes * 0.6 + promedio_tareas * 0.4
    elif promedio_examenes:
        return promedio_examenes
    elif promedio_tareas:
        return promedio_tareas
    else:
        return 0


def _calcular_rendimiento_materia_detallado(matriculacion, materia, gestion):
    """Calcula rendimiento detallado de una materia específica"""
    # Obtener todas las evaluaciones de la materia
    examenes = NotaExamen.objects.filter(
        matriculacion=matriculacion,
        examen__profesor_materia__materia=materia,
        examen__trimestre__gestion=gestion
    ).select_related('examen').order_by('examen__fecha_examen')

    tareas = NotaTarea.objects.filter(
        matriculacion=matriculacion,
        tarea__profesor_materia__materia=materia,
        tarea__trimestre__gestion=gestion
    ).select_related('tarea').order_by('tarea__fecha_entrega')

    asistencias = Asistencia.objects.filter(
        matriculacion=matriculacion,
        horario__profesor_materia__materia=materia
    ).order_by('fecha')

    participaciones = Participacion.objects.filter(
        matriculacion=matriculacion,
        horario__profesor_materia__materia=materia
    ).order_by('fecha')

    # Calcular estadísticas
    promedio_examenes = examenes.aggregate(Avg('nota'))['nota__avg']
    promedio_tareas = tareas.aggregate(Avg('nota'))['nota__avg']

    total_asistencias = asistencias.count()
    asistencias_efectivas = asistencias.filter(estado__in=['P', 'T']).count()
    porcentaje_asistencia = (asistencias_efectivas / total_asistencias * 100) if total_asistencias > 0 else 0

    promedio_participaciones = participaciones.aggregate(Avg('valor'))['valor__avg']

    # Evolución trimestral
    trimestres = Trimestre.objects.filter(gestion=gestion).order_by('numero')
    evolucion_trimestral = []

    for trimestre in trimestres:
        exams_trimestre = examenes.filter(examen__trimestre=trimestre)
        tareas_trimestre = tareas.filter(tarea__trimestre=trimestre)

        prom_exam_trim = exams_trimestre.aggregate(Avg('nota'))['nota__avg']
        prom_tar_trim = tareas_trimestre.aggregate(Avg('nota'))['nota__avg']

        promedio_trimestre = None
        if prom_exam_trim and prom_tar_trim:
            promedio_trimestre = prom_exam_trim * 0.6 + prom_tar_trim * 0.4
        elif prom_exam_trim:
            promedio_trimestre = prom_exam_trim
        elif prom_tar_trim:
            promedio_trimestre = prom_tar_trim

        evolucion_trimestral.append({
            'trimestre': trimestre.nombre,
            'promedio': round(promedio_trimestre, 2) if promedio_trimestre else None,
            'examenes': exams_trimestre.count(),
            'tareas': tareas_trimestre.count()
        })

    return {
        'materia': {
            'nombre': materia.nombre,
            'codigo': materia.codigo,
            'horas_semanales': materia.horas_semanales
        },
        'resumen': {
            'promedio_examenes': round(promedio_examenes, 2) if promedio_examenes else None,
            'promedio_tareas': round(promedio_tareas, 2) if promedio_tareas else None,
            'promedio_general': round((promedio_examenes * 0.6 + promedio_tareas * 0.4),
                                      2) if promedio_examenes and promedio_tareas else None,
            'porcentaje_asistencia': round(porcentaje_asistencia, 2),
            'promedio_participaciones': round(promedio_participaciones, 2) if promedio_participaciones else None,
            'total_examenes': examenes.count(),
            'total_tareas': tareas.count(),
            'total_participaciones': participaciones.count()
        },
        'evolucion_trimestral': evolucion_trimestral,
        'ultimas_evaluaciones': {
            'examenes': [
                {
                    'titulo': ne.examen.titulo,
                    'fecha': ne.examen.fecha_examen,
                    'nota': float(ne.nota),
                    'ponderacion': float(ne.examen.ponderacion)
                } for ne in examenes[:5]
            ],
            'tareas': [
                {
                    'titulo': nt.tarea.titulo,
                    'fecha_entrega': nt.tarea.fecha_entrega,
                    'nota': float(nt.nota),
                    'ponderacion': float(nt.tarea.ponderacion)
                } for nt in tareas[:5]
            ]
        }
    }


def _calcular_comparativo_grupo(alumno, gestion):
    """Calcula comparativo con el grupo"""
    try:
        grupo = alumno.grupo

        # Obtener todos los alumnos del grupo
        alumnos_grupo = Alumno.objects.filter(grupo=grupo)
        matriculaciones_grupo = Matriculacion.objects.filter(
            alumno__in=alumnos_grupo,
            gestion=gestion,
            activa=True
        )

        if matriculaciones_grupo.count() == 0:
            return {
                'promedio_grupo': 0,
                'promedio_alumno': 0,
                'posicion_en_grupo': 1,
                'total_alumnos_grupo': 0,
                'percentil': 0,
                'por_encima_del_promedio': False,
                'diferencia_con_promedio': 0
            }

        # Calcular promedios de todos los alumnos del grupo
        promedios_grupo = []
        for matriculacion in matriculaciones_grupo:
            notas_examenes = NotaExamen.objects.filter(
                matriculacion=matriculacion,
                examen__trimestre__gestion=gestion
            ).aggregate(promedio=Avg('nota'))['promedio'] or 0

            notas_tareas = NotaTarea.objects.filter(
                matriculacion=matriculacion,
                tarea__trimestre__gestion=gestion
            ).aggregate(promedio=Avg('nota'))['promedio'] or 0

            if notas_examenes and notas_tareas:
                promedio_alumno_grupo = notas_examenes * 0.6 + notas_tareas * 0.4
                promedios_grupo.append(promedio_alumno_grupo)
            elif notas_examenes:
                promedios_grupo.append(notas_examenes)
            elif notas_tareas:
                promedios_grupo.append(notas_tareas)

        if not promedios_grupo:
            return {
                'promedio_grupo': 0,
                'promedio_alumno': 0,
                'posicion_en_grupo': 1,
                'total_alumnos_grupo': matriculaciones_grupo.count(),
                'percentil': 0,
                'por_encima_del_promedio': False,
                'diferencia_con_promedio': 0
            }

        promedio_grupo = sum(promedios_grupo) / len(promedios_grupo)

        # Calcular promedio del alumno actual
        matriculacion_alumno = Matriculacion.objects.get(
            alumno=alumno,
            gestion=gestion,
            activa=True
        )

        notas_examenes_alumno = NotaExamen.objects.filter(
            matriculacion=matriculacion_alumno,
            examen__trimestre__gestion=gestion
        ).aggregate(promedio=Avg('nota'))['promedio'] or 0

        notas_tareas_alumno = NotaTarea.objects.filter(
            matriculacion=matriculacion_alumno,
            tarea__trimestre__gestion=gestion
        ).aggregate(promedio=Avg('nota'))['promedio'] or 0

        promedio_alumno = 0
        if notas_examenes_alumno and notas_tareas_alumno:
            promedio_alumno = notas_examenes_alumno * 0.6 + notas_tareas_alumno * 0.4
        elif notas_examenes_alumno:
            promedio_alumno = notas_examenes_alumno
        elif notas_tareas_alumno:
            promedio_alumno = notas_tareas_alumno

        # Calcular posición en el grupo
        promedios_superiores = [p for p in promedios_grupo if p > promedio_alumno]
        posicion = len(promedios_superiores) + 1

        # Calcular percentil
        percentil = ((len(promedios_grupo) - posicion + 1) / len(promedios_grupo)) * 100

        return {
            'promedio_grupo': round(promedio_grupo, 2),
            'promedio_alumno': round(promedio_alumno, 2),
            'posicion_en_grupo': posicion,
            'total_alumnos_grupo': len(promedios_grupo),
            'percentil': round(percentil, 1),
            'por_encima_del_promedio': promedio_alumno > promedio_grupo,
            'diferencia_con_promedio': round(promedio_alumno - promedio_grupo, 2)
        }

    except Matriculacion.DoesNotExist:
        return {
            'promedio_grupo': 0,
            'promedio_alumno': 0,
            'posicion_en_grupo': 1,
            'total_alumnos_grupo': 0,
            'percentil': 0,
            'por_encima_del_promedio': False,
            'diferencia_con_promedio': 0,
            'mensaje': 'No hay matriculación activa para el alumno'
        }
    except Exception as e:
        return {
            'promedio_grupo': 0,
            'promedio_alumno': 0,
            'posicion_en_grupo': 1,
            'total_alumnos_grupo': 0,
            'percentil': 0,
            'por_encima_del_promedio': False,
            'diferencia_con_promedio': 0,
            'error': f'Error calculando comparativo: {str(e)}'
        }


def _generar_alertas_rendimiento(rendimiento_materias):
    """Genera alertas basadas en el rendimiento"""
    alertas = []

    for materia_data in rendimiento_materias:
        # Alerta por bajo rendimiento
        if materia_data['promedio_notas'] and materia_data['promedio_notas'] < 60:
            alertas.append({
                'tipo': 'bajo_rendimiento',
                'materia': materia_data['materia'],
                'mensaje': f"Promedio por debajo de 60 en {materia_data['materia']}",
                'nivel_criticidad': 'alta',
                'sugerencias': [
                    'Solicitar ayuda al profesor',
                    'Dedicar más tiempo de estudio',
                    'Participar más en clase'
                ]
            })

        # Alerta por baja asistencia
        if materia_data['porcentaje_asistencia'] and materia_data['porcentaje_asistencia'] < 80:
            alertas.append({
                'tipo': 'baja_asistencia',
                'materia': materia_data['materia'],
                'mensaje': f"Asistencia por debajo del 80% en {materia_data['materia']}",
                'nivel_criticidad': 'media',
                'sugerencias': [
                    'Mejorar puntualidad',
                    'Justificar faltas cuando sea necesario'
                ]
            })

        # Alerta por falta de participación
        if materia_data['total_participaciones'] < 3:
            alertas.append({
                'tipo': 'sin_participacion',
                'materia': materia_data['materia'],
                'mensaje': f"Pocas participaciones en {materia_data['materia']}",
                'nivel_criticidad': 'baja',
                'sugerencias': [
                    'Participar más activamente en clase',
                    'Hacer preguntas cuando no entiendas'
                ]
            })

    return alertas
