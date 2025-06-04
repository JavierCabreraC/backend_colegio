import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from academic.models import Horario, ProfesorMateria, Grupo, Aula, Trimestre, Gestion
from datetime import time
import random
import time as sleep_time
from django.db import transaction


def create_schedules_2024():
    print("📅 Creando horarios para año académico 2024...")

    # Obtener datos necesarios
    try:
        gestion_2024 = Gestion.objects.get(anio=2024)
        trimestres = Trimestre.objects.filter(gestion=gestion_2024)
        profesor_materias = list(ProfesorMateria.objects.all())
        grupos = list(Grupo.objects.all())
        aulas = list(Aula.objects.all())
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return

    print(f"📊 Datos disponibles:")
    print(f"   📚 Materias asignadas: {len(profesor_materias)}")
    print(f"   👥 Grupos: {len(grupos)}")
    print(f"   🏫 Aulas: {len(aulas)}")
    print(f"   📆 Trimestres 2024: {len(trimestres)}")

    # Horarios de clase (7 horas académicas)
    horarios_clase = [
        (time(7, 15), time(8, 0)),  # 1ra hora
        (time(8, 0), time(8, 45)),  # 2da hora
        (time(8, 45), time(9, 30)),  # 3ra hora
        (time(9, 45), time(10, 30)),  # 4ta hora (después del recreo)
        (time(10, 30), time(11, 15)),  # 5ta hora
        (time(11, 15), time(12, 0)),  # 6ta hora
        (time(12, 0), time(12, 45)),  # 7ma hora
    ]

    total_created = 0
    batch_size = 50

    for trimestre in trimestres:
        print(f"\n📆 Creando horarios para {trimestre.nombre}")

        # Verificar si ya existen horarios para este trimestre
        existing_schedules = Horario.objects.filter(trimestre=trimestre).count()
        if existing_schedules > 0:
            print(f"   ⚠️ Ya existen {existing_schedules} horarios. ¿Continuar? (se evitarán duplicados)")

        horarios_to_create = []

        for grupo in grupos:
            print(f"   📋 Procesando {grupo.nivel.numero}°{grupo.letra}...")

            # Distribuir materias equitativamente por semana
            materias_semana = distribute_subjects_weekly(profesor_materias, horarios_clase)

            for dia in range(1, 6):  # Lunes a Viernes
                dia_materias = materias_semana[dia - 1]

                for i, (hora_inicio, hora_fin) in enumerate(horarios_clase):
                    if i < len(dia_materias):
                        profesor_materia = dia_materias[i]
                        aula = select_appropriate_classroom(profesor_materia.materia.nombre, aulas)

                        # Verificar si ya existe este horario específico
                        if not Horario.objects.filter(
                                profesor_materia=profesor_materia,
                                grupo=grupo,
                                trimestre=trimestre,
                                dia_semana=dia,
                                hora_inicio=hora_inicio
                        ).exists():

                            horario = Horario(
                                profesor_materia=profesor_materia,
                                grupo=grupo,
                                aula=aula,
                                trimestre=trimestre,
                                dia_semana=dia,
                                hora_inicio=hora_inicio,
                                hora_fin=hora_fin
                            )
                            horarios_to_create.append(horario)

                            # Insertar en lotes
                            if len(horarios_to_create) >= batch_size:
                                created = bulk_create_schedules_safe(horarios_to_create)
                                total_created += created
                                horarios_to_create = []
                                sleep_time.sleep(0.2)

            # Pequeña pausa entre grupos
            sleep_time.sleep(0.3)

        # Insertar horarios restantes del trimestre
        if horarios_to_create:
            created = bulk_create_schedules_safe(horarios_to_create)
            total_created += created

        print(f"   ✅ {trimestre.nombre} completado")
        sleep_time.sleep(1)  # Pausa entre trimestres

    print(f"\n📊 Total horarios 2024 creados: {total_created}")

    # Estadísticas finales
    for trimestre in trimestres:
        count = Horario.objects.filter(trimestre=trimestre).count()
        print(f"📊 {trimestre.nombre}: {count} horarios")

    total_2024 = Horario.objects.filter(trimestre__gestion=gestion_2024).count()
    print(f"📊 Total horarios 2024 en BD: {total_2024}")


def distribute_subjects_weekly(profesor_materias, horarios_clase):
    """Distribuye las materias equitativamente durante la semana"""
    materias_por_dia = []
    total_horas_dia = len(horarios_clase)

    # Crear distribución balanceada para toda la semana
    materias_semana = []
    for _ in range(5 * total_horas_dia):  # 5 días × 7 horas
        materias_semana.extend(profesor_materias)

    random.shuffle(materias_semana)

    # Dividir por días
    for dia in range(5):
        inicio = dia * total_horas_dia
        fin = inicio + total_horas_dia
        materias_del_dia = materias_semana[inicio:fin]
        materias_por_dia.append(materias_del_dia)

    return materias_por_dia


def bulk_create_schedules_safe(horarios_list, max_retries=3):
    """Inserción masiva de horarios con manejo de errores"""
    if not horarios_list:
        return 0

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Filtrar duplicados básicos antes de insertar
                unique_horarios = []
                seen = set()

                for horario in horarios_list:
                    key = (
                        horario.profesor_materia_id,
                        horario.grupo_id,
                        horario.trimestre_id,
                        horario.dia_semana,
                        horario.hora_inicio
                    )
                    if key not in seen:
                        seen.add(key)
                        unique_horarios.append(horario)

                if unique_horarios:
                    Horario.objects.bulk_create(unique_horarios, ignore_conflicts=True)
                    return len(unique_horarios)
                return 0

        except Exception as e:
            print(f"      ⚠️ Error en lote (intento {attempt + 1}): {str(e)[:100]}...")
            if attempt == max_retries - 1:
                print(f"      ❌ Lote fallido después de {max_retries} intentos")
                return 0
            sleep_time.sleep(2 ** attempt)

    return 0


def select_appropriate_classroom(materia_nombre, aulas):
    """Selecciona el aula más apropiada según la materia"""
    # Asignaciones específicas por materia
    if any(word in materia_nombre for word in ['Física', 'Química', 'Biología']):
        lab_ciencias = next((a for a in aulas if 'Ciencias' in a.nombre), None)
        if lab_ciencias:
            return lab_ciencias

    elif 'Tecnología' in materia_nombre:
        lab_comp = next((a for a in aulas if 'Computación' in a.nombre), None)
        if lab_comp:
            return lab_comp

    elif 'Educación Física' in materia_nombre:
        gimnasio = next((a for a in aulas if 'Gimnasio' in a.nombre), None)
        if gimnasio:
            return gimnasio

    elif any(word in materia_nombre for word in ['Arte', 'Artística']):
        aula_arte = next((a for a in aulas if 'Arte' in a.nombre), None)
        if aula_arte:
            return aula_arte

    # Para otras materias, usar aulas regulares
    aulas_regulares = [a for a in aulas if a.nombre.startswith('Aula')]
    return random.choice(aulas_regulares) if aulas_regulares else random.choice(aulas)


if __name__ == '__main__':
    random.seed(2024)
    create_schedules_2024()