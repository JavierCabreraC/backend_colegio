import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from evaluations.models import Asistencia
from academic.models import Matriculacion, Horario, Gestion, Trimestre
from datetime import date, timedelta
import random
import time
from django.db import transaction


def create_attendance_optimized():
    print("✅ Creando registros de asistencia (optimizado)...")

    # Obtener datos necesarios
    gestion_2023 = Gestion.objects.get(anio=2023)
    trimestres = Trimestre.objects.filter(gestion=gestion_2023)
    matriculaciones = list(Matriculacion.objects.filter(gestion=gestion_2023))

    print(f"📊 Estudiantes matriculados: {len(matriculaciones)}")

    total_asistencias = 0
    batch_size = 200  # Insertar en lotes grandes para eficiencia

    for trimestre in trimestres:
        print(f"\n📆 {trimestre.nombre}")

        # Obtener horarios del trimestre
        horarios = list(Horario.objects.filter(trimestre=trimestre))
        print(f"   📚 Horarios del trimestre: {len(horarios)}")

        # Generar fechas de clases
        fechas_clases = generate_class_dates(trimestre.fecha_inicio, trimestre.fecha_fin)
        print(f"   📅 Días de clases: {len(fechas_clases)}")

        # Estimar total de registros para este trimestre
        total_estimado = len(fechas_clases) * len(horarios) * 10  # ~10 estudiantes por grupo
        print(f"   📊 Registros estimados: {total_estimado:,}")

        asistencias_to_create = []

        for i, fecha in enumerate(fechas_clases):
            if i % 10 == 0:  # Progreso cada 10 días
                print(f"      📅 Procesando día {i + 1}/{len(fechas_clases)} ({fecha})")

            dia_semana = fecha.weekday() + 1
            horarios_dia = [h for h in horarios if h.dia_semana == dia_semana]

            for horario in horarios_dia:
                # Obtener estudiantes del grupo
                matriculaciones_grupo = [m for m in matriculaciones if m.alumno.grupo == horario.grupo]

                for matriculacion in matriculaciones_grupo:
                    # Verificar si ya existe (solo verificar en DB cada cierto tiempo para eficiencia)
                    if not should_create_attendance(matriculacion, horario, fecha):
                        continue

                    estado = generate_attendance_status(fecha)

                    asistencia = Asistencia(
                        matriculacion=matriculacion,
                        horario=horario,
                        fecha=fecha,
                        estado=estado
                    )
                    asistencias_to_create.append(asistencia)

                    # Insertar en lotes
                    if len(asistencias_to_create) >= batch_size:
                        created = bulk_create_attendance_with_retry(asistencias_to_create)
                        total_asistencias += created
                        asistencias_to_create = []
                        time.sleep(0.1)  # Pequeña pausa

            # Pausa cada 5 días procesados
            if (i + 1) % 5 == 0:
                time.sleep(0.5)

        # Insertar asistencias restantes del trimestre
        if asistencias_to_create:
            created = bulk_create_attendance_with_retry(asistencias_to_create)
            total_asistencias += created

        print(f"   ✅ {trimestre.nombre} completado")
        time.sleep(2)  # Pausa más larga entre trimestres

    print(f"\n📊 Total registros de asistencia creados: {total_asistencias}")
    print(f"📊 Total registros en BD: {Asistencia.objects.count()}")

    # Estadísticas por trimestre
    for trimestre in trimestres:
        count = Asistencia.objects.filter(horario__trimestre=trimestre).count()
        print(f"📊 {trimestre.nombre}: {count:,} registros de asistencia")

    # Estadísticas por estado
    print("\n📈 Distribución de asistencias:")
    estados = ['P', 'F', 'T', 'J']
    nombres_estados = {'P': 'Presente', 'F': 'Falta', 'T': 'Tardanza', 'J': 'Justificada'}

    for estado in estados:
        count = Asistencia.objects.filter(estado=estado).count()
        porcentaje = (count / total_asistencias * 100) if total_asistencias > 0 else 0
        print(f"   {nombres_estados[estado]}: {count:,} ({porcentaje:.1f}%)")


def should_create_attendance(matriculacion, horario, fecha):
    """Verifica si se debe crear la asistencia (optimizado para reducir consultas)"""
    # En lugar de verificar cada registro individualmente, usar verificación por lotes
    # o confiar en ignore_conflicts=True en bulk_create
    return True


def bulk_create_attendance_with_retry(asistencias_list, max_retries=3):
    """Inserción masiva de asistencias con reintentos"""
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Filtrar duplicados básicos antes de insertar
                unique_asistencias = []
                seen = set()

                for asistencia in asistencias_list:
                    key = (asistencia.matriculacion_id, asistencia.horario_id, asistencia.fecha)
                    if key not in seen:
                        seen.add(key)
                        unique_asistencias.append(asistencia)

                if unique_asistencias:
                    Asistencia.objects.bulk_create(unique_asistencias, ignore_conflicts=True)
                    return len(unique_asistencias)
                return 0

        except Exception as e:
            print(f"      ⚠️ Error en lote (intento {attempt + 1}): {str(e)[:100]}...")
            if attempt == max_retries - 1:
                print(f"      ❌ Lote fallido después de {max_retries} intentos")
                return 0
            time.sleep(2 ** attempt)

    return 0


def generate_class_dates(fecha_inicio, fecha_fin):
    """Genera todas las fechas de clases (lunes a viernes) en el período"""
    fechas = []
    fecha_actual = fecha_inicio

    while fecha_actual <= fecha_fin:
        if fecha_actual.weekday() < 5:  # Solo días de semana
            fechas.append(fecha_actual)
        fecha_actual += timedelta(days=1)

    return fechas


def generate_attendance_status(fecha):
    """Genera un estado de asistencia realista"""
    rand = random.random()

    if rand < 0.85:
        return 'P'  # Presente
    elif rand < 0.93:
        return 'F'  # Falta
    elif rand < 0.98:
        return 'T'  # Tardanza
    else:
        return 'J'  # Justificada


if __name__ == '__main__':
    random.seed(2023)
    create_attendance_optimized()