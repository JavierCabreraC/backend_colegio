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


def create_evaluations_2024():
    print("📝 Creando evaluaciones para 2024 (2 exámenes + 1 tarea por trimestre)...")

    # Obtener datos necesarios
    try:
        gestion_2024 = Gestion.objects.get(anio=2024)
        trimestres = Trimestre.objects.filter(gestion=gestion_2024)
        profesor_materias = list(ProfesorMateria.objects.all())
        matriculaciones = list(Matriculacion.objects.filter(gestion=gestion_2024))
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return

    print(f"📊 Datos a procesar:")
    print(f"   📚 Materias: {len(profesor_materias)}")
    print(f"   👨‍🎓 Estudiantes 2024: {len(matriculaciones)}")
    print(f"   📆 Trimestres: {len(trimestres)}")
    # 2 exámenes + 1 tarea = 3 evaluaciones por materia por trimestre
    total_evaluaciones = len(profesor_materias) * len(trimestres) * 3
    total_notas = total_evaluaciones * len(matriculaciones)
    print(f"   📊 Evaluaciones estimadas: {total_evaluaciones}")
    print(f"   📊 Notas estimadas: {total_notas:,}")

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

            # Verificar evaluaciones existentes
            existing_examenes = Examen.objects.filter(
                profesor_materia=profesor_materia,
                trimestre=trimestre
            ).count()

            existing_tareas = Tarea.objects.filter(
                profesor_materia=profesor_materia,
                trimestre=trimestre
            ).count()

            # Crear 2 exámenes por trimestre (solo si no existen)
            examenes_needed = max(0, 2 - existing_examenes)
            for num_examen in range(existing_examenes + 1, existing_examenes + examenes_needed + 1):
                examen = create_examen_2024(profesor_materia, trimestre, num_examen, materia_nombre)
                if examen:
                    examenes_created += 1
                    # Crear notas en lotes
                    notas_created = create_notas_examen_batch_2024(examen, matriculaciones, batch_size)
                    notas_examenes_created += notas_created
                    time.sleep(0.3)

            # Crear 1 tarea por trimestre (solo si no existe)
            tareas_needed = max(0, 1 - existing_tareas)
            if tareas_needed > 0:
                tarea = create_tarea_2024(profesor_materia, trimestre, materia_nombre)
                if tarea:
                    tareas_created += 1
                    # Crear notas en lotes
                    notas_created = create_notas_tarea_batch_2024(tarea, matriculaciones, batch_size)
                    notas_tareas_created += notas_created
                    time.sleep(0.3)

            # Pausa entre materias
            time.sleep(0.5)

        print(f"   ✅ {trimestre.nombre} completado")
        time.sleep(2)  # Pausa más larga entre trimestres

    print(f"\n📊 Resumen de evaluaciones 2024:")
    print(f"📝 Exámenes creados: {examenes_created}")
    print(f"📋 Tareas creadas: {tareas_created}")
    print(f"📊 Notas de exámenes: {notas_examenes_created}")
    print(f"📊 Notas de tareas: {notas_tareas_created}")

    # Estadísticas por trimestre
    for trimestre in trimestres:
        examenes_count = Examen.objects.filter(trimestre=trimestre).count()
        tareas_count = Tarea.objects.filter(trimestre=trimestre).count()
        print(f"📊 {trimestre.nombre}: {examenes_count} exámenes, {tareas_count} tareas")


def create_examen_2024(profesor_materia, trimestre, num_examen, materia_nombre, max_retries=3):
    """Crea un examen con reintentos"""
    for attempt in range(max_retries):
        try:
            dias_trimestre = (trimestre.fecha_fin - trimestre.fecha_inicio).days
            # Distribuir exámenes a lo largo del trimestre
            if num_examen == 1:
                # Primer examen en el primer tercio
                inicio_rango = dias_trimestre // 4
                fin_rango = dias_trimestre // 2
            else:
                # Segundo examen en el último tercio
                inicio_rango = (2 * dias_trimestre) // 3
                fin_rango = (3 * dias_trimestre) // 4

            fecha_examen = trimestre.fecha_inicio + timedelta(
                days=random.randint(inicio_rango, fin_rango)
            )

            examen = Examen.objects.create(
                profesor_materia=profesor_materia,
                trimestre=trimestre,
                numero_parcial=num_examen,
                titulo=f"Examen {num_examen} - {materia_nombre} 2024",
                descripcion=f"Evaluación parcial {num_examen} de {materia_nombre}",
                fecha_examen=fecha_examen,
                ponderacion=40.0  # 40% cada examen (80% total)
            )
            return examen

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"      ❌ Error creando examen: {e}")
                return None
            time.sleep(1)
    return None


