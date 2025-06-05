import numpy as np
import pandas as pd
from django.db.models import Avg
from datetime import date, datetime, timedelta
from .models import PrediccionRendimiento
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from academic.models import Gestion, Trimestre, Matriculacion
from evaluations.models import NotaExamen, NotaTarea, Asistencia, Participacion, HistoricoTrimestral


class ModeloRendimientoML:
    """
    Motor simplificado para predicciones de rendimiento académico
    Usa solo datos de la gestión activa actual con reglas simples
    """

    def __init__(self):
        self.modelo_entrenado = True  # Siempre está "entrenado" porque usa reglas simples
        self.precision = {
            'tipo': 'modelo_basado_en_reglas',
            'version': '1.0_simple',
            'descripcion': 'Predicción basada en promedios actuales y tendencias'
        }

    def predecir_nota(self, alumno, materia, trimestre=None):
        """
        Hace una predicción simple basada en datos actuales del alumno
        """
        try:
            # Obtener gestión y trimestre actual
            if not trimestre:
                gestion_activa = Gestion.objects.filter(activa=True).order_by('-anio').first()
                if not gestion_activa:
                    return self._prediccion_por_defecto(alumno, materia)

                # Buscar trimestre actual o el más reciente
                trimestre = Trimestre.objects.filter(
                    gestion=gestion_activa,
                    fecha_inicio__lte=date.today(),
                    fecha_fin__gte=date.today()
                ).first()

                if not trimestre:
                    trimestre = Trimestre.objects.filter(
                        gestion=gestion_activa
                    ).order_by('-numero').first()

            if not trimestre:
                return self._prediccion_por_defecto(alumno, materia)

            # Obtener matriculación
            matriculacion = Matriculacion.objects.filter(
                alumno=alumno,
                gestion=trimestre.gestion,
                activa=True
            ).first()

            if not matriculacion:
                return self._prediccion_por_defecto(alumno, materia)

            # Extraer métricas del alumno
            metricas = self._extraer_metricas_alumno(matriculacion, materia, trimestre)

            # Calcular predicción con reglas simples
            nota_predicha = self._calcular_prediccion_simple(metricas)

            # Calcular confianza basada en cantidad de datos
            confianza = self._calcular_confianza(metricas)

            # Clasificar nivel de riesgo
            nivel_riesgo = self._clasificar_riesgo(nota_predicha, metricas)

            # Generar factores explicativos
            factores_importantes = self._generar_factores_importantes(metricas)

            return {
                'nota_predicha': round(max(0, min(100, nota_predicha)), 2),
                'confianza': round(confianza, 1),
                'nivel_riesgo': nivel_riesgo,
                'factores_importantes': factores_importantes,
                'caracteristicas_utilizadas': metricas,
                'metadata': {
                    'modelo_version': '1.0_simple',
                    'tipo_prediccion': 'reglas_basicas',
                    'fecha_prediccion': date.today().isoformat(),
                    'trimestre': f"{trimestre.gestion.anio} - T{trimestre.numero}"
                }
            }

        except Exception as e:
            print(f"Error en predicción simple para {alumno.matricula}: {e}")
            return self._prediccion_por_defecto(alumno, materia)

    def _extraer_metricas_alumno(self, matriculacion, materia, trimestre):
        """
        Extrae métricas básicas del alumno para la predicción
        """
        metricas = {}

        # 1. NOTAS DE EXÁMENES
        notas_examenes = NotaExamen.objects.filter(
            matriculacion=matriculacion,
            examen__profesor_materia__materia=materia,
            examen__trimestre=trimestre
        ).order_by('examen__fecha_examen')

        if notas_examenes.exists():
            notas_list = [float(ne.nota) for ne in notas_examenes]
            metricas['promedio_examenes'] = sum(notas_list) / len(notas_list)
            metricas['total_examenes'] = len(notas_list)
            metricas['nota_mas_alta'] = max(notas_list)
            metricas['nota_mas_baja'] = min(notas_list)

            # Tendencia simple: comparar primera y última nota
            if len(notas_list) >= 2:
                metricas['tendencia_examenes'] = notas_list[-1] - notas_list[0]
            else:
                metricas['tendencia_examenes'] = 0
        else:
            metricas['promedio_examenes'] = 0
            metricas['total_examenes'] = 0
            metricas['nota_mas_alta'] = 0
            metricas['nota_mas_baja'] = 0
            metricas['tendencia_examenes'] = 0

        # 2. NOTAS DE TAREAS
        notas_tareas = NotaTarea.objects.filter(
            matriculacion=matriculacion,
            tarea__profesor_materia__materia=materia,
            tarea__trimestre=trimestre
        )

        if notas_tareas.exists():
            promedio_tareas = notas_tareas.aggregate(Avg('nota'))['nota__avg']
            metricas['promedio_tareas'] = float(promedio_tareas)
            metricas['total_tareas'] = notas_tareas.count()
        else:
            metricas['promedio_tareas'] = 0
            metricas['total_tareas'] = 0

        # 3. ASISTENCIA
        asistencias = Asistencia.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__materia=materia,
            horario__trimestre=trimestre
        )

        total_clases = asistencias.count()
        if total_clases > 0:
            presentes = asistencias.filter(estado__in=['P', 'T']).count()
            faltas = asistencias.filter(estado='F').count()

            metricas['porcentaje_asistencia'] = (presentes / total_clases) * 100
            metricas['total_faltas'] = faltas
            metricas['total_clases'] = total_clases

            # Faltas recientes (últimas 2 semanas)
            fecha_limite = date.today() - timedelta(days=14)
            faltas_recientes = asistencias.filter(
                estado='F',
                fecha__gte=fecha_limite
            ).count()
            metricas['faltas_recientes'] = faltas_recientes
        else:
            metricas['porcentaje_asistencia'] = 100
            metricas['total_faltas'] = 0
            metricas['total_clases'] = 0
            metricas['faltas_recientes'] = 0

        # 4. PARTICIPACIÓN
        participaciones = Participacion.objects.filter(
            matriculacion=matriculacion,
            horario__profesor_materia__materia=materia,
            horario__trimestre=trimestre
        )

        if participaciones.exists():
            promedio_participacion = participaciones.aggregate(Avg('valor'))['valor__avg']
            metricas['promedio_participacion'] = float(promedio_participacion)
            metricas['total_participaciones'] = participaciones.count()
        else:
            metricas['promedio_participacion'] = 0
            metricas['total_participaciones'] = 0

        # 5. MÉTRICAS TEMPORALES
        dias_transcurridos = (date.today() - trimestre.fecha_inicio).days
        duracion_trimestre = (trimestre.fecha_fin - trimestre.fecha_inicio).days
        metricas['progreso_trimestre'] = min(dias_transcurridos / duracion_trimestre,
                                             1.0) if duracion_trimestre > 0 else 0.5

        # 6. RENDIMIENTO PREVIO (trimestre anterior si existe)
        trimestre_anterior = Trimestre.objects.filter(
            gestion=trimestre.gestion,
            numero=trimestre.numero - 1
        ).first()

        if trimestre_anterior:
            # Buscar notas del trimestre anterior para esta materia
            examenes_anteriores = NotaExamen.objects.filter(
                matriculacion__alumno=matriculacion.alumno,
                matriculacion__gestion=trimestre.gestion,
                examen__profesor_materia__materia=materia,
                examen__trimestre=trimestre_anterior
            )

            if examenes_anteriores.exists():
                metricas['promedio_trimestre_anterior'] = examenes_anteriores.aggregate(Avg('nota'))['nota__avg']
            else:
                metricas['promedio_trimestre_anterior'] = 70  # Promedio neutro
        else:
            metricas['promedio_trimestre_anterior'] = 70

        return metricas

    def _calcular_prediccion_simple(self, metricas):
        """
        Calcula predicción usando reglas simples y pesos
        """
        prediccion_base = 70  # Nota base neutral

        # 1. PESO DE EXÁMENES (40% del cálculo)
        if metricas['total_examenes'] > 0:
            factor_examenes = (metricas['promedio_examenes'] - 70) * 0.4
            prediccion_base += factor_examenes

        # 2. PESO DE TAREAS (20% del cálculo)
        if metricas['total_tareas'] > 0:
            factor_tareas = (metricas['promedio_tareas'] - 70) * 0.2
            prediccion_base += factor_tareas

        # 3. PESO DE ASISTENCIA (20% del cálculo)
        if metricas['porcentaje_asistencia'] < 80:
            # Penalización por baja asistencia
            penalizacion_asistencia = (80 - metricas['porcentaje_asistencia']) * 0.3
            prediccion_base -= penalizacion_asistencia
        elif metricas['porcentaje_asistencia'] > 95:
            # Bonus por excelente asistencia
            prediccion_base += 3

        # 4. PESO DE PARTICIPACIÓN (10% del cálculo)
        if metricas['total_participaciones'] > 0:
            if metricas['promedio_participacion'] >= 4:
                prediccion_base += 2  # Bonus por buena participación
            elif metricas['promedio_participacion'] <= 2:
                prediccion_base -= 3  # Penalización por baja participación

        # 5. TENDENCIA DE EXÁMENES (10% del cálculo)
        if metricas['total_examenes'] >= 2:
            if metricas['tendencia_examenes'] > 5:
                prediccion_base += 3  # Tendencia positiva
            elif metricas['tendencia_examenes'] < -5:
                prediccion_base -= 3  # Tendencia negativa

        # 6. AJUSTES POR TRIMESTRE ANTERIOR
        diferencia_anterior = prediccion_base - metricas['promedio_trimestre_anterior']
        if abs(diferencia_anterior) > 20:
            # Si la diferencia es muy grande, moderar hacia el promedio anterior
            prediccion_base = metricas['promedio_trimestre_anterior'] + (diferencia_anterior * 0.7)

        # 7. AJUSTES POR PROGRESO DEL TRIMESTRE
        if metricas['progreso_trimestre'] < 0.3:
            # Si estamos al inicio del trimestre, ser más conservador
            prediccion_base = (prediccion_base + metricas['promedio_trimestre_anterior']) / 2

        # 8. PENALIZACIONES ESPECÍFICAS
        if metricas['faltas_recientes'] >= 3:
            prediccion_base -= 5  # Muchas faltas recientes

        if metricas['total_examenes'] == 0 and metricas['progreso_trimestre'] > 0.5:
            prediccion_base -= 5  # No tiene exámenes y ya pasó la mitad del trimestre

        return prediccion_base

    def _calcular_confianza(self, metricas):
        """
        Calcula la confianza de la predicción basada en datos disponibles
        """
        confianza_base = 50

        # Más datos = más confianza
        if metricas['total_examenes'] >= 3:
            confianza_base += 20
        elif metricas['total_examenes'] >= 1:
            confianza_base += 10

        if metricas['total_tareas'] >= 3:
            confianza_base += 15
        elif metricas['total_tareas'] >= 1:
            confianza_base += 8

        if metricas['total_clases'] >= 15:
            confianza_base += 10
        elif metricas['total_clases'] >= 5:
            confianza_base += 5

        if metricas['total_participaciones'] >= 3:
            confianza_base += 5

        # Progreso del trimestre afecta confianza
        if metricas['progreso_trimestre'] > 0.6:
            confianza_base += 10
        elif metricas['progreso_trimestre'] < 0.2:
            confianza_base -= 10

        return max(30, min(95, confianza_base))

    def _clasificar_riesgo(self, nota_predicha, metricas):
        """
        Clasifica el nivel de riesgo del alumno
        """
        if nota_predicha < 50:
            return 'alto'
        elif nota_predicha < 65:
            # Verificar factores adicionales para riesgo medio
            factores_riesgo = 0

            if metricas['porcentaje_asistencia'] < 80:
                factores_riesgo += 1
            if metricas['tendencia_examenes'] < -5:
                factores_riesgo += 1
            if metricas['faltas_recientes'] >= 2:
                factores_riesgo += 1

            if factores_riesgo >= 2:
                return 'alto'
            else:
                return 'medio'
        elif nota_predicha < 75:
            return 'medio'
        else:
            return 'bajo'

    def _generar_factores_importantes(self, metricas):
        """
        Genera explicaciones sobre los factores más importantes
        """
        factores = []

        # Factor principal: exámenes
        if metricas['total_examenes'] > 0:
            if metricas['promedio_examenes'] >= 80:
                factores.append({
                    'factor': 'Exámenes',
                    'valor': metricas['promedio_examenes'],
                    'impacto': 'positivo',
                    'descripcion': f"Excelente promedio en exámenes: {metricas['promedio_examenes']:.1f}"
                })
            elif metricas['promedio_examenes'] < 60:
                factores.append({
                    'factor': 'Exámenes',
                    'valor': metricas['promedio_examenes'],
                    'impacto': 'negativo',
                    'descripcion': f"Promedio bajo en exámenes: {metricas['promedio_examenes']:.1f}"
                })

        # Factor asistencia
        if metricas['porcentaje_asistencia'] < 80:
            factores.append({
                'factor': 'Asistencia',
                'valor': metricas['porcentaje_asistencia'],
                'impacto': 'negativo',
                'descripcion': f"Baja asistencia: {metricas['porcentaje_asistencia']:.1f}%"
            })
        elif metricas['porcentaje_asistencia'] > 95:
            factores.append({
                'factor': 'Asistencia',
                'valor': metricas['porcentaje_asistencia'],
                'impacto': 'positivo',
                'descripcion': f"Excelente asistencia: {metricas['porcentaje_asistencia']:.1f}%"
            })

        # Factor tendencia
        if metricas['total_examenes'] >= 2:
            if metricas['tendencia_examenes'] > 5:
                factores.append({
                    'factor': 'Tendencia',
                    'valor': metricas['tendencia_examenes'],
                    'impacto': 'positivo',
                    'descripcion': f"Tendencia ascendente en notas (+{metricas['tendencia_examenes']:.1f})"
                })
            elif metricas['tendencia_examenes'] < -5:
                factores.append({
                    'factor': 'Tendencia',
                    'valor': metricas['tendencia_examenes'],
                    'impacto': 'negativo',
                    'descripcion': f"Tendencia descendente en notas ({metricas['tendencia_examenes']:.1f})"
                })

        # Factor participación
        if metricas['total_participaciones'] > 0:
            if metricas['promedio_participacion'] >= 4:
                factores.append({
                    'factor': 'Participación',
                    'valor': metricas['promedio_participacion'],
                    'impacto': 'positivo',
                    'descripcion': f"Buena participación en clase: {metricas['promedio_participacion']:.1f}/5"
                })
            elif metricas['promedio_participacion'] <= 2:
                factores.append({
                    'factor': 'Participación',
                    'valor': metricas['promedio_participacion'],
                    'impacto': 'negativo',
                    'descripcion': f"Baja participación en clase: {metricas['promedio_participacion']:.1f}/5"
                })

        # Factor faltas recientes
        if metricas['faltas_recientes'] >= 3:
            factores.append({
                'factor': 'Faltas recientes',
                'valor': metricas['faltas_recientes'],
                'impacto': 'negativo',
                'descripcion': f"Muchas faltas recientes: {metricas['faltas_recientes']} en 2 semanas"
            })

        # Si no hay factores específicos, agregar uno general
        if not factores:
            factores.append({
                'factor': 'Rendimiento general',
                'valor': (metricas['promedio_examenes'] + metricas['promedio_tareas']) / 2,
                'impacto': 'neutro',
                'descripcion': 'Rendimiento estable basado en datos disponibles'
            })

        return factores[:4]  # Máximo 4 factores

    def _prediccion_por_defecto(self, alumno, materia):
        """
        Predicción por defecto cuando no hay datos suficientes
        """
        return {
            'nota_predicha': 70.0,
            'confianza': 40.0,
            'nivel_riesgo': 'medio',
            'factores_importantes': [{
                'factor': 'Datos insuficientes',
                'valor': 0,
                'impacto': 'neutro',
                'descripcion': 'No hay suficientes datos para hacer una predicción precisa'
            }],
            'caracteristicas_utilizadas': {},
            'metadata': {
                'modelo_version': '1.0_simple',
                'tipo_prediccion': 'por_defecto',
                'fecha_prediccion': date.today().isoformat(),
                'razon': 'datos_insuficientes'
            }
        }

    def guardar_prediccion(self, alumno, materia, prediccion, trimestre=None):
        """
        Guarda la predicción en la base de datos
        """
        if not trimestre:
            gestion_activa = Gestion.objects.filter(activa=True).order_by('-anio').first()
            if gestion_activa:
                trimestre = Trimestre.objects.filter(
                    gestion=gestion_activa,
                    fecha_inicio__lte=date.today(),
                    fecha_fin__gte=date.today()
                ).first()

                if not trimestre:
                    trimestre = Trimestre.objects.filter(gestion=gestion_activa).order_by('-numero').first()

        if not trimestre:
            print(f"No se pudo guardar predicción para {alumno.matricula}: no hay trimestre")
            return

        try:
            PrediccionRendimiento.objects.update_or_create(
                alumno=alumno,
                gestion=trimestre.gestion,
                trimestre=trimestre,
                materia=materia,
                defaults={
                    'nota_predicha': prediccion['nota_predicha'],
                    'confianza_prediccion': prediccion['confianza'],
                    'features_utilizados': prediccion['caracteristicas_utilizadas'],
                    'metadata': prediccion['metadata']
                }
            )
            print(f"✅ Predicción guardada: {alumno.matricula} - {materia.codigo}: {prediccion['nota_predicha']}")
        except Exception as e:
            print(f"❌ Error guardando predicción para {alumno.matricula}: {e}")

    # Métodos para compatibilidad con el código existente
    def entrenar_modelo(self):
        """Compatibility method - el modelo simple no necesita entrenamiento"""
        return True

    @property
    def modelo_entrenado(self):
        """El modelo simple siempre está 'entrenado'"""
        return True


