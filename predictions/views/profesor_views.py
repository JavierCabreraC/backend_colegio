import random
from django.db.models import Avg
from rest_framework import status
from shared.permissions import IsProfesor
from ..models import PrediccionRendimiento
from ..ml_engine import ModeloRendimientoML
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import date, datetime, timedelta
from authentication.models import Alumno, Profesor
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from evaluations.models import (NotaExamen, Asistencia, HistoricoTrimestral)
from academic.models import (ProfesorMateria, Grupo, Gestion, Trimestre, Matriculacion, Materia, Horario )
from ..serializers import (
    MisAlumnosPrediccionSerializer, PrediccionAlumnoMateriaSerializer, AnalisisRiesgoGrupoSerializer,
    AlertaInteligentSerializer, EstadisticasMLSerializer
)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProfesor])
def mis_alumnos_predicciones_dummy_simple(request):
    """
    GET /api/predictions/mis-alumnos-simple/
    Vista DUMMY simple sin serializer
    """

    # Nombres y apellidos bolivianos
    nombres = ["Carlos", "María", "José", "Ana", "Luis", "Carmen", "Pedro", "Rosa", "Miguel", "Elena"]
    apellidos = ["Mamani", "Quispe", "Condori", "Flores", "Choque", "Vargas", "García", "López"]
    grupos = ["1°A", "1°B", "2°A", "2°B", "3°A", "3°B"]

    # Estadísticas aleatorias que sumen 60
    alto_riesgo = random.randint(8, 18)
    medio_riesgo = random.randint(15, 25)
    bajo_riesgo = 60 - alto_riesgo - medio_riesgo

    if bajo_riesgo < 5:
        bajo_riesgo = random.randint(5, 15)
        medio_riesgo = 60 - alto_riesgo - bajo_riesgo

    # Generar 20 alumnos
    alumnos = []
    for i in range(20):
        # Nivel de riesgo basado en distribución
        if i < 6:  # ~30% alto riesgo
            nivel = "alto"
            promedio = round(random.uniform(35, 49), 2)
            materias_riesgo = random.randint(3, 6)
        elif i < 14:  # ~40% medio riesgo
            nivel = "medio"
            promedio = round(random.uniform(50, 69), 2)
            materias_riesgo = random.randint(1, 3)
        else:  # ~30% bajo riesgo
            nivel = "bajo"
            promedio = round(random.uniform(70, 95), 2)
            materias_riesgo = random.randint(0, 1)

        alumno = {
            'alumno_id': 1000 + i,
            'matricula': f"EST{20240000 + i + 1}",
            'nombre_completo': f"{random.choice(nombres)} {random.choice(apellidos)} {random.choice(apellidos)}",
            'grupo_nombre': random.choice(grupos),
            'total_materias': random.randint(6, 8),
            'promedio_predicciones': promedio,
            'nivel_riesgo_general': nivel,
            'materias_riesgo_alto': materias_riesgo,
            'ultima_actualizacion': "2024-12-20T10:30:00Z"
        }
        alumnos.append(alumno)

    return Response({
        'total_alumnos': 60,
        'estadisticas': {
            'alto_riesgo': alto_riesgo,
            'medio_riesgo': medio_riesgo,
            'bajo_riesgo': bajo_riesgo
        },
        'alumnos': alumnos
    })


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

        # CORRECCIÓN: Obtener gestión activa más reciente
        gestion_activa = Gestion.objects.filter(activa=True).order_by('-anio').first()
        if not gestion_activa:
            return Response({
                'error': 'No hay gestión académica activa'
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f"🎯 Gestión activa seleccionada: {gestion_activa.nombre}")

        # Obtener todas las materias del profesor
        profesor_materias = ProfesorMateria.objects.filter(profesor=profesor)

        if not profesor_materias.exists():
            return Response({
                'message': 'No tienes materias asignadas',
                'data': []
            })

        print(f"📚 Materias del profesor: {[pm.materia.nombre for pm in profesor_materias]}")

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

        print(f"👥 Grupos del profesor: {[f'{g.nivel.numero}°{g.letra}' for g in grupos_profesor]}")

        # Obtener alumnos matriculados en esos grupos
        matriculaciones = Matriculacion.objects.filter(
            gestion=gestion_activa,
            activa=True,
            alumno__grupo__in=grupos_profesor
        ).select_related('alumno')

        print(f"🎓 Alumnos encontrados: {matriculaciones.count()}")

        alumnos_data = []
        motor_ml = ModeloRendimientoML()

        # CORRECCIÓN: Intentar entrenar el modelo una sola vez al inicio
        print("🤖 Inicializando motor ML...")
        if not motor_ml.modelo_entrenado:
            exito_entrenamiento = motor_ml.entrenar_modelo()
            print(f"📊 Entrenamiento exitoso: {exito_entrenamiento}")

        for matriculacion in matriculaciones:
            alumno = matriculacion.alumno
            print(f"🔍 Procesando alumno: {alumno.matricula}")

            # Obtener predicciones existentes del alumno
            predicciones = PrediccionRendimiento.objects.filter(
                alumno=alumno,
                gestion=gestion_activa,
                materia__in=[pm.materia for pm in profesor_materias]
            )

            # Si no hay predicciones, generar algunas
            if not predicciones.exists():
                print(f"   💫 Generando predicciones para {alumno.matricula}")
                for pm in profesor_materias:
                    try:
                        prediccion_data = motor_ml.predecir_nota(alumno, pm.materia)
                        motor_ml.guardar_prediccion(alumno, pm.materia, prediccion_data)
                        print(f"      ✅ {pm.materia.codigo}: {prediccion_data['nota_predicha']}")
                    except Exception as e:
                        print(f"      ❌ Error en {pm.materia.codigo}: {e}")

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
            else:
                print(f"   ⚠️ No se pudieron generar predicciones para {alumno.matricula}")

        print(f"📋 Total de alumnos procesados con éxito: {len(alumnos_data)}")

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
            'alumnos': serializer.data,
            'debug_info': {
                'gestion_activa': gestion_activa.nombre,
                'total_materias_profesor': profesor_materias.count(),
                'total_grupos': len(grupos_profesor),
                'modelo_entrenado': motor_ml.modelo_entrenado,
                'precision_modelo': motor_ml.precision
            }
        })

    except Exception as e:
        print(f"❌ Error completo: {str(e)}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")

        return Response({
            'error': f'Error al obtener predicciones: {str(e)}',
            'debug': {
                'traceback': traceback.format_exc(),
                'usuario': request.user.email if request.user else 'Anónimo'
            }
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
