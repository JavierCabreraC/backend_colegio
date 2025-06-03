from django.db.models import Avg
from rest_framework import status
from shared.permissions import IsProfesor, IsAlumno
from .models import PrediccionRendimiento
from .ml_engine import ModeloRendimientoML
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import date, datetime, timedelta
from authentication.models import Alumno, Profesor
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from evaluations.models import (NotaExamen, Asistencia, HistoricoTrimestral, NotaTarea, Participacion)
from academic.models import (ProfesorMateria, Grupo, Gestion, Trimestre, Matriculacion, Materia, Horario )
from .serializers import (
    MisAlumnosPrediccionSerializer, PrediccionAlumnoMateriaSerializer, AnalisisRiesgoGrupoSerializer,
    AlertaInteligentSerializer, EstadisticasMLSerializer, PrediccionAlumnoSerializer, PrediccionDetalladaSerializer,
    ResumenPrediccionesSerializer, EvolucionPrediccionSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProfesor])
def mis_alumnos_predicciones(request):
    """
    GET /api/predictions/mis-alumnos/
    Vista general de predicciones de todos los alumnos del profesor
    """
    try:
        # Obtener profesor actual
        profesor = get_object_or_404(Profesor, usuario=request.user)

        # Obtener gestión activa
        gestion_activa = Gestion.objects.filter(activa=True).first()
        if not gestion_activa:
            return Response({
                'error': 'No hay gestión académica activa'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener todas las materias del profesor
        profesor_materias = ProfesorMateria.objects.filter(profesor=profesor)

        if not profesor_materias.exists():
            return Response({
                'message': 'No tienes materias asignadas',
                'data': []
            })

        # Obtener todos los alumnos únicos de los grupos del profesor
        grupos_profesor = set()
        for pm in profesor_materias:
            # Obtener horarios para encontrar grupos
            horarios = Horario.objects.filter(
                profesor_materia=pm,
                trimestre__gestion=gestion_activa
            )
            for horario in horarios:
                grupos_profesor.add(horario.grupo)

        # Obtener alumnos matriculados en esos grupos
        matriculaciones = Matriculacion.objects.filter(
            gestion=gestion_activa,
            activa=True,
            alumno__grupo__in=grupos_profesor
        ).select_related('alumno')

        alumnos_data = []
        motor_ml = ModeloRendimientoML()

        for matriculacion in matriculaciones:
            alumno = matriculacion.alumno

            # Obtener predicciones existentes del alumno
            predicciones = PrediccionRendimiento.objects.filter(
                alumno=alumno,
                gestion=gestion_activa,
                materia__in=[pm.materia for pm in profesor_materias]
            )

            # Si no hay predicciones, generar algunas
            if not predicciones.exists():
                for pm in profesor_materias:
                    try:
                        prediccion_data = motor_ml.predecir_nota(alumno, pm.materia)
                        motor_ml.guardar_prediccion(alumno, pm.materia, prediccion_data)
                    except Exception as e:
                        print(f"Error generando predicción para {alumno.matricula}: {e}")

                # Recargar predicciones
                predicciones = PrediccionRendimiento.objects.filter(
                    alumno=alumno,
                    gestion=gestion_activa,
                    materia__in=[pm.materia for pm in profesor_materias]
                )

            if predicciones.exists():
                # Calcular estadísticas del alumno
                total_materias = predicciones.count()
                promedio_predicciones = predicciones.aggregate(
                    Avg('nota_predicha')
                )['nota_predicha__avg'] or 0

                materias_riesgo_alto = predicciones.filter(nota_predicha__lt=50).count()

                # Determinar nivel de riesgo general
                if promedio_predicciones < 50:
                    nivel_riesgo_general = 'alto'
                elif promedio_predicciones < 70:
                    nivel_riesgo_general = 'medio'
                else:
                    nivel_riesgo_general = 'bajo'

                ultima_actualizacion = predicciones.order_by('-fecha_prediccion').first().fecha_prediccion

                alumnos_data.append({
                    'alumno_id': alumno.usuario.id,
                    'matricula': alumno.matricula,
                    'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
                    'grupo_nombre': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}",
                    'total_materias': total_materias,
                    'promedio_predicciones': round(promedio_predicciones, 2),
                    'nivel_riesgo_general': nivel_riesgo_general,
                    'materias_riesgo_alto': materias_riesgo_alto,
                    'ultima_actualizacion': ultima_actualizacion
                })

        # Ordenar por riesgo (alto primero) y luego por promedio
        alumnos_data.sort(key=lambda x: (
            0 if x['nivel_riesgo_general'] == 'alto' else 1 if x['nivel_riesgo_general'] == 'medio' else 2,
            x['promedio_predicciones']
        ))

        serializer = MisAlumnosPrediccionSerializer(alumnos_data, many=True)

        return Response({
            'total_alumnos': len(alumnos_data),
            'estadisticas': {
                'alto_riesgo': len([a for a in alumnos_data if a['nivel_riesgo_general'] == 'alto']),
                'medio_riesgo': len([a for a in alumnos_data if a['nivel_riesgo_general'] == 'medio']),
                'bajo_riesgo': len([a for a in alumnos_data if a['nivel_riesgo_general'] == 'bajo']),
            },
            'alumnos': serializer.data
        })

    except Exception as e:
        return Response({
            'error': f'Error al obtener predicciones: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProfesor])
def prediccion_alumno_materia(request, alumno_id, codigo_materia):
    """
    GET /api/predictions/alumno/{id}/materia/{cod}/
    Predicción específica alumno-materia con análisis detallado
    """
    try:
        # Validar profesor
        profesor = get_object_or_404(Profesor, usuario=request.user)

        # Obtener alumno
        alumno = get_object_or_404(Alumno, usuario__id=alumno_id)

        # Obtener materia
        materia = get_object_or_404(Materia, codigo=codigo_materia)

        # Verificar que el profesor enseña esta materia
        profesor_materia = get_object_or_404(
            ProfesorMateria,
            profesor=profesor,
            materia=materia
        )

        # Verificar que el alumno está en un grupo del profesor
        gestion_activa = Gestion.objects.filter(activa=True).first()
        if not gestion_activa:
            return Response({
                'error': 'No hay gestión académica activa'
            }, status=status.HTTP_400_BAD_REQUEST)

        matriculacion = get_object_or_404(
            Matriculacion,
            alumno=alumno,
            gestion=gestion_activa,
            activa=True
        )

        # Generar predicción actualizada
        motor_ml = ModeloRendimientoML()
        prediccion_data = motor_ml.predecir_nota(alumno, materia)
        motor_ml.guardar_prediccion(alumno, materia, prediccion_data)

        # Obtener historial de rendimiento (últimos 3 trimestres)
        historiales = HistoricoTrimestral.objects.filter(
            alumno=alumno,
            materia=materia
        ).order_by('-trimestre__gestion__anio', '-trimestre__numero')[:3]

        historial_rendimiento = []
        for hist in historiales:
            historial_rendimiento.append({
                'trimestre': f"{hist.trimestre.gestion.anio} - {hist.trimestre.nombre}",
                'promedio': float(hist.promedio_trimestre),
                'asistencia': float(hist.porcentaje_asistencia or 0),
                'participaciones': hist.num_participaciones
            })

        # Generar recomendaciones basadas en la predicción
        recomendaciones = generar_recomendaciones(prediccion_data, alumno, materia)

        # Comparación con el grupo
        comparacion_grupo = obtener_comparacion_grupo(alumno, materia, prediccion_data)

        response_data = {
            'alumno_info': {
                'id': alumno.usuario.id,
                'matricula': alumno.matricula,
                'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
                'grupo': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}"
            },
            'materia_info': {
                'codigo': materia.codigo,
                'nombre': materia.nombre,
                'horas_semanales': materia.horas_semanales
            },
            'prediccion_actual': prediccion_data,
            'historial_rendimiento': historial_rendimiento,
            'recomendaciones': recomendaciones,
            'comparacion_grupo': comparacion_grupo
        }

        serializer = PrediccionAlumnoMateriaSerializer(response_data)
        return Response(serializer.data)

    except Exception as e:
        return Response({
            'error': f'Error al obtener predicción específica: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProfesor])
def analisis_riesgo_grupo(request, grupo_id):
    """
    GET /api/predictions/grupo/{id}/riesgo/
    Análisis de riesgo grupal completo
    """
    try:
        # Validar profesor
        profesor = get_object_or_404(Profesor, usuario=request.user)

        # Obtener grupo
        grupo = get_object_or_404(Grupo, id=grupo_id)

        # Verificar que el profesor enseña en este grupo
        gestion_activa = Gestion.objects.filter(activa=True).first()
        horarios_profesor = Horario.objects.filter(
            profesor_materia__profesor=profesor,
            grupo=grupo,
            trimestre__gestion=gestion_activa
        )

        if not horarios_profesor.exists():
            return Response({
                'error': 'No tienes clases asignadas en este grupo'
            }, status=status.HTTP_403_FORBIDDEN)

        # Obtener alumnos del grupo
        matriculaciones = Matriculacion.objects.filter(
            gestion=gestion_activa,
            activa=True,
            alumno__grupo=grupo
        ).select_related('alumno')

        # Obtener materias del profesor en este grupo
        materias_profesor = set(h.profesor_materia.materia for h in horarios_profesor)

        # Generar/actualizar predicciones para todos los alumnos
        motor_ml = ModeloRendimientoML()

        alumnos_alto_riesgo = []
        alumnos_medio_riesgo = []
        alumnos_bajo_riesgo = []

        total_predicciones = 0
        suma_predicciones = 0

        for matriculacion in matriculaciones:
            alumno = matriculacion.alumno
            predicciones_alumno = []

            for materia in materias_profesor:
                try:
                    prediccion_data = motor_ml.predecir_nota(alumno, materia)
                    predicciones_alumno.append(prediccion_data['nota_predicha'])
                    total_predicciones += 1
                    suma_predicciones += prediccion_data['nota_predicha']
                except Exception as e:
                    print(f"Error en predicción para {alumno.matricula}: {e}")

            if predicciones_alumno:
                promedio_alumno = sum(predicciones_alumno) / len(predicciones_alumno)

                alumno_info = {
                    'id': alumno.usuario.id,
                    'matricula': alumno.matricula,
                    'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
                    'promedio_predicho': round(promedio_alumno, 2),
                    'total_materias': len(predicciones_alumno),
                    'materias_riesgo': len([p for p in predicciones_alumno if p < 50])
                }

                if promedio_alumno < 50:
                    alumnos_alto_riesgo.append(alumno_info)
                elif promedio_alumno < 70:
                    alumnos_medio_riesgo.append(alumno_info)
                else:
                    alumnos_bajo_riesgo.append(alumno_info)

        # Estadísticas del grupo
        promedio_grupo = suma_predicciones / total_predicciones if total_predicciones > 0 else 0

        estadisticas_riesgo = {
            'total_alumnos': len(matriculaciones),
            'promedio_grupo': round(promedio_grupo, 2),
            'distribucion': {
                'alto_riesgo': len(alumnos_alto_riesgo),
                'medio_riesgo': len(alumnos_medio_riesgo),
                'bajo_riesgo': len(alumnos_bajo_riesgo)
            },
            'porcentajes': {
                'alto_riesgo': round(len(alumnos_alto_riesgo) / len(matriculaciones) * 100, 1),
                'medio_riesgo': round(len(alumnos_medio_riesgo) / len(matriculaciones) * 100, 1),
                'bajo_riesgo': round(len(alumnos_bajo_riesgo) / len(matriculaciones) * 100, 1)
            }
        }

        # Tendencias del grupo (comparar con trimestre anterior si existe)
        tendencias_grupo = obtener_tendencias_grupo(grupo, materias_profesor)

        # Recomendaciones generales
        recomendaciones_generales = generar_recomendaciones_grupo(estadisticas_riesgo, alumnos_alto_riesgo)

        response_data = {
            'grupo_info': {
                'id': grupo.id,
                'nombre': f"{grupo.nivel.numero}° {grupo.letra}",
                'nivel': grupo.nivel.numero,
                'capacidad_maxima': grupo.capacidad_maxima
            },
            'estadisticas_riesgo': estadisticas_riesgo,
            'alumnos_alto_riesgo': alumnos_alto_riesgo,
            'alumnos_medio_riesgo': alumnos_medio_riesgo,
            'alumnos_bajo_riesgo': alumnos_bajo_riesgo,
            'tendencias_grupo': tendencias_grupo,
            'recomendaciones_generales': recomendaciones_generales
        }

        serializer = AnalisisRiesgoGrupoSerializer(response_data)
        return Response(serializer.data)

    except Exception as e:
        return Response({
            'error': f'Error en análisis de riesgo grupal: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProfesor])
def alertas_inteligentes(request):
    """
    GET /api/predictions/alertas/mis-clases/
    Sistema de alertas inteligentes para el profesor
    """
    try:
        # Obtener profesor
        profesor = get_object_or_404(Profesor, usuario=request.user)

        # Obtener gestión activa
        gestion_activa = Gestion.objects.filter(activa=True).first()
        if not gestion_activa:
            return Response({
                'error': 'No hay gestión académica activa'
            }, status=status.HTTP_400_BAD_REQUEST)

        alertas = []
        motor_ml = ModeloRendimientoML()

        # Obtener materias del profesor
        profesor_materias = ProfesorMateria.objects.filter(profesor=profesor)

        for pm in profesor_materias:
            # Obtener alumnos de esta materia
            horarios = Horario.objects.filter(
                profesor_materia=pm,
                trimestre__gestion=gestion_activa
            )

            for horario in horarios:
                matriculaciones = Matriculacion.objects.filter(
                    gestion=gestion_activa,
                    activa=True,
                    alumno__grupo=horario.grupo
                )

                for matriculacion in matriculaciones:
                    alumno = matriculacion.alumno

                    # Generar alertas para este alumno-materia
                    alertas_alumno = generar_alertas_alumno(alumno, pm.materia, horario, motor_ml)
                    alertas.extend(alertas_alumno)

        # Ordenar alertas por prioridad y fecha
        prioridad_orden = {'alta': 0, 'media': 1, 'baja': 2}
        alertas.sort(key=lambda x: (prioridad_orden[x['prioridad']], x['dias_desde_deteccion']))

        # Filtrar por parámetros opcionales
        tipo_filtro = request.query_params.get('tipo')
        prioridad_filtro = request.query_params.get('prioridad')

        if tipo_filtro:
            alertas = [a for a in alertas if a['tipo_alerta'] == tipo_filtro]

        if prioridad_filtro:
            alertas = [a for a in alertas if a['prioridad'] == prioridad_filtro]

        serializer = AlertaInteligentSerializer(alertas, many=True)

        return Response({
            'total_alertas': len(alertas),
            'resumen': {
                'alta_prioridad': len([a for a in alertas if a['prioridad'] == 'alta']),
                'media_prioridad': len([a for a in alertas if a['prioridad'] == 'media']),
                'baja_prioridad': len([a for a in alertas if a['prioridad'] == 'baja'])
            },
            'alertas': serializer.data
        })

    except Exception as e:
        return Response({
            'error': f'Error al generar alertas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================================
# FUNCIONES AUXILIARES
# ================================

def generar_recomendaciones(prediccion_data, alumno, materia):
    """Genera recomendaciones personalizadas basadas en la predicción"""
    recomendaciones = []

    nota_predicha = prediccion_data['nota_predicha']
    factores = prediccion_data.get('factores_importantes', [])

    if nota_predicha < 50:
        recomendaciones.append("⚠️ URGENTE: El alumno está en riesgo alto de reprobación")
        recomendaciones.append("📞 Contactar al tutor inmediatamente")
        recomendaciones.append("📝 Asignar tareas de refuerzo adicionales")
    elif nota_predicha < 70:
        recomendaciones.append("⚡ Reforzar conceptos clave de la materia")
        recomendaciones.append("👥 Considerar trabajo en grupos de estudio")

    # Recomendaciones basadas en factores específicos
    for factor in factores:
        factor_nombre = factor.get('factor', '')

        if 'asistencia' in factor_nombre and factor.get('valor', 100) < 80:
            recomendaciones.append("📅 Monitorear asistencia más de cerca")

        if 'examenes' in factor_nombre and factor.get('valor', 100) < 60:
            recomendaciones.append("📊 Reforzar preparación para exámenes")

        if 'participacion' in factor_nombre and factor.get('valor', 0) < 3:
            recomendaciones.append("🗣️ Incentivar participación en clase")

    if not recomendaciones:
        recomendaciones.append("✅ El alumno tiene buen rendimiento, continuar motivando")

    return recomendaciones


def obtener_comparacion_grupo(alumno, materia, prediccion_data):
    """Compara el rendimiento del alumno con su grupo"""
    try:
        # Obtener otros alumnos del mismo grupo y materia
        gestion_activa = Gestion.objects.filter(activa=True).first()

        predicciones_grupo = PrediccionRendimiento.objects.filter(
            gestion=gestion_activa,
            materia=materia,
            alumno__grupo=alumno.grupo
        ).exclude(alumno=alumno)

        if predicciones_grupo.exists():
            promedio_grupo = predicciones_grupo.aggregate(
                Avg('nota_predicha')
            )['nota_predicha__avg']

            nota_alumno = prediccion_data['nota_predicha']
            diferencia = nota_alumno - promedio_grupo

            posicion = predicciones_grupo.filter(
                nota_predicha__lt=nota_alumno
            ).count() + 1

            total_grupo = predicciones_grupo.count() + 1

            return {
                'promedio_grupo': round(promedio_grupo, 2),
                'nota_alumno': nota_alumno,
                'diferencia_con_grupo': round(diferencia, 2),
                'posicion_en_grupo': posicion,
                'total_alumnos_grupo': total_grupo,
                'percentil': round((total_grupo - posicion) / total_grupo * 100, 1)
            }
    except Exception as e:
        print(f"Error en comparación de grupo: {e}")

    return {
        'promedio_grupo': 0,
        'nota_alumno': prediccion_data['nota_predicha'],
        'diferencia_con_grupo': 0,
        'posicion_en_grupo': 1,
        'total_alumnos_grupo': 1,
        'percentil': 50
    }


def obtener_tendencias_grupo(grupo, materias_profesor):
    """Obtiene tendencias históricas del grupo"""
    try:
        # Obtener datos del trimestre actual vs anterior
        gestion_activa = Gestion.objects.filter(activa=True).first()
        trimestre_actual = Trimestre.objects.filter(
            gestion=gestion_activa,
            fecha_inicio__lte=date.today(),
            fecha_fin__gte=date.today()
        ).first()

        if not trimestre_actual:
            return {'tendencia': 'sin_datos', 'descripcion': 'No hay datos suficientes'}

        # Comparar con trimestre anterior
        trimestre_anterior = Trimestre.objects.filter(
            gestion=gestion_activa,
            numero=trimestre_actual.numero - 1
        ).first()

        if trimestre_anterior:
            # Promedios del trimestre anterior
            promedios_anterior = HistoricoTrimestral.objects.filter(
                trimestre=trimestre_anterior,
                alumno__grupo=grupo,
                materia__in=materias_profesor
            ).aggregate(Avg('promedio_trimestre'))['promedio_trimestre__avg'] or 0

            # Promedios actuales (predicciones)
            predicciones_actuales = PrediccionRendimiento.objects.filter(
                gestion=gestion_activa,
                alumno__grupo=grupo,
                materia__in=materias_profesor
            ).aggregate(Avg('nota_predicha'))['nota_predicha__avg'] or 0

            diferencia = predicciones_actuales - promedios_anterior

            if diferencia > 5:
                tendencia = 'mejorando'
                descripcion = f'El grupo ha mejorado {diferencia:.1f} puntos respecto al trimestre anterior'
            elif diferencia < -5:
                tendencia = 'empeorando'
                descripcion = f'El grupo ha disminuido {abs(diferencia):.1f} puntos respecto al trimestre anterior'
            else:
                tendencia = 'estable'
                descripcion = 'El rendimiento del grupo se mantiene estable'

            return {
                'tendencia': tendencia,
                'descripcion': descripcion,
                'promedio_anterior': round(promedios_anterior, 2),
                'promedio_actual': round(predicciones_actuales, 2),
                'diferencia': round(diferencia, 2)
            }
    except Exception as e:
        print(f"Error en tendencias de grupo: {e}")

    return {'tendencia': 'sin_datos', 'descripcion': 'No hay datos suficientes para mostrar tendencias'}


def generar_recomendaciones_grupo(estadisticas, alumnos_alto_riesgo):
    """Genera recomendaciones para todo el grupo"""
    recomendaciones = []

    porcentaje_riesgo_alto = estadisticas['porcentajes']['alto_riesgo']

    if porcentaje_riesgo_alto > 30:
        recomendaciones.append("🚨 ALERTA: Más del 30% del grupo en riesgo alto")
        recomendaciones.append("📚 Revisar metodología de enseñanza")
        recomendaciones.append("⏰ Considerar clases de refuerzo grupales")
    elif porcentaje_riesgo_alto > 15:
        recomendaciones.append("⚠️ Porcentaje considerable en riesgo")
        recomendaciones.append("👥 Implementar sistema de tutorías entre pares")

    if len(alumnos_alto_riesgo) > 0:
        nombres = ', '.join([a['nombre_completo'] for a in alumnos_alto_riesgo[:3]])
        if len(alumnos_alto_riesgo) > 3:
            nombres += f' y {len(alumnos_alto_riesgo) - 3} más'
        recomendaciones.append(f"👤 Atención prioritaria a: {nombres}")

    if estadisticas['promedio_grupo'] > 80:
        recomendaciones.append("🌟 Excelente rendimiento grupal, mantener el nivel")

    return recomendaciones


def generar_alertas_alumno(alumno, materia, horario, motor_ml):
    """Genera alertas específicas para un alumno"""
    alertas = []

    try:
        # Obtener datos recientes del alumno
        gestion_activa = Gestion.objects.filter(activa=True).first()
        matriculacion = Matriculacion.objects.filter(
            alumno=alumno,
            gestion=gestion_activa,
            activa=True
        ).first()

        if not matriculacion:
            return alertas

        # 1. ALERTA POR RENDIMIENTO BAJO
        prediccion = motor_ml.predecir_nota(alumno, materia)
        if prediccion['nota_predicha'] < 50:
            alertas.append({
                'id': f"rendimiento_{alumno.matricula}_{materia.codigo}",
                'tipo_alerta': 'rendimiento_bajo',
                'prioridad': 'alta',
                'alumno_info': {
                    'id': alumno.usuario.id,
                    'matricula': alumno.matricula,
                    'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
                    'grupo': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}"
                },
                'materia_info': {
                    'codigo': materia.codigo,
                    'nombre': materia.nombre
                },
                'descripcion': f"Predicción de {prediccion['nota_predicha']:.1f} puntos - Alto riesgo de reprobación",
                'metricas_relevantes': {
                    'nota_predicha': prediccion['nota_predicha'],
                    'confianza': prediccion['confianza'],
                    'nivel_riesgo': prediccion['nivel_riesgo']
                },
                'acciones_sugeridas': [
                    "Programar reunión con el alumno",
                    "Contactar al tutor",
                    "Asignar tareas de refuerzo",
                    "Monitorear progreso semanalmente"
                ],
                'fecha_deteccion': datetime.now(),
                'dias_desde_deteccion': 0
            })

        # 2. ALERTA POR AUSENCIAS FRECUENTES
        trimestre_actual = Trimestre.objects.filter(
            gestion=gestion_activa,
            fecha_inicio__lte=date.today(),
            fecha_fin__gte=date.today()
        ).first()

        if trimestre_actual:
            asistencias_recientes = Asistencia.objects.filter(
                matriculacion=matriculacion,
                horario=horario,
                fecha__gte=date.today() - timedelta(days=14)
            )

            total_clases = asistencias_recientes.count()
            faltas = asistencias_recientes.filter(estado='F').count()

            if total_clases > 0 and faltas / total_clases > 0.3:  # Más del 30% de faltas
                alertas.append({
                    'id': f"ausencias_{alumno.matricula}_{materia.codigo}",
                    'tipo_alerta': 'ausencias',
                    'prioridad': 'media',
                    'alumno_info': {
                        'id': alumno.usuario.id,
                        'matricula': alumno.matricula,
                        'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
                        'grupo': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}"
                    },
                    'materia_info': {
                        'codigo': materia.codigo,
                        'nombre': materia.nombre
                    },
                    'descripcion': f"{faltas} faltas en las últimas {total_clases} clases ({faltas / total_clases * 100:.1f}%)",
                    'metricas_relevantes': {
                        'faltas_recientes': faltas,
                        'total_clases': total_clases,
                        'porcentaje_faltas': round(faltas / total_clases * 100, 1)
                    },
                    'acciones_sugeridas': [
                        "Verificar motivos de ausencias",
                        "Contactar al tutor",
                        "Proporcionar material de clases perdidas",
                        "Establecer plan de recuperación"
                    ],
                    'fecha_deteccion': datetime.now(),
                    'dias_desde_deteccion': 1
                })

        # 3. ALERTA POR TENDENCIA NEGATIVA
        examenes_recientes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__profesor_materia__materia=materia
        ).order_by('-examen__fecha_examen')[:3]

        if examenes_recientes.count() >= 2:
            notas = [float(e.nota) for e in examenes_recientes]
            if len(notas) >= 2 and notas[0] < notas[-1] - 10:  # Bajó más de 10 puntos
                alertas.append({
                    'id': f"tendencia_{alumno.matricula}_{materia.codigo}",
                    'tipo_alerta': 'tendencia_negativa',
                    'prioridad': 'media',
                    'alumno_info': {
                        'id': alumno.usuario.id,
                        'matricula': alumno.matricula,
                        'nombre_completo': f"{alumno.nombres} {alumno.apellidos}",
                        'grupo': f"{alumno.grupo.nivel.numero}° {alumno.grupo.letra}"
                    },
                    'materia_info': {
                        'codigo': materia.codigo,
                        'nombre': materia.nombre
                    },
                    'descripcion': f"Tendencia descendente: de {notas[-1]:.1f} a {notas[0]:.1f} puntos",
                    'metricas_relevantes': {
                        'nota_anterior': notas[-1],
                        'nota_actual': notas[0],
                        'diferencia': round(notas[0] - notas[-1], 1),
                        'total_evaluaciones': len(notas)
                    },
                    'acciones_sugeridas': [
                        "Analizar dificultades específicas",
                        "Reforzar conceptos problemáticos",
                        "Ajustar metodología de estudio",
                        "Considerar apoyo adicional"
                    ],
                    'fecha_deteccion': datetime.now(),
                    'dias_desde_deteccion': 2
                })

    except Exception as e:
        print(f"Error generando alertas para {alumno.matricula}: {e}")

    return alertas


# ================================
# ENDPOINT ADICIONAL: ESTADÍSTICAS ML
# ================================

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProfesor])
def estadisticas_modelo(request):
    """
    GET /api/predictions/estadisticas/
    Estadísticas del modelo de Machine Learning
    """
    try:
        motor_ml = ModeloRendimientoML()

        # Intentar entrenar el modelo si no está entrenado
        if not motor_ml.modelo_entrenado:
            motor_ml.entrenar_modelo()

        gestion_activa = Gestion.objects.filter(activa=True).first()

        # Contar predicciones totales
        total_predicciones = PrediccionRendimiento.objects.filter(
            gestion=gestion_activa
        ).count()

        # Distribución de riesgo
        distribucion_riesgo = {
            'alto_riesgo': PrediccionRendimiento.objects.filter(
                gestion=gestion_activa,
                nota_predicha__lt=50
            ).count(),
            'medio_riesgo': PrediccionRendimiento.objects.filter(
                gestion=gestion_activa,
                nota_predicha__gte=50,
                nota_predicha__lt=70
            ).count(),
            'bajo_riesgo': PrediccionRendimiento.objects.filter(
                gestion=gestion_activa,
                nota_predicha__gte=70
            ).count()
        }

        # Última actualización
        ultima_prediccion = PrediccionRendimiento.objects.filter(
            gestion=gestion_activa
        ).order_by('-fecha_prediccion').first()

        ultima_actualizacion = ultima_prediccion.fecha_prediccion if ultima_prediccion else None

        response_data = {
            'modelo_info': {
                'version': '1.0',
                'algoritmo': 'Random Forest',
                'estado': 'entrenado' if motor_ml.modelo_entrenado else 'no_entrenado',
                'caracteristicas_principales': [
                    'Rendimiento académico previo',
                    'Patrones de asistencia',
                    'Participación en clase',
                    'Tendencias temporales'
                ]
            },
            'precision_metricas': motor_ml.precision if motor_ml.precision else {
                'mae': 'N/A',
                'r2': 'N/A',
                'samples_train': 0,
                'samples_test': 0
            },
            'total_predicciones': total_predicciones,
            'distribucion_riesgo': distribucion_riesgo,
            'factores_mas_importantes': [
                'Promedio del trimestre anterior',
                'Porcentaje de asistencia',
                'Promedio de exámenes actuales',
                'Tendencia de notas',
                'Número de participaciones'
            ],
            'ultima_actualizacion': ultima_actualizacion
        }

        serializer = EstadisticasMLSerializer(response_data)
        return Response(serializer.data)

    except Exception as e:
        return Response({
            'error': f'Error al obtener estadísticas del modelo: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ********************************************************************************************************
# ********************************************************************************************************
# ********************************************************************************************************
# ********************************************************************************************************

# Alumnos:

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




