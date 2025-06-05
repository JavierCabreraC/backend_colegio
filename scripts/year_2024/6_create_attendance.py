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

from evaluations.models import Asistencia
from academic.models import Matriculacion, Horario, Gestion, Trimestre
from datetime import date, timedelta
import random
import time
from django.db import transaction


def create_attendance_2024():
    print("✅ Creando registros de asistencia para 2024...")

    # Obtener datos necesarios
    try:
        gestion_2024 = Gestion.objects.get(anio=2024)
        trimestres = Trimestre.objects.filter(gestion=gestion_2024)
        matriculaciones = list(Matriculacion.objects.filter(gestion=gestion_2024, activa=True))
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return

    print(f"📊 Estudiantes matriculados 2024: {len(matriculaciones)}")

    # Verificar si ya existen asistencias 2024
    existing_attendance = Asistencia.objects.filter(
        matriculacion__gestion=gestion_2024
    ).count()

    if existing_attendance > 0:
        print(f"⚠️ Ya existen {existing_attendance:,} registros de asistencia 2024")
        response = input("¿Continuar agregando más registros? (s/n): ").lower()
        if response != 's':
            return

    total_asistencias = 0
    batch_size = 200

    for trimestre in trimestres:
        print(f"\n📆 {trimestre.nombre}")

        # Obtener horarios del trimestre
        horarios = list(Horario.objects.filter(trimestre=trimestre))
        print(f"   📚 Horarios: {len(horarios)}")

        # Generar fechas de clases (hasta fecha actual o fin de trimestre)
        fechas_clases = generate_class_dates_2024(trimestre.fecha_inicio, trimestre.fecha_fin)
        print(f"   📅 Días de clases a procesar: {len(fechas_clases)}")

        if not fechas_clases:
            print(f"   ⚠️ No hay fechas de clases para este trimestre")
            continue

        asistencias_to_create = []

        for i, fecha in enumerate(fechas_clases):
            if i % 10 == 0:
                print(f"      📅 Procesando día {i + 1}/{len(fechas_clases)} ({fecha})")

            dia_semana = fecha.weekday() + 1
            horarios_dia = [h for h in horarios if h.dia_semana == dia_semana]

            for horario in horarios_dia:
                # Obtener estudiantes del grupo
                matriculaciones_grupo = [m for m in matriculaciones if m.alumno.grupo == horario.grupo]

                for matriculacion in matriculaciones_grupo:
                    # Verificar si ya existe (básico para evitar duplicados obvios)
                    if should_create_attendance_2024(matriculacion, horario, fecha):
                        estado = generate_attendance_status_2024(fecha, matriculacion)

                        asistencia = Asistencia(
                            matriculacion=matriculacion,
                            horario=horario,
                            fecha=fecha,
                            estado=estado
                        )
                        asistencias_to_create.append(asistencia)

                        # Insertar en lotes
                        if len(asistencias_to_create) >= batch_size:
                            created = bulk_create_attendance_2024(asistencias_to_create)
                            total_asistencias += created
                            asistencias_to_create = []
                            time.sleep(0.1)

            # Pausa cada 5 días
            if (i + 1) % 5 == 0:
                time.sleep(0.5)

        # Insertar asistencias restantes del trimestre
        if asistencias_to_create:
            created = bulk_create_attendance_2024(asistencias_to_create)
            total_asistencias += created

        print(f"   ✅ {trimestre.nombre} completado")
        time.sleep(2)

    print(f"\n📊 Total asistencias 2024 creadas: {total_asistencias:,}")

    # Estadísticas finales
    try:
        total_final = Asistencia.objects.filter(matriculacion__gestion=gestion_2024).count()
        print(f"📊 Total asistencias 2024 en BD: {total_final:,}")

        # Estadísticas por trimestre
        for trimestre in trimestres:
            count = Asistencia.objects.filter(
                horario__trimestre=trimestre
            ).count()
            print(f"📊 {trimestre.nombre}: {count:,} registros")

        # Distribución por estado
        print(f"\n📈 Distribución de asistencias 2024:")
        estados = ['P', 'F', 'T', 'J']
        nombres_estados = {'P': 'Presente', 'F': 'Falta', 'T': 'Tardanza', 'J': 'Justificada'}

        for estado in estados:
            count = Asistencia.objects.filter(
                matriculacion__gestion=gestion_2024,
                estado=estado
            ).count()
            porcentaje = (count / total_final * 100) if total_final > 0 else 0
            print(f"   {nombres_estados[estado]}: {count:,} ({porcentaje:.1f}%)")

    except Exception as e:
        print(f"⚠️ Error en estadísticas finales: {e}")


def generate_class_dates_2024(fecha_inicio, fecha_fin):
    """Genera fechas de clases hasta la fecha actual o fin de trimestre"""
    fechas = []
    fecha_actual = fecha_inicio
    hoy = date.today()

    # Solo generar hasta hoy o hasta el fin del trimestre
    fecha_limite = min(hoy, fecha_fin)

    while fecha_actual <= fecha_limite:
        if fecha_actual.weekday() < 5:  # Solo días de semana
            fechas.append(fecha_actual)
        fecha_actual += timedelta(days=1)

    return fechas


def should_create_attendance_2024(matriculacion, horario, fecha):
    """Verificación básica para evitar duplicados obvios"""
    # En lugar de verificar cada registro (costoso), confiar en ignore_conflicts
    return True


def generate_attendance_status_2024(fecha, matriculacion):
    """Genera estado de asistencia con variaciones por estudiante"""
    # Obtener un "perfil" del estudiante basado en su usuario.id para consistencia
    try:
        student_seed = matriculacion.alumno.usuario.id % 100
    except AttributeError:
        # Fallback en caso de que la estructura sea diferente
        student_seed = hash(matriculacion.alumno.matricula) % 100

    # Diferentes perfiles de asistencia
    if student_seed < 70:  # 70% estudiantes regulares
        # Asistencia normal: 88% presente
        rand = random.random()
        if rand < 0.88:
            return 'P'
        elif rand < 0.95:
            return 'F'
        elif rand < 0.98:
            return 'T'
        else:
            return 'J'

    elif student_seed < 85:  # 15% estudiantes con más faltas
        # Asistencia irregular: 75% presente
        rand = random.random()
        if rand < 0.75:
            return 'P'
        elif rand < 0.90:
            return 'F'
        elif rand < 0.96:
            return 'T'
        else:
            return 'J'

    else:  # 15% estudiantes muy regulares
        # Excelente asistencia: 95% presente
        rand = random.random()
        if rand < 0.95:
            return 'P'
        elif rand < 0.98:
            return 'T'
        elif rand < 0.99:
            return 'J'
        else:
            return 'F'


def bulk_create_attendance_2024(asistencias_list, max_retries=3):
    """Inserción masiva con reintentos"""
    if not asistencias_list:
        return 0

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Filtrar duplicados básicos
                unique_asistencias = []
                seen = set()

                for asistencia in asistencias_list:
                    key = (asistencia.matriculacion.id, asistencia.horario.id, asistencia.fecha)
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
                return 0
            time.sleep(2 ** attempt)

    return 0


if __name__ == '__main__':
    random.seed(2024)
    create_attendance_2024()