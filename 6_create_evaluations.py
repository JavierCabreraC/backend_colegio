import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from evaluations.models import Examen, Tarea, NotaExamen, NotaTarea
from academic.models import ProfesorMateria, Trimestre, Gestion, Matriculacion
from datetime import date, timedelta
import random
import time
from django.db import transaction


def create_evaluations_optimized():
    print("📝 Creando exámenes y tareas (optimizado)...")

    # Obtener datos necesarios
    gestion_2023 = Gestion.objects.get(anio=2023)
    trimestres = Trimestre.objects.filter(gestion=gestion_2023)
    profesor_materias = list(ProfesorMateria.objects.all())
    matriculaciones = list(Matriculacion.objects.filter(gestion=gestion_2023))

    print(f"📊 Datos a procesar:")
    print(f"   📚 Materias: {len(profesor_materias)}")
    print(f"   👨‍🎓 Estudiantes: {len(matriculaciones)}")
    print(f"   📊 Notas estimadas: {len(profesor_materias) * 3 * 4 * len(matriculaciones):,}")

    examenes_created = 0
    tareas_created = 0
    notas_examenes_created = 0
    notas_tareas_created = 0

    batch_size = 100  # Insertar notas en lotes

    for trimestre in trimestres:
        print(f"\n📆 {trimestre.nombre}")

        for i, profesor_materia in enumerate(profesor_materias):
            materia_nombre = profesor_materia.materia.nombre
            print(f"   📚 {materia_nombre} ({i + 1}/{len(profesor_materias)})")

            # Verificar si ya existen evaluaciones para esta materia/trimestre
            existing_examenes = Examen.objects.filter(
                profesor_materia=profesor_materia,
                trimestre=trimestre
            ).count()

            existing_tareas = Tarea.objects.filter(
                profesor_materia=profesor_materia,
                trimestre=trimestre
            ).count()

            # Crear exámenes solo si no existen
            examenes_to_create = max(0, 2 - existing_examenes)
            for num_examen in range(existing_examenes + 1, existing_examenes + examenes_to_create + 1):
                examen = create_examen_with_retry(profesor_materia, trimestre, num_examen, materia_nombre)
                if examen:
                    examenes_created += 1
                    # Crear notas en lotes
                    notas_created = create_notas_examen_batch(examen, matriculaciones, batch_size)
                    notas_examenes_created += notas_created
                    time.sleep(0.2)  # Pausa entre exámenes

            # Crear tareas solo si no existen
            tareas_to_create = max(0, 2 - existing_tareas)
            for num_tarea in range(existing_tareas + 1, existing_tareas + tareas_to_create + 1):
                tarea = create_tarea_with_retry(profesor_materia, trimestre, num_tarea, materia_nombre)
                if tarea:
                    tareas_created += 1
                    # Crear notas en lotes
                    notas_created = create_notas_tarea_batch(tarea, matriculaciones, batch_size)
                    notas_tareas_created += notas_created
                    time.sleep(0.2)  # Pausa entre tareas

            # Pausa entre materias
            time.sleep(0.5)

        print(f"   ✅ {trimestre.nombre} completado")
        time.sleep(1)  # Pausa entre trimestres

    print(f"\n📊 Resumen de evaluaciones creadas:")
    print(f"📝 Exámenes: {examenes_created}")
    print(f"📋 Tareas: {tareas_created}")
    print(f"📊 Notas de exámenes: {notas_examenes_created}")
    print(f"📊 Notas de tareas: {notas_tareas_created}")


def create_examen_with_retry(profesor_materia, trimestre, num_examen, materia_nombre, max_retries=3):
    """Crea un examen con reintentos"""
    for attempt in range(max_retries):
        try:
            dias_trimestre = (trimestre.fecha_fin - trimestre.fecha_inicio).days
            fecha_examen = trimestre.fecha_inicio + timedelta(
                days=random.randint(dias_trimestre // 4, 3 * dias_trimestre // 4)
            )

            examen = Examen.objects.create(
                profesor_materia=profesor_materia,
                trimestre=trimestre,
                numero_parcial=num_examen,
                titulo=f"Examen {num_examen} - {materia_nombre}",
                descripcion=f"Evaluación parcial {num_examen} de {materia_nombre}",
                fecha_examen=fecha_examen,
                ponderacion=50.0
            )
            return examen

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"      ❌ Error creando examen: {e}")
                return None
            time.sleep(1)
    return None


