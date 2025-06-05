import os
import sys
import django
from pathlib import Path


# Configurar Django
def setup_django():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / 'manage.py').exists():
            break
        project_root = project_root.parent
    sys.path.insert(0, str(project_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
    django.setup()


setup_django()

from evaluations.models import (
    HistoricoTrimestral, HistoricoAnual, NotaExamen, NotaTarea,
    Asistencia, Participacion, EstadoMateria
)
from predictions.models import PrediccionRendimiento
from academic.models import Gestion, Trimestre, Materia, Matriculacion
from authentication.models import Alumno
from django.db.models import Avg, Count, Q
from django.db import transaction, connection
from decimal import Decimal
import random
import time
from datetime import datetime, timedelta


def create_historical_data():
    print("📊 Creando datos históricos y predicciones...")

    # Procesar cada año académico
    years = [2023, 2024, 2025]

    for year in years:
        try:
            gestion = Gestion.objects.get(anio=year)
            print(f"\n📅 Procesando año {year}...")

            # Crear históricos trimestrales
            create_trimestral_records(gestion)

            # Solo crear históricos anuales para años completos
            if year < 2025:  # 2025 no está completo
                create_annual_records(gestion)

            # Crear predicciones para todos los años
            create_predictions(gestion)

        except Gestion.DoesNotExist:
            print(f"⚠️ Gestión {year} no encontrada")
        except Exception as e:
            print(f"❌ Error procesando año {year}: {e}")
            # Intentar reconectar
            connection.close()
            time.sleep(2)

    show_final_statistics()


def create_trimestral_records(gestion):
    """Crea registros históricos trimestrales"""
    print(f"   📊 Creando históricos trimestrales para {gestion.anio}...")

    try:
        trimestres = list(Trimestre.objects.filter(gestion=gestion))
        materias = list(Materia.objects.all())
        matriculaciones = list(Matriculacion.objects.filter(gestion=gestion, activa=True))

        # Seleccionar solo algunos estudiantes (no todos)
        if len(matriculaciones) > 15:
            matriculaciones = random.sample(matriculaciones, 15)

        created_count = 0

        for trimestre in trimestres:
            print(f"      📆 {trimestre.nombre}")

            for matriculacion in matriculaciones:
                alumno = matriculacion.alumno

                # Seleccionar solo algunas materias por estudiante
                selected_materias = random.sample(materias, min(4, len(materias)))

                for materia in selected_materias:
                    # Verificar si ya existe
                    if HistoricoTrimestral.objects.filter(
                            alumno=alumno,
                            trimestre=trimestre,
                            materia=materia
                    ).exists():
                        continue

                    # Calcular promedios con manejo de errores
                    datos_calculados = calculate_trimestral_data_safe(matriculacion, trimestre, materia)

                    if datos_calculados:
                        try:
                            with transaction.atomic():
                                HistoricoTrimestral.objects.create(
                                    alumno=alumno,
                                    trimestre=trimestre,
                                    materia=materia,
                                    promedio_trimestre=datos_calculados['promedio_final'],
                                    promedio_examenes=datos_calculados['promedio_examenes'],
                                    promedio_tareas=datos_calculados['promedio_tareas'],
                                    porcentaje_asistencia=datos_calculados['porcentaje_asistencia'],
                                    num_participaciones=datos_calculados['num_participaciones'],
                                    observaciones=get_performance_comment(datos_calculados['promedio_final'])
                                )
                                created_count += 1
                        except Exception as e:
                            print(f"         ⚠️ Error creando registro: {str(e)[:80]}")

                    # Pausa para evitar saturar la BD
                    if created_count % 10 == 0:
                        time.sleep(0.2)

                # Pausa entre estudiantes
                time.sleep(0.1)

        print(f"      ✅ {created_count} registros trimestrales creados")

    except Exception as e:
        print(f"      ❌ Error en históricos trimestrales: {e}")


def calculate_trimestral_data_safe(matriculacion, trimestre, materia):
    """Calcula datos trimestrales con manejo seguro de tipos"""
    try:
        # Reintentos con reconexión en caso de error de BD
        for attempt in range(3):
            try:
                # Obtener notas de exámenes
                notas_examenes = NotaExamen.objects.filter(
                    matriculacion=matriculacion,
                    examen__trimestre=trimestre,
                    examen__profesor_materia__materia=materia
                )

                # Obtener notas de tareas
                notas_tareas = NotaTarea.objects.filter(
                    matriculacion=matriculacion,
                    tarea__trimestre=trimestre,
                    tarea__profesor_materia__materia=materia
                )

                # Calcular promedios con conversión segura de tipos
                promedio_examenes = None
                if notas_examenes.exists():
                    avg_examenes = notas_examenes.aggregate(Avg('nota'))['nota__avg']
                    if avg_examenes is not None:
                        promedio_examenes = float(avg_examenes)

                promedio_tareas = None
                if notas_tareas.exists():
                    avg_tareas = notas_tareas.aggregate(Avg('nota'))['nota__avg']
                    if avg_tareas is not None:
                        promedio_tareas = float(avg_tareas)

                # Calcular promedio final ponderado
                promedio_final = calculate_weighted_average_safe(promedio_examenes, promedio_tareas)

                # Obtener asistencias (con límite para evitar consultas muy grandes)
                asistencias = Asistencia.objects.filter(
                    matriculacion=matriculacion,
                    horario__trimestre=trimestre,
                    horario__profesor_materia__materia=materia
                )[:100]  # Limitar resultados

                # Calcular porcentaje de asistencia
                porcentaje_asistencia = None
                if asistencias.exists():
                    total_asistencias = asistencias.count()
                    if total_asistencias > 0:
                        presentes = asistencias.filter(estado='P').count()
                        porcentaje_asistencia = round((presentes / total_asistencias) * 100, 2)

                # Obtener participaciones (con límite)
                participaciones = Participacion.objects.filter(
                    matriculacion=matriculacion,
                    horario__trimestre=trimestre,
                    horario__profesor_materia__materia=materia
                )[:50]  # Limitar resultados

                num_participaciones = participaciones.count()

                if promedio_final is not None:
                    return {
                        'promedio_final': Decimal(str(promedio_final)),
                        'promedio_examenes': Decimal(str(promedio_examenes)) if promedio_examenes else None,
                        'promedio_tareas': Decimal(str(promedio_tareas)) if promedio_tareas else None,
                        'porcentaje_asistencia': Decimal(str(porcentaje_asistencia)) if porcentaje_asistencia else None,
                        'num_participaciones': num_participaciones
                    }

                break  # Salir del loop de reintentos si fue exitoso

            except Exception as e:
                print(f"         ⚠️ Intento {attempt + 1} falló: {str(e)[:60]}")
                if attempt == 2:  # Último intento
                    return None
                connection.close()  # Cerrar conexión para reconectar
                time.sleep(1)

    except Exception as e:
        print(f"Error calculando datos trimestrales: {e}")

    return None


def calculate_weighted_average_safe(promedio_examenes, promedio_tareas):
    """Calcula promedio ponderado con manejo seguro de tipos"""
    try:
        if promedio_examenes is not None and promedio_tareas is not None:
            return round((promedio_examenes * 0.8) + (promedio_tareas * 0.2), 2)
        elif promedio_examenes is not None:
            return round(promedio_examenes, 2)
        elif promedio_tareas is not None:
            return round(promedio_tareas, 2)
        else:
            return None
    except Exception as e:
        print(f"Error en promedio ponderado: {e}")
        return None


def create_annual_records(gestion):
    """Crea registros históricos anuales"""
    print(f"   📊 Creando históricos anuales para {gestion.anio}...")

    try:
        # Obtener estudiantes que tienen datos trimestrales
        estudiantes_con_datos = HistoricoTrimestral.objects.filter(
            trimestre__gestion=gestion
        ).values('alumno').distinct()[:10]  # Limitar a 10 estudiantes

        created_count = 0

        for estudiante_data in estudiantes_con_datos:
            try:
                alumno = Alumno.objects.get(pk=estudiante_data['alumno'])

                # Obtener materias que tienen datos trimestrales
                materias_con_datos = HistoricoTrimestral.objects.filter(
                    alumno=alumno,
                    trimestre__gestion=gestion
                ).values('materia').distinct()

                for materia_data in materias_con_datos:
                    materia = Materia.objects.get(pk=materia_data['materia'])

                    # Verificar si ya existe
                    if HistoricoAnual.objects.filter(
                            alumno=alumno,
                            gestion=gestion,
                            materia=materia
                    ).exists():
                        continue

                    # Calcular datos anuales
                    datos_anuales = calculate_annual_data_safe(alumno, gestion, materia)

                    if datos_anuales:
                        try:
                            with transaction.atomic():
                                HistoricoAnual.objects.create(
                                    alumno=alumno,
                                    gestion=gestion,
                                    materia=materia,
                                    promedio_anual=datos_anuales['promedio_anual'],
                                    promedio_t1=datos_anuales['promedio_t1'],
                                    promedio_t2=datos_anuales['promedio_t2'],
                                    promedio_t3=datos_anuales['promedio_t3'],
                                    porcentaje_asistencia_anual=datos_anuales['asistencia_anual'],
                                    total_participaciones=datos_anuales['total_participaciones'],
                                    estado_materia=determine_subject_status(datos_anuales['promedio_anual']),
                                    observaciones=get_annual_comment(datos_anuales['promedio_anual'])
                                )
                                created_count += 1
                        except Exception as e:
                            print(f"         ⚠️ Error: {e}")

                if created_count % 5 == 0:
                    time.sleep(0.3)

            except Exception as e:
                print(f"         ⚠️ Error procesando estudiante: {e}")

        print(f"      ✅ {created_count} registros anuales creados")

    except Exception as e:
        print(f"      ❌ Error en históricos anuales: {e}")


def calculate_annual_data_safe(alumno, gestion, materia):
    """Calcula datos anuales con manejo seguro"""
    try:
        registros_trimestrales = HistoricoTrimestral.objects.filter(
            alumno=alumno,
            trimestre__gestion=gestion,
            materia=materia
        ).order_by('trimestre__numero')

        if not registros_trimestrales.exists():
            return None

        promedios_trimestrales = []
        promedio_t1 = promedio_t2 = promedio_t3 = None
        total_participaciones = 0
        asistencias_ponderadas = []

        for registro in registros_trimestrales:
            promedios_trimestrales.append(float(registro.promedio_trimestre))
            total_participaciones += registro.num_participaciones

            if registro.porcentaje_asistencia:
                asistencias_ponderadas.append(float(registro.porcentaje_asistencia))

            # Asignar por trimestre
            if registro.trimestre.numero == 1:
                promedio_t1 = registro.promedio_trimestre
            elif registro.trimestre.numero == 2:
                promedio_t2 = registro.promedio_trimestre
            elif registro.trimestre.numero == 3:
                promedio_t3 = registro.promedio_trimestre

        # Calcular promedio anual
        promedio_anual = Decimal(str(round(sum(promedios_trimestrales) / len(promedios_trimestrales), 2)))

        # Calcular asistencia anual promedio
        asistencia_anual = None
        if asistencias_ponderadas:
            asistencia_anual = Decimal(str(round(sum(asistencias_ponderadas) / len(asistencias_ponderadas), 2)))

        return {
            'promedio_anual': promedio_anual,
            'promedio_t1': promedio_t1,
            'promedio_t2': promedio_t2,
            'promedio_t3': promedio_t3,
            'asistencia_anual': asistencia_anual,
            'total_participaciones': total_participaciones
        }
    except Exception as e:
        print(f"Error calculando datos anuales: {e}")
        return None


def create_predictions(gestion):
    """Crea predicciones de rendimiento"""
    print(f"   🔮 Creando predicciones para {gestion.anio}...")

    try:
        materias = list(Materia.objects.all())
        matriculaciones = list(Matriculacion.objects.filter(gestion=gestion, activa=True))

        # Seleccionar pocos estudiantes para predicciones
        if len(matriculaciones) > 8:
            matriculaciones = random.sample(matriculaciones, 8)

        created_count = 0

        for matriculacion in matriculaciones:
            alumno = matriculacion.alumno

            # Solo algunas materias por estudiante
            selected_materias = random.sample(materias, min(3, len(materias)))

            for materia in selected_materias:
                # 50% probabilidad de crear predicción
                if random.random() < 0.5:
                    try:
                        prediccion_data = generate_prediction_data_safe(alumno, gestion, materia)

                        with transaction.atomic():
                            PrediccionRendimiento.objects.create(
                                alumno=alumno,
                                gestion=gestion,
                                trimestre=get_random_trimestre_safe(gestion),
                                materia=materia,
                                nota_predicha=prediccion_data['nota_predicha'],
                                confianza_prediccion=prediccion_data['confianza'],
                                features_utilizados=prediccion_data['features'],
                                metadata=prediccion_data['metadata']
                            )
                            created_count += 1
                    except Exception as e:
                        print(f"         ⚠️ Error creando predicción: {str(e)[:60]}")

            if created_count % 5 == 0:
                time.sleep(0.2)

        print(f"      ✅ {created_count} predicciones creadas")

    except Exception as e:
        print(f"      ❌ Error en predicciones: {e}")


def generate_prediction_data_safe(alumno, gestion, materia):
    """Genera datos de predicción seguros"""
    try:
        # Obtener historial del estudiante
        historial_previo = HistoricoAnual.objects.filter(
            alumno=alumno,
            materia=materia,
            gestion__anio__lt=gestion.anio
        ).order_by('-gestion__anio').first()

        # Base para la predicción
        if historial_previo:
            base_nota = float(historial_previo.promedio_anual)
            nota_predicha = max(0, min(100, base_nota + random.uniform(-8, 8)))
            confianza = random.uniform(75, 90)
        else:
            nota_predicha = random.uniform(55, 80)
            confianza = random.uniform(60, 75)

        # Features simplificados
        features = {
            "nota_anterior": float(historial_previo.promedio_anual) if historial_previo else None,
            "asistencia_promedio": round(random.uniform(80, 95), 2),
            "nivel_academico": alumno.grupo.nivel.numero,
            "mes_prediccion": random.randint(1, 12)
        }

        # Metadata del modelo
        metadata = {
            "modelo_version": "1.0.0",
            "algoritmo": random.choice(["RandomForest", "LinearRegression"]),
            "fecha_entrenamiento": "2024-12-01",
            "precision_modelo": round(random.uniform(0.70, 0.85), 3)
        }

        return {
            'nota_predicha': Decimal(str(round(nota_predicha, 2))),
            'confianza': Decimal(str(round(confianza, 2))),
            'features': features,
            'metadata': metadata
        }
    except Exception as e:
        print(f"Error generando predicción: {e}")
        return {
            'nota_predicha': Decimal('70.00'),
            'confianza': Decimal('75.00'),
            'features': {},
            'metadata': {}
        }


def determine_subject_status(promedio_anual):
    """Determina el estado de la materia"""
    promedio_float = float(promedio_anual)
    if promedio_float >= 70:
        return EstadoMateria.APROBADO
    elif promedio_float >= 51:
        return EstadoMateria.EN_RECUPERACION
    else:
        return EstadoMateria.REPROBADO


def get_performance_comment(promedio):
    """Comentario según rendimiento"""
    promedio_float = float(promedio)
    if promedio_float >= 90:
        return "Rendimiento excelente"
    elif promedio_float >= 80:
        return "Buen rendimiento"
    elif promedio_float >= 70:
        return "Rendimiento satisfactorio"
    elif promedio_float >= 60:
        return "Rendimiento regular"
    else:
        return "Necesita apoyo"


def get_annual_comment(promedio_anual):
    """Comentario anual"""
    promedio_float = float(promedio_anual)
    if promedio_float >= 85:
        return "Estudiante destacado"
    elif promedio_float >= 70:
        return "Aprobado satisfactoriamente"
    elif promedio_float >= 51:
        return "En proceso de recuperación"
    else:
        return "Requiere plan de apoyo"


def get_random_trimestre_safe(gestion):
    """Obtiene trimestre aleatorio seguro"""
    try:
        trimestres = list(Trimestre.objects.filter(gestion=gestion))
        return random.choice(trimestres) if trimestres else None
    except:
        return None


def show_final_statistics():
    """Muestra estadísticas finales"""
    print(f"\n📊 ESTADÍSTICAS FINALES:")

    try:
        # Históricos trimestrales
        total_trimestral = HistoricoTrimestral.objects.count()
        print(f"📈 Registros históricos trimestrales: {total_trimestral}")

        # Históricos anuales
        total_anual = HistoricoAnual.objects.count()
        print(f"📊 Registros históricos anuales: {total_anual}")

        # Predicciones
        total_predicciones = PrediccionRendimiento.objects.count()
        print(f"🔮 Predicciones de rendimiento: {total_predicciones}")

        print(f"\n✅ Datos históricos y predicciones creados exitosamente")

    except Exception as e:
        print(f"⚠️ Error mostrando estadísticas: {e}")


if __name__ == '__main__':
    random.seed(2024)
    create_historical_data()