# ********************************************************************************************************
# ********************************************************************************************************
# ********************************************************************************************************
# ********************************************************************************************************

# Alumnos:

def generar_prediccion_alumno(alumno, materia, gestion, trimestre=None):
    """
    Función básica para generar predicciones ML
    En una implementación real, aquí iría el modelo de ML entrenado
    """
    try:
        matriculacion = Matriculacion.objects.get(
            alumno=alumno,
            gestion=gestion,
            activa=True
        )

        # Recopilar características (features)
        features = _extraer_features_alumno(matriculacion, materia)

        # Modelo simple basado en promedios históricos y tendencias
        nota_predicha = _calcular_prediccion_simple(features)

        # Calcular confianza basada en cantidad de datos
        confianza = _calcular_confianza_prediccion(features)

        # Crear o actualizar predicción
        prediccion, created = PrediccionRendimiento.objects.update_or_create(
            alumno=alumno,
            materia=materia,
            gestion=gestion,
            trimestre=trimestre,
            defaults={
                'nota_predicha': nota_predicha,
                'confianza_prediccion': confianza,
                'features_utilizados': features,
                'metadata': {
                    'modelo_version': '1.0',
                    'fecha_entrenamiento': datetime.now().isoformat(),
                    'features_count': len(features)
                }
            }
        )

        return prediccion

    except Exception as e:
        print(f"Error generando predicción: {str(e)}")
        return None