def create_tarea_with_retry(profesor_materia, trimestre, num_tarea, materia_nombre, max_retries=3):
    """Crea una tarea con reintentos"""
    for attempt in range(max_retries):
        try:
            dias_trimestre = (trimestre.fecha_fin - trimestre.fecha_inicio).days
            fecha_asignacion = trimestre.fecha_inicio + timedelta(
                days=random.randint(5, dias_trimestre // 2)
            )
            fecha_entrega = fecha_asignacion + timedelta(days=random.randint(3, 14))

            tarea = Tarea.objects.create(
                profesor_materia=profesor_materia,
                trimestre=trimestre,
                titulo=f"Tarea {num_tarea} - {materia_nombre}",
                descripcion=f"Actividad práctica {num_tarea}",
                fecha_asignacion=fecha_asignacion,
                fecha_entrega=fecha_entrega,
                ponderacion=25.0
            )
            return tarea

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"      ❌ Error creando tarea: {e}")
                return None
            time.sleep(1)
    return None


def create_notas_examen_batch(examen, matriculaciones, batch_size):
    """Crea notas de examen en lotes"""
    notas_to_create = []
    created_count = 0

    for matriculacion in matriculaciones:
        # Verificar si ya existe la nota
        if not NotaExamen.objects.filter(matriculacion=matriculacion, examen=examen).exists():
            nota = generate_realistic_grade()

            nota_examen = NotaExamen(
                matriculacion=matriculacion,
                examen=examen,
                nota=nota,
                observaciones=get_grade_comment(nota)
            )
            notas_to_create.append(nota_examen)

            # Insertar en lotes
            if len(notas_to_create) >= batch_size:
                created_count += bulk_create_with_retry(NotaExamen, notas_to_create)
                notas_to_create = []

    # Insertar notas restantes
    if notas_to_create:
        created_count += bulk_create_with_retry(NotaExamen, notas_to_create)

    return created_count


def create_notas_tarea_batch(tarea, matriculaciones, batch_size):
    """Crea notas de tarea en lotes"""
    notas_to_create = []
    created_count = 0

    for matriculacion in matriculaciones:
        # Verificar si ya existe la nota
        if not NotaTarea.objects.filter(matriculacion=matriculacion, tarea=tarea).exists():
            nota = generate_realistic_grade(is_homework=True)

            nota_tarea = NotaTarea(
                matriculacion=matriculacion,
                tarea=tarea,
                nota=nota,
                observaciones=get_grade_comment(nota)
            )
            notas_to_create.append(nota_tarea)

            # Insertar en lotes
            if len(notas_to_create) >= batch_size:
                created_count += bulk_create_with_retry(NotaTarea, notas_to_create)
                notas_to_create = []

    # Insertar notas restantes
    if notas_to_create:
        created_count += bulk_create_with_retry(NotaTarea, notas_to_create)

    return created_count


def bulk_create_with_retry(model_class, objects_list, max_retries=3):
    """Inserción masiva con reintentos"""
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                model_class.objects.bulk_create(objects_list, ignore_conflicts=True)
                return len(objects_list)
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"      ❌ Error en inserción masiva: {e}")
                return 0
            time.sleep(2 ** attempt)
    return 0


def generate_realistic_grade(is_homework=False):
    """Genera una nota realista con distribución normal"""
    if is_homework:
        base_grade = random.normalvariate(75, 15)
    else:
        base_grade = random.normalvariate(70, 20)

    grade = max(0, min(100, base_grade))
    return round(grade, 1)


def get_grade_comment(nota):
    """Retorna un comentario apropiado según la nota"""
    if nota >= 90:
        return "Excelente trabajo"
    elif nota >= 80:
        return "Muy buen desempeño"
    elif nota >= 70:
        return "Buen trabajo"
    elif nota >= 60:
        return "Satisfactorio"
    elif nota >= 51:
        return "Necesita mejorar"
    else:
        return "Requiere refuerzo"


if __name__ == '__main__':
    random.seed(2023)
    create_evaluations_optimized()