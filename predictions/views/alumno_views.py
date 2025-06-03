from datetime import timedelta
from django.db.models import Avg
from rest_framework import status
from shared.permissions import IsAlumno
from ..models import PrediccionRendimiento
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from academic.models import (Gestion, Matriculacion, Materia)
from rest_framework.decorators import api_view, permission_classes
from evaluations.models import (NotaExamen, Asistencia, NotaTarea, Participacion)
from ..serializers import (
    PrediccionAlumnoSerializer, PrediccionDetalladaSerializer, ResumenPrediccionesSerializer,
    EvolucionPrediccionSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mis_predicciones(request):
    """
    Endpoint para obtener todas las predicciones del alumno
    Query params opcionales:
    - materia: ID de materia específica
    - trimestre: ID del trimestre
    - solo_activas: true/false (por defecto true)
    """
    try:
        alumno = request.user.alumno

        # Obtener gestión activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
        except Gestion.DoesNotExist:
            return Response(
                {'error': 'No hay gestión académica activa'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Base queryset
        predicciones = PrediccionRendimiento.objects.filter(
            alumno=alumno,
            gestion=gestion_activa
        ).select_related('materia', 'trimestre', 'gestion').order_by('-fecha_prediccion')

        # Filtros opcionales
        materia_id = request.query_params.get('materia')
        trimestre_id = request.query_params.get('trimestre')
        solo_activas = request.query_params.get('solo_activas', 'true').lower() == 'true'

        if materia_id:
            predicciones = predicciones.filter(materia_id=materia_id)

        if trimestre_id:
            predicciones = predicciones.filter(trimestre_id=trimestre_id)

        if solo_activas:
            # Solo la predicción más reciente por materia
            predicciones_recientes = []
            materias_vistas = set()

            for prediccion in predicciones:
                if prediccion.materia_id not in materias_vistas:
                    predicciones_recientes.append(prediccion)
                    materias_vistas.add(prediccion.materia_id)

            predicciones = predicciones_recientes

        serializer = PrediccionAlumnoSerializer(predicciones, many=True)

        return Response({
            'predicciones': serializer.data,
            'total_predicciones': len(predicciones),
            'gestion': gestion_activa.nombre
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mi_prediccion_detallada(request, materia_id):
    """
    Endpoint para obtener predicción detallada de una materia específica
    con análisis, factores influyentes y recomendaciones
    """
    try:
        alumno = request.user.alumno

        # Validar que la materia existe
        try:
            materia = Materia.objects.get(id=materia_id)
        except Materia.DoesNotExist:
            return Response(
                {'error': 'Materia no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener gestión activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
        except Gestion.DoesNotExist:
            return Response(
                {'error': 'No hay gestión académica activa'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener la predicción más reciente para la materia
        try:
            prediccion = PrediccionRendimiento.objects.filter(
                alumno=alumno,
                materia=materia,
                gestion=gestion_activa
            ).order_by('-fecha_prediccion').first()

            if not prediccion:
                return Response(
                    {'error': 'No hay predicciones disponibles para esta materia'},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': f'Error obteniendo predicción: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Analizar factores influyentes
        factores = _analizar_factores_influyentes(alumno, materia, gestion_activa, prediccion)

        # Generar recomendaciones personalizadas
        recomendaciones = _generar_recomendaciones_materia(alumno, materia, prediccion, factores)

        # Comparación histórica
        comparacion = _obtener_comparacion_historica(alumno, materia, gestion_activa)

        # Calcular meta sugerida y probabilidad de aprobación
        meta_sugerida = _calcular_meta_sugerida(prediccion, factores)
        probabilidad_aprobacion = _calcular_probabilidad_aprobacion(prediccion, factores)

        # Construir respuesta detallada
        prediccion_detallada = {
            'prediccion': PrediccionAlumnoSerializer(prediccion).data,
            'factores_influyentes': factores,
            'recomendaciones': recomendaciones,
            'comparacion_historica': comparacion,
            'meta_sugerida': meta_sugerida,
            'probabilidad_aprobacion': probabilidad_aprobacion
        }

        serializer = PrediccionDetalladaSerializer(prediccion_detallada)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mis_recomendaciones(request):
    """
    Endpoint para obtener recomendaciones personalizadas basadas en todas las predicciones
    """
    try:
        alumno = request.user.alumno

        # Obtener gestión activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
        except Gestion.DoesNotExist:
            return Response(
                {'error': 'No hay gestión académica activa'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener todas las predicciones recientes
        predicciones = PrediccionRendimiento.objects.filter(
            alumno=alumno,
            gestion=gestion_activa
        ).select_related('materia').order_by('materia', '-fecha_prediccion')

        # Agrupar por materia (solo la más reciente)
        predicciones_por_materia = {}
        for prediccion in predicciones:
            if prediccion.materia_id not in predicciones_por_materia:
                predicciones_por_materia[prediccion.materia_id] = prediccion

        # Generar recomendaciones para todas las materias
        todas_recomendaciones = []

        for prediccion in predicciones_por_materia.values():
            factores = _analizar_factores_influyentes(alumno, prediccion.materia, gestion_activa, prediccion)
            recomendaciones_materia = _generar_recomendaciones_materia(alumno, prediccion.materia, prediccion, factores)
            todas_recomendaciones.extend(recomendaciones_materia)

        # Ordenar por prioridad
        orden_prioridad = {'alta': 1, 'media': 2, 'baja': 3}
        todas_recomendaciones.sort(key=lambda x: orden_prioridad.get(x['prioridad'], 4))

        # Generar recomendaciones generales
        recomendaciones_generales = _generar_recomendaciones_generales(alumno, gestion_activa,
                                                                       list(predicciones_por_materia.values()))

        return Response({
            'recomendaciones_por_materia': todas_recomendaciones,
            'recomendaciones_generales': recomendaciones_generales,
            'total_recomendaciones': len(todas_recomendaciones)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def mi_resumen_predicciones(request):
    """
    Endpoint para obtener resumen general de todas las predicciones del alumno
    """
    try:
        alumno = request.user.alumno

        # Obtener gestión activa
        try:
            gestion_activa = Gestion.objects.get(activa=True)
        except Gestion.DoesNotExist:
            return Response(
                {'error': 'No hay gestión académica activa'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener predicciones más recientes por materia
        predicciones = PrediccionRendimiento.objects.filter(
            alumno=alumno,
            gestion=gestion_activa
        ).select_related('materia').order_by('materia', '-fecha_prediccion')

        predicciones_recientes = {}
        for prediccion in predicciones:
            if prediccion.materia_id not in predicciones_recientes:
                predicciones_recientes[prediccion.materia_id] = prediccion

        predicciones_list = list(predicciones_recientes.values())

        if not predicciones_list:
            return Response({
                'total_materias': 0,
                'promedio_predicho': 0,
                'materias_en_riesgo': 0,
                'materias_excelentes': 0,
                'confianza_promedio': 0,
                'tendencia_general': 'sin_datos',
                'proxima_actualizacion': None,
                'mensaje': 'No hay predicciones disponibles'
            }, status=status.HTTP_200_OK)

        # Calcular métricas del resumen
        total_materias = len(predicciones_list)
        promedio_predicho = sum(float(p.nota_predicha) for p in predicciones_list) / total_materias

        materias_en_riesgo = sum(1 for p in predicciones_list if float(p.nota_predicha) < 60)
        materias_excelentes = sum(1 for p in predicciones_list if float(p.nota_predicha) >= 85)

        confianzas_validas = [float(p.confianza_prediccion) for p in predicciones_list if p.confianza_prediccion]
        confianza_promedio = sum(confianzas_validas) / len(confianzas_validas) if confianzas_validas else 0

        # Determinar tendencia general
        tendencia_general = _determinar_tendencia_general(alumno, gestion_activa)

        # Próxima actualización (estimada)
        ultima_prediccion = max(predicciones_list, key=lambda p: p.fecha_prediccion)
        proxima_actualizacion = ultima_prediccion.fecha_prediccion + timedelta(days=7)

        resumen = {
            'total_materias': total_materias,
            'promedio_predicho': round(promedio_predicho, 2),
            'materias_en_riesgo': materias_en_riesgo,
            'materias_excelentes': materias_excelentes,
            'confianza_promedio': round(confianza_promedio, 2),
            'tendencia_general': tendencia_general,
            'proxima_actualizacion': proxima_actualizacion
        }

        serializer = ResumenPrediccionesSerializer(resumen)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAlumno])
def evolucion_prediccion(request, materia_id):
    """
    Endpoint para obtener la evolución histórica de predicciones vs realidad para una materia
    """
    try:
        alumno = request.user.alumno

        # Validar materia
        try:
            materia = Materia.objects.get(id=materia_id)
        except Materia.DoesNotExist:
            return Response(
                {'error': 'Materia no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener todas las predicciones históricas de la materia
        predicciones = PrediccionRendimiento.objects.filter(
            alumno=alumno,
            materia=materia
        ).order_by('fecha_prediccion')

        if not predicciones:
            return Response(
                {'error': 'No hay predicciones históricas para esta materia'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Construir evolución con notas reales cuando estén disponibles
        evolucion = []

        for prediccion in predicciones:
            # Buscar nota real correspondiente al período de la predicción
            nota_real = _obtener_nota_real_periodo(alumno, materia, prediccion)

            evolucion.append({
                'fecha': prediccion.fecha_prediccion.date(),
                'nota_predicha': float(prediccion.nota_predicha),
                'confianza': float(prediccion.confianza_prediccion) if prediccion.confianza_prediccion else 0,
                'nota_real': nota_real
            })

        # Calcular precisión de las predicciones
        precision_stats = _calcular_precision_predicciones(evolucion)

        serializer = EvolucionPrediccionSerializer(evolucion, many=True)

        return Response({
            'evolucion': serializer.data,
            'estadisticas_precision': precision_stats,
            'materia': {
                'nombre': materia.nombre,
                'codigo': materia.codigo
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Error interno del servidor: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# =====================================
# FUNCIONES AUXILIARES PARA ANÁLISIS ML
# =====================================

def _analizar_factores_influyentes(alumno, materia, gestion, prediccion):
    """Analiza los factores que más influyen en la predicción"""
    try:
        matriculacion = Matriculacion.objects.get(alumno=alumno, gestion=gestion, activa=True)
    except Matriculacion.DoesNotExist:
        return []

    factores = []

    # Factor 1: Rendimiento en exámenes
    promedio_examenes = NotaExamen.objects.filter(
        matriculacion=matriculacion,
        examen__profesor_materia__materia=materia
    ).aggregate(Avg('nota'))['nota__avg']

    if promedio_examenes:
        tendencia_examenes = 'positiva' if promedio_examenes >= 70 else 'negativa' if promedio_examenes < 60 else 'estable'
        factores.append({
            'factor': 'Rendimiento en Exámenes',
            'importancia': round(promedio_examenes / 100 * 40, 2),  # 40% de importancia máxima
            'descripcion': f'Promedio actual: {round(promedio_examenes, 1)} puntos',
            'tendencia': tendencia_examenes
        })

    # Factor 2: Rendimiento en tareas
    promedio_tareas = NotaTarea.objects.filter(
        matriculacion=matriculacion,
        tarea__profesor_materia__materia=materia
    ).aggregate(Avg('nota'))['nota__avg']

    if promedio_tareas:
        tendencia_tareas = 'positiva' if promedio_tareas >= 70 else 'negativa' if promedio_tareas < 60 else 'estable'
        factores.append({
            'factor': 'Rendimiento en Tareas',
            'importancia': round(promedio_tareas / 100 * 30, 2),  # 30% de importancia máxima
            'descripcion': f'Promedio actual: {round(promedio_tareas, 1)} puntos',
            'tendencia': tendencia_tareas
        })

    # Factor 3: Asistencia
    asistencias = Asistencia.objects.filter(
        matriculacion=matriculacion,
        horario__profesor_materia__materia=materia
    )
    total_clases = asistencias.count()
    asistencias_efectivas = asistencias.filter(estado__in=['P', 'T']).count()
    porcentaje_asistencia = (asistencias_efectivas / total_clases * 100) if total_clases > 0 else 0

    if total_clases > 0:
        tendencia_asistencia = 'positiva' if porcentaje_asistencia >= 90 else 'negativa' if porcentaje_asistencia < 80 else 'estable'
        factores.append({
            'factor': 'Asistencia a Clases',
            'importancia': round(porcentaje_asistencia / 100 * 20, 2),  # 20% de importancia máxima
            'descripcion': f'Asistencia: {round(porcentaje_asistencia, 1)}%',
            'tendencia': tendencia_asistencia
        })

    # Factor 4: Participación
    participaciones = Participacion.objects.filter(
        matriculacion=matriculacion,
        horario__profesor_materia__materia=materia
    )
    promedio_participacion = participaciones.aggregate(Avg('valor'))['valor__avg']

    if promedio_participacion:
        tendencia_participacion = 'positiva' if promedio_participacion >= 4 else 'negativa' if promedio_participacion < 3 else 'estable'
        factores.append({
            'factor': 'Participación en Clase',
            'importancia': round(promedio_participacion / 5 * 10, 2),  # 10% de importancia máxima
            'descripcion': f'Promedio: {round(promedio_participacion, 1)}/5',
            'tendencia': tendencia_participacion
        })

    # Ordenar por importancia
    factores.sort(key=lambda x: x['importancia'], reverse=True)

    return factores

def _generar_recomendaciones_materia(alumno, materia, prediccion, factores):
    """Genera recomendaciones específicas para una materia"""
    recomendaciones = []
    nota_predicha = float(prediccion.nota_predicha)

    # Recomendaciones basadas en factores débiles
    for factor in factores:
        if factor['tendencia'] == 'negativa':
            if factor['factor'] == 'Rendimiento en Exámenes':
                recomendaciones.append({
                    'tipo': 'examenes',
                    'materia': materia.nombre,
                    'prioridad': 'alta',
                    'mensaje': 'Mejorar preparación para exámenes',
                    'acciones_sugeridas': [
                        'Repasar temas antes de cada examen',
                        'Solicitar material de estudio adicional',
                        'Formar grupo de estudio con compañeros'
                    ],
                    'impacto_estimado': 15.0
                })
            elif factor['factor'] == 'Rendimiento en Tareas':
                recomendaciones.append({
                    'tipo': 'estudio',
                    'materia': materia.nombre,
                    'prioridad': 'media',
                    'mensaje': 'Mejorar calidad de tareas entregadas',
                    'acciones_sugeridas': [
                        'Dedicar más tiempo a las tareas',
                        'Revisar las tareas antes de entregarlas',
                        'Consultar dudas con el profesor'
                    ],
                    'impacto_estimado': 10.0
                })
            elif factor['factor'] == 'Asistencia a Clases':
                recomendaciones.append({
                    'tipo': 'asistencia',
                    'materia': materia.nombre,
                    'prioridad': 'alta',
                    'mensaje': 'Mejorar asistencia a clases',
                    'acciones_sugeridas': [
                        'Establecer rutina de asistencia',
                        'Solicitar justificaciones cuando sea necesario',
                        'Recuperar clases perdidas con compañeros'
                    ],
                    'impacto_estimado': 12.0
                })
            elif factor['factor'] == 'Participación en Clase':
                recomendaciones.append({
                    'tipo': 'participacion',
                    'materia': materia.nombre,
                    'prioridad': 'baja',
                    'mensaje': 'Aumentar participación en clase',
                    'acciones_sugeridas': [
                        'Hacer más preguntas en clase',
                        'Participar en discusiones grupales',
                        'Ofrecer respuestas cuando el profesor pregunte'
                    ],
                    'impacto_estimado': 5.0
                })

    # Recomendaciones basadas en la predicción
    if nota_predicha < 60:
        recomendaciones.append({
            'tipo': 'urgente',
            'materia': materia.nombre,
            'prioridad': 'alta',
            'mensaje': 'Riesgo de reprobar la materia',
            'acciones_sugeridas': [
                'Solicitar tutoría con el profesor',
                'Aumentar horas de estudio significativamente',
                'Considerar clases particulares',
                'Revisar todos los temas desde el inicio'
            ],
            'impacto_estimado': 25.0
        })
    elif nota_predicha < 70:
        recomendaciones.append({
            'tipo': 'preventivo',
            'materia': materia.nombre,
            'prioridad': 'media',
            'mensaje': 'Reforzar conocimientos para asegurar aprobación',
            'acciones_sugeridas': [
                'Revisar temas que presentan dificultad',
                'Aumentar tiempo de estudio',
                'Practicar más ejercicios'
            ],
            'impacto_estimado': 15.0
        })

    return recomendaciones

def _generar_recomendaciones_generales(alumno, gestion, predicciones):
    """Genera recomendaciones generales basadas en todas las predicciones"""
    if not predicciones:
        return []

    recomendaciones = []
    promedio_general = sum(float(p.nota_predicha) for p in predicciones) / len(predicciones)
    materias_en_riesgo = [p for p in predicciones if float(p.nota_predicha) < 60]

    # Recomendación general de estudio
    if promedio_general < 70:
        recomendaciones.append({
            'tipo': 'estudio_general',
            'mensaje': 'Desarrollar mejores hábitos de estudio',
            'acciones': [
                'Crear un horario de estudio regular',
                'Usar técnicas de estudio efectivas',
                'Eliminar distracciones durante el estudio',
                'Buscar un lugar de estudio adecuado'
            ],
            'prioridad': 'alta'
        })

    # Recomendación para materias en riesgo
    if len(materias_en_riesgo) > 2:
        materias_nombres = [p.materia.nombre for p in materias_en_riesgo[:3]]
        recomendaciones.append({
            'tipo': 'materias_riesgo',
            'mensaje': f'Enfocar esfuerzos en {len(materias_en_riesgo)} materias en riesgo',
            'acciones': [
                f'Priorizar estudio en: {", ".join(materias_nombres)}',
                'Solicitar ayuda del profesor en materias difíciles',
                'Considerar tutoría adicional',
                'Redistribuir tiempo de estudio'
            ],
            'prioridad': 'alta'
        })

    # Recomendación de organización
    recomendaciones.append({
        'tipo': 'organizacion',
        'mensaje': 'Mejorar organización académica',
        'acciones': [
            'Usar una agenda para tareas y exámenes',
            'Planificar estudio con anticipación',
            'Mantener apuntes organizados',
            'Revisar progreso semanalmente'
        ],
        'prioridad': 'media'
    })

    return recomendaciones

def _obtener_comparacion_historica(alumno, materia, gestion):
    """Obtiene comparación con rendimiento histórico del alumno"""
    try:
        matriculacion = Matriculacion.objects.get(alumno=alumno, gestion=gestion, activa=True)

        # Promedio actual
        promedio_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__profesor_materia__materia=materia
        ).aggregate(Avg('nota'))['nota__avg'] or 0

        promedio_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__profesor_materia__materia=materia
        ).aggregate(Avg('nota'))['nota__avg'] or 0

        promedio_actual = (
                    promedio_examenes * 0.6 + promedio_tareas * 0.4) if promedio_examenes and promedio_tareas else 0

        # Buscar gestiones anteriores
        gestiones_anteriores = Gestion.objects.filter(
            anio__lt=gestion.anio
        ).order_by('-anio')[:2]  # Últimas 2 gestiones

        promedios_historicos = []
        for gestion_ant in gestiones_anteriores:
            try:
                matriculacion_ant = Matriculacion.objects.get(
                    alumno=alumno,
                    gestion=gestion_ant,
                    activa=True
                )

                prom_exam_ant = NotaExamen.objects.filter(
                    matriculacion=matriculacion_ant,
                    examen__profesor_materia__materia=materia
                ).aggregate(Avg('nota'))['nota__avg'] or 0

                prom_tar_ant = NotaTarea.objects.filter(
                    matriculacion=matriculacion_ant,
                    tarea__profesor_materia__materia=materia
                ).aggregate(Avg('nota'))['nota__avg'] or 0

                promedio_historico = (prom_exam_ant * 0.6 + prom_tar_ant * 0.4) if prom_exam_ant and prom_tar_ant else 0

                if promedio_historico > 0:
                    promedios_historicos.append({
                        'gestion': gestion_ant.nombre,
                        'promedio': round(promedio_historico, 2)
                    })

            except Matriculacion.DoesNotExist:
                continue

        # Calcular tendencia
        tendencia = 'estable'
        if promedios_historicos:
            ultimo_promedio = promedios_historicos[0]['promedio']
            if promedio_actual > ultimo_promedio + 5:
                tendencia = 'mejorando'
            elif promedio_actual < ultimo_promedio - 5:
                tendencia = 'empeorando'

        return {
            'promedio_actual': round(promedio_actual, 2),
            'promedios_anteriores': promedios_historicos,
            'tendencia': tendencia,
            'diferencia_ultimo_año': round(promedio_actual - promedios_historicos[0]['promedio'],
                                           2) if promedios_historicos else 0
        }

    except Exception:
        return {
            'promedio_actual': 0,
            'promedios_anteriores': [],
            'tendencia': 'sin_datos',
            'diferencia_ultimo_año': 0
        }

def _calcular_meta_sugerida(prediccion, factores):
    """Calcula una meta realista basada en la predicción y factores"""
    nota_predicha = float(prediccion.nota_predicha)

    # Meta base: nota predicha + margen de mejora
    margen_mejora = 0

    # Aumentar margen según factores positivos
    for factor in factores:
        if factor['tendencia'] == 'positiva':
            margen_mejora += factor['importancia'] * 0.1
        elif factor['tendencia'] == 'negativa':
            margen_mejora -= factor['importancia'] * 0.05

    meta = nota_predicha + margen_mejora

    # Limitar meta entre 51 y 100
    meta = max(51, min(100, meta))

    return round(meta, 2)

def _calcular_probabilidad_aprobacion(prediccion, factores):
    """Calcula probabilidad de aprobación basada en predicción y factores"""
    nota_predicha = float(prediccion.nota_predicha)
    confianza = float(prediccion.confianza_prediccion) if prediccion.confianza_prediccion else 50

    # Probabilidad base según la nota predicha
    if nota_predicha >= 80:
        prob_base = 95
    elif nota_predicha >= 70:
        prob_base = 85
    elif nota_predicha >= 60:
        prob_base = 70
    elif nota_predicha >= 51:
        prob_base = 50
    else:
        prob_base = 20

    # Ajustar según factores
    ajuste_factores = 0
    for factor in factores:
        if factor['tendencia'] == 'positiva':
            ajuste_factores += 2
        elif factor['tendencia'] == 'negativa':
            ajuste_factores -= 3

    # Ajustar según confianza del modelo
    ajuste_confianza = (confianza - 50) * 0.2

    probabilidad = prob_base + ajuste_factores + ajuste_confianza

    # Limitar entre 0 y 100
    probabilidad = max(0, min(100, probabilidad))

    return round(probabilidad, 2)

def _determinar_tendencia_general(alumno, gestion):
    """Determina la tendencia general del rendimiento del alumno"""
    try:
        # Comparar con gestión anterior
        gestion_anterior = Gestion.objects.filter(
            anio__lt=gestion.anio
        ).order_by('-anio').first()

        if not gestion_anterior:
            return 'sin_datos'

        # Promedios actuales
        try:
            matriculacion_actual = Matriculacion.objects.get(alumno=alumno, gestion=gestion, activa=True)
            matriculacion_anterior = Matriculacion.objects.get(alumno=alumno, gestion=gestion_anterior, activa=True)
        except Matriculacion.DoesNotExist:
            return 'sin_datos'

        # Calcular promedios
        notas_actual = []
        notas_actual.extend(
            NotaExamen.objects.filter(matriculacion=matriculacion_actual).values_list('nota', flat=True))
        notas_actual.extend(NotaTarea.objects.filter(matriculacion=matriculacion_actual).values_list('nota', flat=True))

        notas_anterior = []
        notas_anterior.extend(
            NotaExamen.objects.filter(matriculacion=matriculacion_anterior).values_list('nota', flat=True))
        notas_anterior.extend(
            NotaTarea.objects.filter(matriculacion=matriculacion_anterior).values_list('nota', flat=True))

        if not notas_actual or not notas_anterior:
            return 'sin_datos'

        promedio_actual = sum(float(n) for n in notas_actual) / len(notas_actual)
        promedio_anterior = sum(float(n) for n in notas_anterior) / len(notas_anterior)

        diferencia = promedio_actual - promedio_anterior

        if diferencia > 3:
            return 'mejorando'
        elif diferencia < -3:
            return 'empeorando'
        else:
            return 'estable'

    except Exception:
        return 'sin_datos'

def _obtener_nota_real_periodo(alumno, materia, prediccion):
    """Obtiene la nota real del alumno en el período de la predicción"""
    try:
        matriculacion = Matriculacion.objects.get(
            alumno=alumno,
            gestion=prediccion.gestion,
            activa=True
        )

        # Buscar notas después de la fecha de predicción
        fecha_limite = prediccion.fecha_prediccion.date() + timedelta(days=30)

        notas_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__profesor_materia__materia=materia,
            examen__fecha_examen__gte=prediccion.fecha_prediccion.date(),
            examen__fecha_examen__lte=fecha_limite
        ).values_list('nota', flat=True)

        notas_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__profesor_materia__materia=materia,
            tarea__fecha_entrega__gte=prediccion.fecha_prediccion.date(),
            tarea__fecha_entrega__lte=fecha_limite
        ).values_list('nota', flat=True)

        todas_notas = list(notas_examenes) + list(notas_tareas)

        if todas_notas:
            return round(sum(float(n) for n in todas_notas) / len(todas_notas), 2)
        else:
            return None

    except Exception:
        return None

def _calcular_precision_predicciones(evolucion):
    """Calcula estadísticas de precisión de las predicciones"""
    predicciones_con_real = [e for e in evolucion if e['nota_real'] is not None]

    if not predicciones_con_real:
        return {
            'total_comparaciones': 0,
            'precision_promedio': 0,
            'error_promedio': 0,
            'predicciones_acertadas': 0
        }

    errores = []
    acertadas = 0

    for evol in predicciones_con_real:
        error = abs(evol['nota_predicha'] - evol['nota_real'])
        errores.append(error)

        # Consideramos "acertada" si el error es menor a 5 puntos
        if error <= 5:
            acertadas += 1

    error_promedio = sum(errores) / len(errores)
    precision_promedio = 100 - (error_promedio / 100 * 100)  # Convertir error a precisión

    return {
        'total_comparaciones': len(predicciones_con_real),
        'precision_promedio': round(max(0, precision_promedio), 2),
        'error_promedio': round(error_promedio, 2),
        'predicciones_acertadas': acertadas,
        'porcentaje_acertadas': round((acertadas / len(predicciones_con_real)) * 100, 2)
    }