def _extraer_features_alumno(matriculacion, materia):
    """Extrae características del alumno para el modelo ML"""
    features = {}

    # Features de notas
    notas_examenes = NotaExamen.objects.filter(
        matriculacion=matriculacion,
        examen__profesor_materia__materia=materia
    )

    notas_tareas = NotaTarea.objects.filter(
        matriculacion=matriculacion,
        tarea__profesor_materia__materia=materia
    )

    features['promedio_examenes'] = notas_examenes.aggregate(Avg('nota'))['nota__avg'] or 0
    features['promedio_tareas'] = notas_tareas.aggregate(Avg('nota'))['nota__avg'] or 0
    features['total_examenes'] = notas_examenes.count()
    features['total_tareas'] = notas_tareas.count()

    # Features de asistencia
    asistencias = Asistencia.objects.filter(
        matriculacion=matriculacion,
        horario__profesor_materia__materia=materia
    )

    total_clases = asistencias.count()
    asistencias_efectivas = asistencias.filter(estado__in=['P', 'T']).count()

    features['porcentaje_asistencia'] = (asistencias_efectivas / total_clases * 100) if total_clases > 0 else 0
    features['total_clases'] = total_clases

    # Features de participación
    participaciones = Participacion.objects.filter(
        matriculacion=matriculacion,
        horario__profesor_materia__materia=materia
    )

    features['promedio_participacion'] = participaciones.aggregate(Avg('valor'))['valor__avg'] or 0
    features['total_participaciones'] = participaciones.count()

    # Features temporales
    features['semanas_transcurridas'] = _calcular_semanas_transcurridas(matriculacion.gestion)

    return features


