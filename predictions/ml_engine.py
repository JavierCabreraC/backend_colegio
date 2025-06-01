# import pickle
# import numpy as np
# import pandas as pd
# from datetime import date, timedelta
# from sklearn.ensemble import RandomForestRegressor
# from sklearn.preprocessing import StandardScaler
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import mean_absolute_error, r2_score
# from django.db.models import Avg, Count, Max, Min
# from django.conf import settings
# import os
# import logging
#
# from academic.models import Gestion, Trimestre, Matriculacion, Horario
# from evaluations.models import NotaExamen, NotaTarea, Asistencia, Participacion, HistoricoTrimestral
# from authentication.models import Alumno
# from .models import PrediccionRendimiento
#
# logger = logging.getLogger(__name__)
#
#
# class ModeloRendimientoML:
#     """Motor de Machine Learning para predicciones de rendimiento académico"""
#
#     def __init__(self):
#         self.modelo = None
#         self.scaler = None
#         self.feature_names = None
#         self.modelo_entrenado = False
#         self.modelo_path = os.path.join(settings.BASE_DIR, 'ml_models')
#         self.crear_directorio_modelos()
#
#     def crear_directorio_modelos(self):
#         """Crear directorio para modelos si no existe"""
#         if not os.path.exists(self.modelo_path):
#             os.makedirs(self.modelo_path)
#
#     def obtener_features_alumno(self, alumno_id, materia_id, trimestre_id=None):
#         """Extraer características del alumno para el modelo"""
#         try:
#             alumno = Alumno.objects.get(usuario_id=alumno_id)
#             gestion_activa = Gestion.objects.filter(activa=True).first()
#
#             if not gestion_activa:
#                 return None
#
#             if not trimestre_id:
#                 # Usar trimestre actual
#                 trimestre_actual = Trimestre.objects.filter(
#                     gestion=gestion_activa,
#                     fecha_inicio__lte=date.today(),
#                     fecha_fin__gte=date.today()
#                 ).first()
#                 if not trimestre_actual:
#                     trimestre_actual = Trimestre.objects.filter(gestion=gestion_activa).first()
#             else:
#                 trimestre_actual = Trimestre.objects.get(id=trimestre_id)
#
#             if not trimestre_actual:
#                 return None
#
#             # Obtener matriculación activa
#             matriculacion = Matriculacion.objects.filter(
#                 alumno=alumno,
#                 gestion=gestion_activa,
#                 activa=True
#             ).first()
#
#             if not matriculacion:
#                 return None
#
#             # 1. CARACTERÍSTICAS DE RENDIMIENTO HISTÓRICO
#             notas_examenes = NotaExamen.objects.filter(
#                 matriculacion=matriculacion,
#                 examen__profesor_materia__materia_id=materia_id
#             ).values_list('nota', flat=True)
#
#             notas_tareas = NotaTarea.objects.filter(
#                 matriculacion=matriculacion,
#                 tarea__profesor_materia__materia_id=materia_id
#             ).values_list('nota', flat=True)
#
#             promedio_examenes = np.mean(list(notas_examenes)) if notas_examenes else 0
#             promedio_tareas = np.mean(list(notas_tareas)) if notas_tareas else 0
#             promedio_general = (promedio_examenes + promedio_tareas) / 2 if (
#                         promedio_examenes > 0 or promedio_tareas > 0) else 0
#
#             # 2. CARACTERÍSTICAS DE ASISTENCIA
#             asistencias = Asistencia.objects.filter(
#                 matriculacion=matriculacion,
#                 horario__profesor_materia__materia_id=materia_id
#             )
#
#             total_asistencias = asistencias.count()
#             presentes = asistencias.filter(estado__in=['P', 'T']).count()
#             porcentaje_asistencia = (presentes / total_asistencias * 100) if total_asistencias > 0 else 100
#
#             faltas_consecutivas = self.calcular_faltas_consecutivas(matriculacion, materia_id)
#
#             # 3. CARACTERÍSTICAS DE PARTICIPACIÓN
#             participaciones = Participacion.objects.filter(
#                 matriculacion=matriculacion,
#                 horario__profesor_materia__materia_id=materia_id
#             )
#
#             total_participaciones = participaciones.count()
#             promedio_participacion = participaciones.aggregate(Avg('valor'))['valor__avg'] or 0
#
#             # 4. TENDENCIAS TEMPORALES
#             tendencia_notas = self.calcular_tendencia_notas(notas_examenes, notas_tareas)
#             dias_desde_ultimo_examen = self.calcular_dias_ultimo_examen(matriculacion, materia_id)
#             semana_del_trimestre = self.calcular_semana_trimestre(trimestre_actual)
#
#             # 5. CONTEXTO DE LA MATERIA
#             dificultad_materia = self.calcular_dificultad_materia(materia_id, gestion_activa)
#             promedio_grupo_materia = self.calcular_promedio_grupo_materia(alumno.grupo, materia_id)
#
#             # 6. HISTÓRICO TRIMESTRAL
#             historico_trimestres = HistoricoTrimestral.objects.filter(
#                 alumno=alumno,
#                 materia_id=materia_id
#             ).order_by('-trimestre__gestion__anio', '-trimestre__numero')[:3]
#
#             promedio_historico = np.mean(
#                 [h.promedio_trimestre for h in historico_trimestres]) if historico_trimestres else 0
#
#             features = {
#                 # Rendimiento
#                 'promedio_examenes': float(promedio_examenes),
#                 'promedio_tareas': float(promedio_tareas),
#                 'promedio_general': float(promedio_general),
#                 'promedio_historico': float(promedio_historico),
#
#                 # Asistencia
#                 'porcentaje_asistencia': float(porcentaje_asistencia),
#                 'total_asistencias': int(total_asistencias),
#                 'faltas_consecutivas_max': int(faltas_consecutivas),
#
#                 # Participación
#                 'total_participaciones': int(total_participaciones),
#                 'promedio_participacion': float(promedio_participacion),
#
#                 # Tendencias
#                 'tendencia_notas': float(tendencia_notas),
#                 'dias_desde_ultimo_examen': int(dias_desde_ultimo_examen),
#                 'semana_del_trimestre': int(semana_del_trimestre),
#
#                 # Contexto
#                 'dificultad_materia': float(dificultad_materia),
#                 'promedio_grupo_materia': float(promedio_grupo_materia),
#
#                 # Metadata
#                 'total_examenes': len(notas_examenes),
#                 'total_tareas': len(notas_tareas)
#             }
#
#             return features
#
#         except Exception as e:
#             logger.error(f"Error obteniendo features para alumno {alumno_id}: {str(e)}")
#             return None
#
#     def calcular_faltas_consecutivas(self, matriculacion, materia_id):
#         """Calcular el máximo de faltas consecutivas"""
#         asistencias = Asistencia.objects.filter(
#             matriculacion=matriculacion,
#             horario__profesor_materia__materia_id=materia_id
#         ).order_by('fecha')
#
#         max_consecutivas = 0
#         consecutivas_actual = 0
#
#         for asistencia in asistencias:
#             if asistencia.estado == 'F':
#                 consecutivas_actual += 1
#                 max_consecutivas = max(max_consecutivas, consecutivas_actual)
#             else:
#                 consecutivas_actual = 0
#
#         return max_consecutivas
#
#     def calcular_tendencia_notas(self, notas_examenes, notas_tareas):
#         """Calcular tendencia de las últimas notas"""
#         todas_notas = list(notas_examenes) + list(notas_tareas)
#         if len(todas_notas) < 2:
#             return 0
#
#         # Tomar las últimas 5 notas
#         ultimas_notas = todas_notas[-5:]
#
#         # Calcular tendencia simple (diferencia entre promedio de últimas 2 vs primeras 2)
#         if len(ultimas_notas) >= 4:
#             promedio_inicial = np.mean(ultimas_notas[:2])
#             promedio_final = np.mean(ultimas_notas[-2:])
#             return promedio_final - promedio_inicial
#
#         return 0
#
#     def calcular_dias_ultimo_examen(self, matriculacion, materia_id):
#         """Calcular días desde el último examen"""
#         ultimo_examen = NotaExamen.objects.filter(
#             matriculacion=matriculacion,
#             examen__profesor_materia__materia_id=materia_id
#         ).order_by('-examen__fecha_examen').first()
#
#         if ultimo_examen:
#             return (date.today() - ultimo_examen.examen.fecha_examen).days
#
#         return 30  # Default si no hay exámenes
#
#     def calcular_semana_trimestre(self, trimestre):
#         """Calcular en qué semana del trimestre estamos"""
#         if not trimestre:
#             return 1
#
#         dias_transcurridos = (date.today() - trimestre.fecha_inicio).days
#         return min(max(dias_transcurridos // 7 + 1, 1), 12)
#
#     def calcular_dificultad_materia(self, materia_id, gestion):
#         """Calcular dificultad histórica de la materia"""
#         promedios_historicos = HistoricoTrimestral.objects.filter(
#             materia_id=materia_id,
#             trimestre__gestion=gestion
#         ).aggregate(promedio=Avg('promedio_trimestre'))
#
#         promedio_materia = promedios_historicos['promedio'] or 75
#
#         # Convertir a escala de dificultad (0-1, donde 1 es más difícil)
#         return max(0, (85 - promedio_materia) / 35)
#
#     def calcular_promedio_grupo_materia(self, grupo, materia_id):
#         """Calcular promedio del grupo en la materia"""
#         alumnos_grupo = Alumno.objects.filter(grupo=grupo)
#         gestion_activa = Gestion.objects.filter(activa=True).first()
#
#         matriculaciones = Matriculacion.objects.filter(
#             alumno__in=alumnos_grupo,
#             gestion=gestion_activa,
#             activa=True
#         )
#
#         notas_grupo = []
#         for matriculacion in matriculaciones:
#             notas_examenes = NotaExamen.objects.filter(
#                 matriculacion=matriculacion,
#                 examen__profesor_materia__materia_id=materia_id
#             ).values_list('nota', flat=True)
#
#             notas_tareas = NotaTarea.objects.filter(
#                 matriculacion=matriculacion,
#                 tarea__profesor_materia__materia_id=materia_id
#             ).values_list('nota', flat=True)
#
#             todas_notas = list(notas_examenes) + list(notas_tareas)
#             if todas_notas:
#                 notas_grupo.extend(todas_notas)
#
#         return np.mean(notas_grupo) if notas_grupo else 75
#
#     def entrenar_modelo(self):
#         """Entrenar el modelo Random Forest con datos históricos"""
#         try:
#             # Obtener datos de entrenamiento
#             datos_entrenamiento = self.preparar_datos_entrenamiento()
#
#             if len(datos_entrenamiento) < 50:
#                 logger.warning("Datos insuficientes para entrenar modelo")
#                 return False
#
#             # Preparar features y targets
#             df = pd.DataFrame(datos_entrenamiento)
#
#             feature_columns = [
#                 'promedio_examenes', 'promedio_tareas', 'promedio_general', 'promedio_historico',
#                 'porcentaje_asistencia', 'total_asistencias', 'faltas_consecutivas_max',
#                 'total_participaciones', 'promedio_participacion',
#                 'tendencia_notas', 'dias_desde_ultimo_examen', 'semana_del_trimestre',
#                 'dificultad_materia', 'promedio_grupo_materia',
#                 'total_examenes', 'total_tareas'
#             ]
#
#             X = df[feature_columns].fillna(0)
#             y = df['nota_real']
#
#             # Dividir datos
#             X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
#             # Normalizar features
#             self.scaler = StandardScaler()
#             X_train_scaled = self.scaler.fit_transform(X_train)
#             X_test_scaled = self.scaler.transform(X_test)
#
#             # Entrenar modelo Random Forest
#             self.modelo = RandomForestRegressor(
#                 n_estimators=100,
#                 max_depth=10,
#                 min_samples_split=5,
#                 min_samples_leaf=2,
#                 random_state=42
#             )
#
#             self.modelo.fit(X_train_scaled, y_train)
#
#             # Evaluar modelo
#             y_pred = self.modelo.predict(X_test_scaled)
#             mae = mean_absolute_error(y_test, y_pred)
#             r2 = r2_score(y_test, y_pred)
#
#             logger.info(f"Modelo entrenado - MAE: {mae:.2f}, R2: {r2:.2f}")
#
#             # Guardar modelo
#             self.feature_names = feature_columns
#             self.guardar_modelo()
#             self.modelo_entrenado = True
#
#             return True
#
#         except Exception as e:
#             logger.error(f"Error entrenando modelo: {str(e)}")
#             return False
#
#     def preparar_datos_entrenamiento(self):
#         """Preparar datos históricos para entrenamiento"""
#         datos = []
#
#         # Obtener gestiones anteriores (no la actual)
#         gestion_actual = Gestion.objects.filter(activa=True).first()
#         gestiones_pasadas = Gestion.objects.exclude(id=gestion_actual.id).order_by('-anio')[:3]
#
#         for gestion in gestiones_pasadas:
#             trimestres = Trimestre.objects.filter(gestion=gestion)
#
#             for trimestre in trimestres:
#                 historicos = HistoricoTrimestral.objects.filter(trimestre=trimestre)
#
#                 for historico in historicos:
#                     features = self.obtener_features_historico(historico)
#                     if features:
#                         features['nota_real'] = float(historico.promedio_trimestre)
#                         datos.append(features)
#
#         return datos
#
#     def obtener_features_historico(self, historico):
#         """Obtener features de un histórico trimestral"""
#         try:
#             # Simulación de features basado en histórico
#             # En un caso real, necesitarías acceso a los datos detallados
#             return {
#                 'promedio_examenes': float(historico.promedio_examenes or 0),
#                 'promedio_tareas': float(historico.promedio_tareas or 0),
#                 'promedio_general': float(historico.promedio_trimestre),
#                 'promedio_historico': float(historico.promedio_trimestre),
#                 'porcentaje_asistencia': float(historico.porcentaje_asistencia or 85),
#                 'total_asistencias': 20,  # Aproximación
#                 'faltas_consecutivas_max': max(0, int((100 - (historico.porcentaje_asistencia or 85)) / 10)),
#                 'total_participaciones': int(historico.num_participaciones),
#                 'promedio_participacion': 3.5,  # Aproximación
#                 'tendencia_notas': 0,  # Default
#                 'dias_desde_ultimo_examen': 15,  # Aproximación
#                 'semana_del_trimestre': 8,  # Aproximación
#                 'dificultad_materia': 0.5,  # Aproximación
#                 'promedio_grupo_materia': float(historico.promedio_trimestre),
#                 'total_examenes': 3,  # Aproximación
#                 'total_tareas': 2  # Aproximación
#             }
#         except:
#             return None
#
#     def cargar_modelo(self):
#         """Cargar modelo entrenado desde archivo"""
#         try:
#             modelo_file = os.path.join(self.modelo_path, 'modelo_rendimiento.pkl')
#             scaler_file = os.path.join(self.modelo_path, 'scaler.pkl')
#             features_file = os.path.join(self.modelo_path, 'feature_names.pkl')
#
#             if all(os.path.exists(f) for f in [modelo_file, scaler_file, features_file]):
#                 with open(modelo_file, 'rb') as f:
#                     self.modelo = pickle.load(f)
#                 with open(scaler_file, 'rb') as f:
#                     self.scaler = pickle.load(f)
#                 with open(features_file, 'rb') as f:
#                     self.feature_names = pickle.load(f)
#
#                 self.modelo_entrenado = True
#                 return True
#             else:
#                 # Si no existe modelo, entrenar uno nuevo
#                 return self.entrenar_modelo()
#
#         except Exception as e:
#             logger.error(f"Error cargando modelo: {str(e)}")
#             return self.entrenar_modelo()
#
#     def guardar_modelo(self):
#         """Guardar modelo entrenado"""
#         try:
#             modelo_file = os.path.join(self.modelo_path, 'modelo_rendimiento.pkl')
#             scaler_file = os.path.join(self.modelo_path, 'scaler.pkl')
#             features_file = os.path.join(self.modelo_path, 'feature_names.pkl')
#
#             with open(modelo_file, 'wb') as f:
#                 pickle.dump(self.modelo, f)
#             with open(scaler_file, 'wb') as f:
#                 pickle.dump(self.scaler, f)
#             with open(features_file, 'wb') as f:
#                 pickle.dump(self.feature_names, f)
#
#             logger.info("Modelo guardado exitosamente")
#
#         except Exception as e:
#             logger.error(f"Error guardando modelo: {str(e)}")
#
#     def predecir_nota(self, alumno_id, materia_id, trimestre_id=None):
#         """Realizar predicción para un alumno específico"""
#         if not self.modelo_entrenado:
#             if not self.cargar_modelo():
#                 return None
#
#         features = self.obtener_features_alumno(alumno_id, materia_id, trimestre_id)
#         if not features:
#             return None
#
#         try:
#             # Preparar datos para predicción
#             feature_array = np.array([[features[col] for col in self.feature_names]])
#             feature_array_scaled = self.scaler.transform(feature_array)
#
#             # Hacer predicción
#             nota_predicha = self.modelo.predict(feature_array_scaled)[0]
#
#             # Calcular confianza basada en la varianza de los árboles
#             predicciones_arboles = [tree.predict(feature_array_scaled)[0] for tree in self.modelo.estimators_]
#             confianza = max(0, 1 - (np.std(predicciones_arboles) / 20))  # Normalizar a 0-1
#
#             # Obtener importancia de características
#             feature_importance = dict(zip(self.feature_names, self.modelo.feature_importances_))
#             top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
#
#             return {
#                 'nota_predicha': round(max(0, min(100, nota_predicha)), 2),
#                 'confianza': round(confianza * 100, 2),
#                 'features_utilizados': features,
#                 'factores_importantes': [{'factor': k, 'importancia': round(v * 100, 2)} for k, v in top_features],
#                 'metadata': {
#                     'modelo_version': '1.0',
#                     'fecha_prediccion': date.today().isoformat(),
#                     'algoritmo': 'RandomForest'
#                 }
#             }
#
#         except Exception as e:
#             logger.error(f"Error en predicción: {str(e)}")
#             return None
#
#     def analizar_riesgo_alumno(self, prediccion):
#         """Analizar nivel de riesgo basado en la predicción"""
#         if not prediccion:
#             return 'desconocido'
#
#         nota = prediccion['nota_predicha']
#         confianza = prediccion['confianza']
#
#         if nota < 51:
#             return 'alto'  # Riesgo de reprobar
#         elif nota < 70:
#             return 'medio'  # Rendimiento bajo
#         elif nota < 85:
#             return 'bajo'  # Rendimiento aceptable
#         else:
#             return 'sin_riesgo'  # Buen rendimiento


import pickle
import numpy as np
import pandas as pd
from datetime import date, timedelta
from authentication.models import Alumno
from .models import PrediccionRendimiento
from django.db.models import Avg, Count, Q
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
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
