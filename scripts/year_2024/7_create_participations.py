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

from evaluations.models import Participacion, Asistencia
from academic.models import Matriculacion, Gestion
import random
import time
from django.db import transaction


def create_participations_2024():
    print("🙋 Creando participaciones para 2024 (realistas - no todos participan igual)...")

    # Obtener datos necesarios
    try:
        gestion_2024 = Gestion.objects.get(anio=2024)
    except Exception as e:
        print(f"❌ Error obteniendo gestión 2024: {e}")
        return

    # Contar asistencias presentes 2024
    total_presentes = Asistencia.objects.filter(
        estado='P',
        matriculacion__gestion=gestion_2024
    ).count()

    print(f"📊 Total asistencias 'Presente' 2024: {total_presentes:,}")

    if total_presentes == 0:
        print("❌ No hay asistencias registradas para 2024. Ejecuta primero el script de asistencias.")
        return

    # Verificar participaciones existentes
    existing_participations = Participacion.objects.filter(
        matriculacion__gestion=gestion_2024
    ).count()

    print(f"📊 Participaciones existentes 2024: {existing_participations:,}")

    if existing_participations > 0:
        response = input("¿Continuar agregando participaciones? (s/n): ").lower()
        if response != 's':
            return

    # Clasificar estudiantes por perfil de participación
    matriculaciones = list(Matriculacion.objects.filter(gestion=gestion_2024, activa=True))
    student_profiles = classify_students_by_participation(matriculaciones)

    print(f"\n👥 Perfiles de participación:")
    for profile, students in student_profiles.items():
        print(f"   {profile}: {len(students)} estudiantes")

    batch_size = 1000  # Procesar asistencias en lotes
    participation_batch_size = 150
    total_participaciones = 0
    offset = 0

    participaciones_to_create = []

    while offset < total_presentes:
        print(f"📈 Procesando lote {offset:,} - {min(offset + batch_size, total_presentes):,}")

        try:
            # Obtener lote de asistencias presentes
            asistencias_lote = Asistencia.objects.filter(
                estado='P',
                matriculacion__gestion=gestion_2024
            ).select_related('matriculacion')[offset:offset + batch_size]

            asistencias_list = list(asistencias_lote)

            for asistencia in asistencias_list:
                # Determinar probabilidad de participación según el perfil del estudiante
                participation_chance = get_participation_chance_for_student(
                    asistencia.matriculacion, student_profiles
                )

                if random.random() < participation_chance:
                    descripcion, valor = generate_participation_data_2024()

                    participacion = Participacion(
                        matriculacion_id=asistencia.matriculacion_id,
                        horario_id=asistencia.horario_id,
                        fecha=asistencia.fecha,
                        descripcion=descripcion,
                        valor=valor
                    )
                    participaciones_to_create.append(participacion)

                    # Insertar en lotes
                    if len(participaciones_to_create) >= participation_batch_size:
                        created = bulk_create_participations_2024(participaciones_to_create)
                        total_participaciones += created
                        participaciones_to_create = []
                        time.sleep(0.2)

            offset += batch_size
            time.sleep(0.5)

        except Exception as e:
            print(f"   ❌ Error en lote {offset}: {e}")
            offset += batch_size  # Continuar con el siguiente lote
            time.sleep(2)

    # Insertar participaciones restantes
    if participaciones_to_create:
        created = bulk_create_participations_2024(participaciones_to_create)
        total_participaciones += created

    print(f"\n📊 Total participaciones 2024 creadas: {total_participaciones:,}")

    # Estadísticas finales
    try:
        total_final = Participacion.objects.filter(matriculacion__gestion=gestion_2024).count()
        print(f"📊 Total participaciones 2024 en BD: {total_final:,}")

        # Porcentaje de participación general
        porcentaje_general = (total_final / total_presentes * 100) if total_presentes > 0 else 0
        print(f"📊 Porcentaje general de participación: {porcentaje_general:.1f}%")

        # Distribución por valor
        print(f"\n📈 Distribución por valor de participación:")
        for valor in range(1, 6):
            count = Participacion.objects.filter(
                matriculacion__gestion=gestion_2024,
                valor=valor
            ).count()
            porcentaje = (count / total_final * 100) if total_final > 0 else 0
            descripcion_valor = get_participation_description(valor)
            print(f"   Valor {valor} ({descripcion_valor}): {count:,} ({porcentaje:.1f}%)")

        # Análisis por perfil de estudiante
        print(f"\n👥 Participación por perfil de estudiante:")
        analyze_participation_by_profile(student_profiles, gestion_2024)

    except Exception as e:
        print(f"⚠️ Error en estadísticas finales: {e}")