def _calcular_prediccion_simple(features):
    """Modelo simple de predicción basado en pesos"""
    # Pesos para cada característica
    peso_examenes = 0.4
    peso_tareas = 0.3
    peso_asistencia = 0.2
    peso_participacion = 0.1

    # Predicción base
    prediccion = (
            features['promedio_examenes'] * peso_examenes +
            features['promedio_tareas'] * peso_tareas +
            (features['porcentaje_asistencia'] / 100 * 100) * peso_asistencia +
            (features['promedio_participacion'] / 5 * 100) * peso_participacion
    )

    # Ajustes por tendencias
    if features['total_examenes'] > 3 and features['promedio_examenes'] > 80:
        prediccion += 2  # Bonus por consistencia alta
    elif features['total_examenes'] > 3 and features['promedio_examenes'] < 60:
        prediccion -= 3  # Penalización por bajo rendimiento

    if features['porcentaje_asistencia'] < 80:
        prediccion -= 5  # Penalización por baja asistencia

    # Limitar entre 0 y 100
    prediccion = max(0, min(100, prediccion))

    return round(prediccion, 2)


def _calcular_confianza_prediccion(features):
    """Calcula la confianza de la predicción basada en cantidad de datos"""
    base_confianza = 50

    # Aumentar confianza según datos disponibles
    if features['total_examenes'] >= 3:
        base_confianza += 15
    elif features['total_examenes'] >= 1:
        base_confianza += 5

    if features['total_tareas'] >= 3:
        base_confianza += 15
    elif features['total_tareas'] >= 1:
        base_confianza += 5

    if features['total_clases'] >= 10:
        base_confianza += 10
    elif features['total_clases'] >= 5:
        base_confianza += 5

    if features['total_participaciones'] >= 5:
        base_confianza += 5

    # Limitar entre 0 y 100
    confianza = max(0, min(100, base_confianza))

    return round(confianza, 2)


def _calcular_semanas_transcurridas(gestion):
    """Calcula semanas transcurridas desde el inicio de la gestión"""
    inicio = gestion.fecha_inicio
    ahora = datetime.now().date()

    if ahora < inicio:
        return 0

    diferencia = ahora - inicio
    semanas = diferencia.days // 7

    return semanas


