import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from academic.models import Horario, ProfesorMateria, Grupo, Aula, Trimestre, Gestion
from datetime import time
import random
import time as sleep_time
from django.db import transaction


def create_schedules():
    print("📅 Creando horarios académicos (optimizado)...")

    # Obtener datos necesarios
    gestion_2023 = Gestion.objects.get(anio=2023)
    trimestres = Trimestre.objects.filter(gestion=gestion_2023)
    profesor_materias = list(ProfesorMateria.objects.all())
    grupos = list(Grupo.objects.all())
    aulas = list(Aula.objects.all())

    print(f"📊 Datos disponibles:")
    print(f"   📚 Materias asignadas: {len(profesor_materias)}")
    print(f"   👥 Grupos: {len(grupos)}")
    print(f"   🏫 Aulas: {len(aulas)}")

    # Horarios de clase (sin recreo)
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
    batch_size = 50  # Insertar en lotes de 50

    for trimestre in trimestres:
        print(f"\n📆 {trimestre.nombre}")
        horarios_to_create = []

        for grupo in grupos:
            print(f"   📋 Procesando {grupo.nivel.numero}°{grupo.letra}...")

            # Distribuir materias equitativamente por semana
            materias_semana = distribute_subjects_weekly(profesor_materias, horarios_clase)

            # Para cada día de la semana (Lunes=1 a Viernes=5)
            for dia in range(1, 6):
                dia_materias = materias_semana[dia - 1]  # Obtener materias del día

                # Asignar cada materia a su horario correspondiente
                for i, (hora_inicio, hora_fin) in enumerate(horarios_clase):
                    if i < len(dia_materias):
                        profesor_materia = dia_materias[i]
                        aula = select_appropriate_classroom(profesor_materia.materia.nombre, aulas)

                        # Crear objeto sin guardar aún
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

                        # Insertar en lotes para evitar sobrecarga
                        if len(horarios_to_create) >= batch_size:
                            total_created += bulk_create_with_retry(horarios_to_create)
                            horarios_to_create = []
                            sleep_time.sleep(0.1)  # Pequeña pausa

        # Insertar horarios restantes del trimestre
        if horarios_to_create:
            total_created += bulk_create_with_retry(horarios_to_create)
            horarios_to_create = []

        print(f"   ✅ {trimestre.nombre} completado")
        sleep_time.sleep(0.5)  # Pausa entre trimestres

    print(f"\n📊 Total horarios creados: {total_created}")
    print(f"📊 Total horarios en BD: {Horario.objects.count()}")

    # Mostrar estadísticas por trimestre
    for trimestre in trimestres:
        count = Horario.objects.filter(trimestre=trimestre).count()
        print(f"📊 {trimestre.nombre}: {count} horarios")


def distribute_subjects_weekly(profesor_materias, horarios_clase):
    """Distribuye las materias equitativamente durante la semana"""
    materias_por_dia = []
    total_horas_dia = len(horarios_clase)

    # Crear una lista balanceada de materias para toda la semana
    materias_semana = []
    for _ in range(5 * total_horas_dia):  # 5 días × 7 horas
        materias_semana.extend(profesor_materias)

    # Mezclar para variedad
    random.shuffle(materias_semana)

    # Dividir por días
    for dia in range(5):
        inicio = dia * total_horas_dia
        fin = inicio + total_horas_dia
        materias_del_dia = materias_semana[inicio:fin]
        materias_por_dia.append(materias_del_dia)

    return materias_por_dia


def bulk_create_with_retry(horarios_list, max_retries=3):
    """Inserta horarios en lotes con reintentos en caso de error"""
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Filtrar duplicados antes de insertar
                horarios_unicos = []
                for horario in horarios_list:
                    if not Horario.objects.filter(
                            profesor_materia=horario.profesor_materia,
                            grupo=horario.grupo,
                            trimestre=horario.trimestre,
                            dia_semana=horario.dia_semana,
                            hora_inicio=horario.hora_inicio
                    ).exists():
                        horarios_unicos.append(horario)

                if horarios_unicos:
                    Horario.objects.bulk_create(horarios_unicos, ignore_conflicts=True)
                    return len(horarios_unicos)
                return 0

        except Exception as e:
            print(f"   ⚠️ Error en intento {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:
                print(f"   ❌ Falló después de {max_retries} intentos")
                return 0
            sleep_time.sleep(1)  # Esperar antes del siguiente intento

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
    # Establecer semilla para reproducibilidad
    random.seed(42)
    create_schedules()