def classify_students_by_participation(matriculaciones):
    """Clasifica estudiantes en perfiles de participación realistas"""
    profiles = {
        'Muy Activos (40-60%)': [],
        'Activos (25-40%)': [],
        'Promedio (15-25%)': [],
        'Tímidos (5-15%)': [],
        'Muy Tímidos (0-5%)': []
    }

    for matriculacion in matriculaciones:
        # Usar usuario.id del alumno para asignar perfil consistente
        student_seed = matriculacion.alumno.usuario.id % 100

        if student_seed < 10:  # 10% muy activos
            profiles['Muy Activos (40-60%)'].append(matriculacion)
        elif student_seed < 30:  # 20% activos
            profiles['Activos (25-40%)'].append(matriculacion)
        elif student_seed < 65:  # 35% promedio
            profiles['Promedio (15-25%)'].append(matriculacion)
        elif student_seed < 90:  # 25% tímidos
            profiles['Tímidos (5-15%)'].append(matriculacion)
        else:  # 10% muy tímidos
            profiles['Muy Tímidos (0-5%)'].append(matriculacion)

    return profiles


def get_participation_chance_for_student(matriculacion, student_profiles):
    """Retorna la probabilidad de participación según el perfil del estudiante"""
    for profile_name, students in student_profiles.items():
        if matriculacion in students:
            if 'Muy Activos' in profile_name:
                return random.uniform(0.40, 0.60)  # 40-60%
            elif 'Activos' in profile_name:
                return random.uniform(0.25, 0.40)  # 25-40%
            elif 'Promedio' in profile_name:
                return random.uniform(0.15, 0.25)  # 15-25%
            elif 'Tímidos' in profile_name and 'Muy' not in profile_name:
                return random.uniform(0.05, 0.15)  # 5-15%
            else:  # Muy Tímidos
                return random.uniform(0.00, 0.05)  # 0-5%

    return 0.20  # Default 20%


def generate_participation_data_2024():
    """Genera descripción y valor realista de participación para 2024"""
    participaciones_tipos = [
        ("Respuesta correcta", [4, 5]),
        ("Pregunta interesante", [3, 4, 5]),
        ("Participación voluntaria", [3, 4]),
        ("Ayuda a compañeros", [4, 5]),
        ("Presentación grupal", [3, 4, 5]),
        ("Respuesta parcial", [2, 3]),
        ("Intento de respuesta", [2, 3]),
        ("Debate constructivo", [3, 4, 5]),
        ("Explicación clara", [4, 5]),
        ("Corrección oportuna", [3, 4]),
        ("Pregunta reflexiva", [3, 4, 5]),
        ("Iniciativa propia", [4, 5]),
        ("Comentario relevante", [3, 4]),
        ("Propuesta creativa", [4, 5])
    ]

    descripcion, valores_posibles = random.choice(participaciones_tipos)
    valor = random.choice(valores_posibles)

    return descripcion, valor


def bulk_create_participations_2024(participaciones_list, max_retries=3):
    """Inserción masiva con reintentos"""
    if not participaciones_list:
        return 0

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Filtrar duplicados básicos
                unique_participaciones = []
                seen = set()

                for participacion in participaciones_list:
                    key = (participacion.matriculacion_id, participacion.horario_id, participacion.fecha)
                    if key not in seen:
                        seen.add(key)
                        unique_participaciones.append(participacion)

                if unique_participaciones:
                    Participacion.objects.bulk_create(unique_participaciones, ignore_conflicts=True)
                    return len(unique_participaciones)
                return 0

        except Exception as e:
            print(f"      ⚠️ Error en lote (intento {attempt + 1}): {str(e)[:80]}...")
            if attempt == max_retries - 1:
                return 0
            time.sleep(2 ** attempt)

    return 0


def analyze_participation_by_profile(student_profiles, gestion):
    """Analiza participación real por perfil de estudiante"""
    for profile_name, students in student_profiles.items():
        if not students:
            continue

        student_ids = [s.id for s in students]
        total_participaciones = Participacion.objects.filter(
            matriculacion__in=student_ids,
            matriculacion__gestion=gestion
        ).count()

        total_asistencias = Asistencia.objects.filter(
            matriculacion__in=student_ids,
            matriculacion__gestion=gestion,
            estado='P'
        ).count()

        porcentaje = (total_participaciones / total_asistencias * 100) if total_asistencias > 0 else 0
        print(f"   {profile_name}: {porcentaje:.1f}% de participación real")


def get_participation_description(valor):
    """Retorna descripción del valor de participación"""
    descripciones = {
        1: "Muy básica",
        2: "Básica",
        3: "Regular",
        4: "Buena",
        5: "Excelente"
    }
    return descripciones.get(valor, "Unknown")


if __name__ == '__main__':
    random.seed(2024)
    create_participations_2024()