def create_tarea_2024(profesor_materia, trimestre, materia_nombre, max_retries=3):
    """Crea una tarea con reintentos"""
    for attempt in range(max_retries):
        try:
            dias_trimestre = (trimestre.fecha_fin - trimestre.fecha_inicio).days
            # Tarea en la mitad del trimestre
            fecha_asignacion = trimestre.fecha_inicio + timedelta(
                days=random.randint(dias_trimestre // 3, 2 * dias_trimestre // 3)
            )
            fecha_entrega = fecha_asignacion + timedelta(days=random.randint(7, 14))

            tarea = Tarea.objects.create(
                profesor_materia=profesor_materia,
                trimestre=trimestre,
                titulo=f"Proyecto - {materia_nombre} 2024",
                descripcion=f"Actividad integral de {materia_nombre}",
                fecha_asignacion=fecha_asignacion,
                fecha_entrega=fecha_entrega,
                ponderacion=20.0  # 20% la tarea
            )
            return tarea

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"      ❌ Error creando tarea: {e}")
                return None
            time.sleep(1)
    return None


def create_notas_examen_batch_2024(examen, matriculaciones, batch_size):
    """Crea notas de examen en lotes para 2024"""
    notas_to_create = []
    created_count = 0

    for matriculacion in matriculaciones:
        if not NotaExamen.objects.filter(matriculacion=matriculacion, examen=examen).exists():
            nota = generate_realistic_grade_2024()

            nota_examen = NotaExamen(
                matriculacion=matriculacion,
                examen=examen,
                nota=nota,
                observaciones=get_grade_comment_2024(nota)
            )
            notas_to_create.append(nota_examen)

            if len(notas_to_create) >= batch_size:
                created_count += bulk_create_safe(NotaExamen, notas_to_create)
                notas_to_create = []

    if notas_to_create:
        created_count += bulk_create_safe(NotaExamen, notas_to_create)

    return created_count


def create_notas_tarea_batch_2024(tarea, matriculaciones, batch_size):
    """Crea notas de tarea en lotes para 2024"""
    notas_to_create = []
    created_count = 0

    for matriculacion in matriculaciones:
        if not NotaTarea.objects.filter(matriculacion=matriculacion, tarea=tarea).exists():
            nota = generate_realistic_grade_2024(is_homework=True)

            nota_tarea = NotaTarea(
                matriculacion=matriculacion,
                tarea=tarea,
                nota=nota,
                observaciones=get_grade_comment_2024(nota)
            )
            notas_to_create.append(nota_tarea)

            if len(notas_to_create) >= batch_size:
                created_count += bulk_create_safe(NotaTarea, notas_to_create)
                notas_to_create = []

    if notas_to_create:
        created_count += bulk_create_safe(NotaTarea, notas_to_create)

    return created_count


def bulk_create_safe(model_class, objects_list, max_retries=3):
    """Inserción masiva segura con reintentos"""
    if not objects_list:
        return 0

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                model_class.objects.bulk_create(objects_list, ignore_conflicts=True)
                return len(objects_list)
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"      ❌ Error en inserción masiva: {str(e)[:80]}")
                return 0
            time.sleep(2 ** attempt)
    return 0


def generate_realistic_grade_2024(is_homework=False):
    """Genera una nota realista para 2024"""
    if is_homework:
        # Las tareas tienden a tener mejores notas
        base_grade = random.normalvariate(78, 12)  # Promedio ligeramente mejor en 2024
    else:
        # Los exámenes con distribución normal
        base_grade = random.normalvariate(72, 18)

    grade = max(0, min(100, base_grade))
    return round(grade, 1)


def get_grade_comment_2024(nota):
    """Retorna un comentario apropiado según la nota"""
    if nota >= 90:
        return "Excelente rendimiento"
    elif nota >= 80:
        return "Muy buen trabajo"
    elif nota >= 70:
        return "Buen desempeño"
    elif nota >= 60:
        return "Satisfactorio"
    elif nota >= 51:
        return "Debe mejorar"
    else:
        return "Requiere apoyo adicional"


if __name__ == '__main__':
    random.seed(2024)
    create_evaluations_2024()