import numpy as np
import pandas as pd
from django.db.models import Avg
from datetime import date, datetime
from .models import PrediccionRendimiento
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from academic.models import Gestion, Trimestre, Matriculacion
from evaluations.models import NotaExamen, NotaTarea, Asistencia, Participacion, HistoricoTrimestral


class ModeloRendimientoML:
    """
    Motor de Machine Learning para predicciones de rendimiento académico
    Utiliza Random Forest para predecir notas futuras basándose en datos históricos
    """

    def __init__(self):
        self.modelo = None
        self.scaler = None
        self.feature_names = []
        self.modelo_entrenado = False
        self.precision = None

    def obtener_datos_entrenamiento(self):
        """
        Extrae datos históricos para entrenar el modelo
        Retorna: DataFrame con características y notas reales
        """
        datos_entrenamiento = []

        # Obtener gestiones anteriores (no la activa)
        gestiones_anteriores = Gestion.objects.filter(activa=False).order_by('-anio')[:3]

        for gestion in gestiones_anteriores:
            # Obtener todos los registros históricos trimestrales
            historicos = HistoricoTrimestral.objects.filter(
                trimestre__gestion=gestion
            ).select_related('alumno', 'trimestre', 'materia')

            for historico in historicos:
                caracteristicas = self.extraer_caracteristicas_alumno(
                    historico.alumno,
                    historico.materia,
                    historico.trimestre
                )

                if caracteristicas:
                    caracteristicas['nota_real'] = float(historico.promedio_trimestre)
                    datos_entrenamiento.append(caracteristicas)

        return pd.DataFrame(datos_entrenamiento)

    def extraer_caracteristicas_alumno(self, alumno, materia, trimestre):
        """
        Extrae características relevantes de un alumno para el modelo
        """
        try:
            # Obtener matriculación
            matriculacion = Matriculacion.objects.get(
                alumno=alumno,
                gestion=trimestre.gestion,
                activa=True
            )

            # 1. RENDIMIENTO ACADÉMICO PREVIO
            # Promedio trimestre anterior
            trimestre_anterior = Trimestre.objects.filter(
                gestion=trimestre.gestion,
                numero=trimestre.numero - 1
            ).first()

            promedio_anterior = 0
            if trimestre_anterior:
                hist_anterior = HistoricoTrimestral.objects.filter(
                    alumno=alumno,
                    trimestre=trimestre_anterior,
                    materia=materia
                ).first()
                promedio_anterior = float(hist_anterior.promedio_trimestre) if hist_anterior else 0

            # Promedios de exámenes y tareas del trimestre actual
            notas_examenes = NotaExamen.objects.filter(
                matriculacion=matriculacion,
                examen__profesor_materia__materia=materia,
                examen__trimestre=trimestre
            )

            notas_tareas = NotaTarea.objects.filter(
                matriculacion=matriculacion,
                tarea__profesor_materia__materia=materia,
                tarea__trimestre=trimestre
            )

            promedio_examenes = notas_examenes.aggregate(Avg('nota'))['nota__avg'] or 0
            promedio_tareas = notas_tareas.aggregate(Avg('nota'))['nota__avg'] or 0

            # 2. ASISTENCIA
            asistencias = Asistencia.objects.filter(
                matriculacion=matriculacion,
                horario__profesor_materia__materia=materia,
                horario__trimestre=trimestre
            )

            total_asistencias = asistencias.count()
            asistencias_efectivas = asistencias.filter(estado__in=['P', 'T']).count()
            porcentaje_asistencia = (asistencias_efectivas / total_asistencias * 100) if total_asistencias > 0 else 100

            # Faltas consecutivas máximas
            faltas_consecutivas = self.calcular_faltas_consecutivas(asistencias)

            # 3. PARTICIPACIÓN
            participaciones = Participacion.objects.filter(
                matriculacion=matriculacion,
                horario__profesor_materia__materia=materia,
                horario__trimestre=trimestre
            )

            total_participaciones = participaciones.count()
            promedio_participaciones = participaciones.aggregate(Avg('valor'))['valor__avg'] or 0

            # 4. TENDENCIAS TEMPORALES
            # Tendencia de las últimas 5 notas
            ultimas_notas = list(notas_examenes.order_by('examen__fecha_examen').values_list('nota', flat=True)[-5:])
            tendencia_notas = self.calcular_tendencia(ultimas_notas)

            # Días transcurridos en el trimestre
            dias_trimestre = (date.today() - trimestre.fecha_inicio).days
            progreso_trimestre = min(dias_trimestre / 90, 1.0)  # Normalizar a 0-1

            # 5. CONTEXTO ACADÉMICO
            # Edad del alumno
            edad_alumno = self.calcular_edad(alumno.fecha_nacimiento)

            # Dificultad histórica de la materia (promedio general de la materia)
            dificultad_materia = HistoricoTrimestral.objects.filter(
                materia=materia,
                trimestre__gestion=trimestre.gestion
            ).aggregate(Avg('promedio_trimestre'))['promedio_trimestre__avg'] or 70

            # Normalizar dificultad (0-1, donde 1 = más fácil)
            dificultad_normalizada = dificultad_materia / 100

            return {
                # Rendimiento previo
                'promedio_trimestre_anterior': promedio_anterior,
                'promedio_examenes_actual': float(promedio_examenes),
                'promedio_tareas_actual': float(promedio_tareas),
                'total_examenes': notas_examenes.count(),
                'total_tareas': notas_tareas.count(),

                # Asistencia
                'porcentaje_asistencia': porcentaje_asistencia,
                'total_asistencias': total_asistencias,
                'faltas_consecutivas_max': faltas_consecutivas,

                # Participación
                'total_participaciones': total_participaciones,
                'promedio_participaciones': float(promedio_participaciones),

                # Tendencias
                'tendencia_notas': tendencia_notas,
                'progreso_trimestre': progreso_trimestre,

                # Contexto
                'edad_alumno': edad_alumno,
                'dificultad_materia': float(dificultad_normalizada),

                # Información adicional
                'numero_trimestre': trimestre.numero,
                'semanas_transcurridas': min(dias_trimestre // 7, 12)
            }

        except Exception as e:
            print(f"Error extrayendo características para {alumno.matricula}: {e}")
            return None

    def calcular_faltas_consecutivas(self, asistencias):
        """Calcula el máximo de faltas consecutivas"""
        faltas = asistencias.filter(estado='F').order_by('fecha')
        if not faltas.exists():
            return 0

        max_consecutivas = 0
        consecutivas_actuales = 0
        fecha_anterior = None

        for falta in faltas:
            if fecha_anterior and (falta.fecha - fecha_anterior).days == 1:
                consecutivas_actuales += 1
            else:
                consecutivas_actuales = 1

            max_consecutivas = max(max_consecutivas, consecutivas_actuales)
            fecha_anterior = falta.fecha

        return max_consecutivas

    def calcular_tendencia(self, notas):
        """Calcula tendencia de notas: -1 (descendente), 0 (estable), 1 (ascendente)"""
        if len(notas) < 2:
            return 0

        # Calcular diferencias
        diferencias = [notas[i] - notas[i - 1] for i in range(1, len(notas))]
        promedio_diferencias = sum(diferencias) / len(diferencias)

        if promedio_diferencias > 2:
            return 1  # Ascendente
        elif promedio_diferencias < -2:
            return -1  # Descendente
        else:
            return 0  # Estable

    def calcular_edad(self, fecha_nacimiento):
        """Calcula edad en años"""
        if not fecha_nacimiento:
            return 15  # Edad promedio por defecto

        hoy = date.today()
        return hoy.year - fecha_nacimiento.year - (
                    (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

    def entrenar_modelo(self):
        """
        Entrena el modelo Random Forest con datos históricos
        """
        print("🤖 Iniciando entrenamiento del modelo ML...")

        # 1. Obtener datos de entrenamiento
        df = self.obtener_datos_entrenamiento()

        if df.empty:
            print("❌ No hay datos suficientes para entrenar el modelo")
            return False

        print(f"📊 Datos de entrenamiento: {len(df)} registros")

        # 2. Preparar características y target
        self.feature_names = [col for col in df.columns if col != 'nota_real']
        X = df[self.feature_names].fillna(0)
        y = df['nota_real']

        # 3. Dividir datos para entrenamiento y validación
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # 4. Normalizar datos
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 5. Entrenar Random Forest
        self.modelo = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )

        self.modelo.fit(X_train_scaled, y_train)

        # 6. Evaluar modelo
        y_pred = self.modelo.predict(X_test_scaled)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        self.precision = {
            'mae': round(mae, 2),
            'r2': round(r2, 3),
            'samples_train': len(X_train),
            'samples_test': len(X_test)
        }

        self.modelo_entrenado = True

        print(f"✅ Modelo entrenado exitosamente")
        print(f"📈 Error medio absoluto: {mae:.2f}")
        print(f"📊 R² Score: {r2:.3f}")

        return True

    def predecir_nota(self, alumno, materia, trimestre=None):
        """
        Hace una predicción de nota para un alumno en una materia específica
        """
        if not self.modelo_entrenado:
            # Intentar entrenar el modelo si no está entrenado
            if not self.entrenar_modelo():
                return self._prediccion_fallback(alumno, materia)

        # Usar trimestre actual si no se especifica
        if not trimestre:
            gestion_activa = Gestion.objects.filter(activa=True).first()
            if not gestion_activa:
                return self._prediccion_fallback(alumno, materia)

            trimestre = Trimestre.objects.filter(
                gestion=gestion_activa,
                fecha_inicio__lte=date.today(),
                fecha_fin__gte=date.today()
            ).first()

            if not trimestre:
                trimestre = Trimestre.objects.filter(gestion=gestion_activa).first()

        # Extraer características del alumno
        caracteristicas = self.extraer_caracteristicas_alumno(alumno, materia, trimestre)

        if not caracteristicas:
            return self._prediccion_fallback(alumno, materia)

        # Preparar datos para predicción
        X = pd.DataFrame([caracteristicas])
        X = X.reindex(columns=self.feature_names, fill_value=0)
        X_scaled = self.scaler.transform(X)

        # Hacer predicción
        nota_predicha = self.modelo.predict(X_scaled)[0]

        # Calcular confianza basada en la varianza de los árboles
        predicciones_arboles = [arbol.predict(X_scaled)[0] for arbol in self.modelo.estimators_]
        varianza = np.var(predicciones_arboles)
        confianza = max(0.5, min(0.95, 1 - (varianza / 100)))  # Entre 50% y 95%

        # Determinar factores más importantes
        importancias = self.modelo.feature_importances_
        factores_importantes = self._obtener_factores_clave(caracteristicas, importancias)

        # Clasificar nivel de riesgo
        nivel_riesgo = self._clasificar_riesgo(nota_predicha, caracteristicas)

        return {
            'nota_predicha': round(max(0, min(100, nota_predicha)), 2),
            'confianza': round(confianza * 100, 1),
            'nivel_riesgo': nivel_riesgo,
            'factores_importantes': factores_importantes,
            'caracteristicas_utilizadas': caracteristicas,
            'metadata': {
                'modelo_version': '1.0',
                'precision_mae': self.precision['mae'] if self.precision else None,
                'fecha_prediccion': date.today().isoformat()
            }
        }

    def _prediccion_fallback(self, alumno, materia):
        """
        Predicción básica cuando no hay modelo entrenado
        """
        # Calcular promedio histórico del alumno
        historicos = HistoricoTrimestral.objects.filter(
            alumno=alumno,
            materia=materia
        ).order_by('-trimestre__gestion__anio')[:3]

        if historicos.exists():
            promedio = sum(h.promedio_trimestre for h in historicos) / len(historicos)
        else:
            promedio = 70  # Promedio por defecto

        return {
            'nota_predicha': float(promedio),
            'confianza': 60.0,
            'nivel_riesgo': 'medio' if promedio < 70 else 'bajo',
            'factores_importantes': ['Sin datos suficientes para análisis detallado'],
            'caracteristicas_utilizadas': {},
            'metadata': {
                'modelo_version': 'fallback',
                'metodo': 'promedio_historico',
                'fecha_prediccion': date.today().isoformat()
            }
        }

    def _obtener_factores_clave(self, caracteristicas, importancias):
        """
        Identifica los factores más importantes para la predicción
        """
        factores_con_importancia = list(zip(self.feature_names, importancias))
        factores_ordenados = sorted(factores_con_importancia, key=lambda x: x[1], reverse=True)

        factores_clave = []
        for factor, importancia in factores_ordenados[:5]:  # Top 5
            if importancia > 0.05:  # Solo factores significativos
                valor = caracteristicas.get(factor, 0)
                descripcion = self._describir_factor(factor, valor)
                factores_clave.append({
                    'factor': factor,
                    'importancia': round(importancia * 100, 1),
                    'valor': valor,
                    'descripcion': descripcion
                })

        return factores_clave

    def _describir_factor(self, factor, valor):
        """
        Proporciona descripción legible de un factor
        """
        descripciones = {
            'promedio_trimestre_anterior': f"Promedio anterior: {valor:.1f}",
            'porcentaje_asistencia': f"Asistencia: {valor:.1f}%",
            'promedio_examenes_actual': f"Promedio exámenes: {valor:.1f}",
            'promedio_tareas_actual': f"Promedio tareas: {valor:.1f}",
            'total_participaciones': f"Participaciones: {valor}",
            'tendencia_notas': f"Tendencia: {'📈 Ascendente' if valor > 0 else '📉 Descendente' if valor < 0 else '➡️ Estable'}",
            'faltas_consecutivas_max': f"Máx. faltas consecutivas: {valor}"
        }

        return descripciones.get(factor, f"{factor}: {valor}")

    def _clasificar_riesgo(self, nota_predicha, caracteristicas):
        """
        Clasifica el nivel de riesgo del alumno
        """
        if nota_predicha < 50:
            return 'alto'
        elif nota_predicha < 70:
            return 'medio'
        else:
            return 'bajo'

    def guardar_prediccion(self, alumno, materia, prediccion, trimestre=None):
        """
        Guarda la predicción en la base de datos
        """
        if not trimestre:
            gestion_activa = Gestion.objects.filter(activa=True).first()
            trimestre = Trimestre.objects.filter(
                gestion=gestion_activa,
                fecha_inicio__lte=date.today(),
                fecha_fin__gte=date.today()
            ).first()

        PrediccionRendimiento.objects.update_or_create(
            alumno=alumno,
            gestion=trimestre.gestion if trimestre else None,
            trimestre=trimestre,
            materia=materia,
            defaults={
                'nota_predicha': prediccion['nota_predicha'],
                'confianza_prediccion': prediccion['confianza'],
                'features_utilizados': prediccion['caracteristicas_utilizadas'],
                'metadata': prediccion['metadata']
            }
        )


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


