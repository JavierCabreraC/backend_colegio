#!/usr/bin/env python3
"""
Script complementario OPTIMIZADO para generar datos faltantes del año 2022
Versión mejorada con procesamiento por lotes y control de memoria
"""

import os
import django
import random
import sys
import time
from datetime import date, timedelta, datetime
from faker import Faker

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from django.db import transaction
from authentication.models import Alumno
from academic.models import (
    ProfesorMateria, Gestion, Trimestre, Horario, Matriculacion
)
from evaluations.models import (
    Examen, NotaExamen, Tarea, NotaTarea,
    Asistencia, Participacion, EstadoAsistencia
)

fake = Faker('es_ES')
random.seed(2022)

YEAR = 2022
BATCH_SIZE = 100  # Procesar en lotes de 100 registros

STUDENT_PROFILES = {
    'excelente': {
        'nota_base': (85, 98),
        'asistencia_rate': 0.96,
        'participacion_freq': 0.85,
        'tarea_bonus': 10
    },
    'bueno': {
        'nota_base': (70, 84),
        'asistencia_rate': 0.90,
        'participacion_freq': 0.65,
        'tarea_bonus': 5
    },
    'regular': {
        'nota_base': (55, 69),
        'asistencia_rate': 0.78,
        'participacion_freq': 0.45,
        'tarea_bonus': 0
    },
    'bajo': {
        'nota_base': (25, 54),
        'asistencia_rate': 0.65,
        'participacion_freq': 0.25,
        'tarea_bonus': -5
    }
}


def main():
    """Función principal optimizada"""
    print("🚀 COMPLEMENTANDO DATOS ACADÉMICOS 2022 - VERSIÓN OPTIMIZADA")
    print("📝 Procesamiento por lotes para evitar timeouts")
    print("=" * 70)

    try:
        verify_base_data()

        print("\n📋 PASO 1: Creando tareas y calificaciones (OPTIMIZADO)...")
        create_tasks_and_grades_optimized()

        print("\n📅 PASO 2: Generando asistencias (MUESTRA)...")
        create_attendance_sample()

        print("\n🙋‍♂️ PASO 3: Registrando participaciones (MUESTRA)...")
        create_participation_sample()

        print("\n" + "=" * 70)
        print("🎉 DATOS COMPLEMENTARIOS CREADOS EXITOSAMENTE")
        print_completion_summary()

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def verify_base_data():
    """Verificar datos existentes"""
    print("🔍 Verificando datos existentes...")

    gestion = Gestion.objects.filter(anio=YEAR).first()
    if not gestion:
        raise Exception(f"No se encontró la gestión {YEAR}")

    trimestres = Trimestre.objects.filter(gestion=gestion).count()
    matriculaciones = Matriculacion.objects.filter(gestion=gestion).count()
    profesor_materias = ProfesorMateria.objects.count()
    horarios = Horario.objects.filter(trimestre__gestion=gestion).count()

    print(f"  ✅ Gestión {YEAR}: {gestion.nombre}")
    print(f"  ✅ Trimestres: {trimestres}")
    print(f"  ✅ Matriculaciones: {matriculaciones}")
    print(f"  ✅ Profesor-Materias: {profesor_materias}")
    print(f"  ✅ Horarios: {horarios}")


def get_student_profile(matriculacion):
    """Obtener perfil del estudiante"""
    obs = matriculacion.observaciones or ''
    if 'excelente' in obs.lower():
        return 'excelente'
    elif 'bueno' in obs.lower():
        return 'bueno'
    elif 'regular' in obs.lower():
        return 'regular'
    elif 'bajo' in obs.lower():
        return 'bajo'
    else:
        return 'regular'


def create_tasks_and_grades_optimized():
    """Crear tareas y notas - VERSIÓN OPTIMIZADA"""

    gestion = Gestion.objects.get(anio=YEAR)
    trimestres = Trimestre.objects.filter(gestion=gestion)
    profesor_materias = list(ProfesorMateria.objects.all())
    matriculaciones = list(Matriculacion.objects.filter(gestion=gestion))

    print(f"  📊 Procesando {len(profesor_materias)} materias × {len(trimestres)} trimestres")
    print(f"  📊 {len(matriculaciones)} alumnos matriculados")

    tareas_creadas = 0
    notas_creadas = 0

    for i, trimestre in enumerate(trimestres, 1):
        print(f"    📅 {trimestre.nombre} ({i}/{len(trimestres)})...")

        for j, pm in enumerate(profesor_materias, 1):
            print(f"      📚 {pm.materia.nombre} ({j}/{len(profesor_materias)})...")

            # Crear solo 2 tareas por materia por trimestre (menos carga)
            num_tareas = 2

            for k in range(num_tareas):
                # Crear tarea
                dias_trimestre = (trimestre.fecha_fin - trimestre.fecha_inicio).days
                dia_asignacion = random.randint(1, max(1, dias_trimestre - 10))
                fecha_asignacion = trimestre.fecha_inicio + timedelta(days=dia_asignacion)
                fecha_entrega = fecha_asignacion + timedelta(days=random.randint(7, 14))

                if fecha_entrega > trimestre.fecha_fin:
                    fecha_entrega = trimestre.fecha_fin

                tarea = Tarea.objects.create(
                    profesor_materia=pm,
                    trimestre=trimestre,
                    titulo=f"Tarea {k + 1} - {pm.materia.codigo} T{trimestre.numero}"[:50],
                    descripcion=f"Actividad {k + 1}"[:50],
                    fecha_asignacion=fecha_asignacion,
                    fecha_entrega=fecha_entrega,
                    ponderacion=random.choice([15.0, 20.0, 25.0])
                )
                tareas_creadas += 1

                # Crear notas EN LOTES para evitar timeout
                print(f"        📝 Creando {len(matriculaciones)} notas para Tarea {k + 1}...")

                notas_batch = []
                for matriculacion in matriculaciones:
                    perfil_nombre = get_student_profile(matriculacion)
                    perfil = STUDENT_PROFILES.get(perfil_nombre, STUDENT_PROFILES['regular'])

                    # Generar nota
                    nota_min, nota_max = perfil['nota_base']
                    bonus = perfil['tarea_bonus']
                    nota_base = random.uniform(nota_min + 5, min(100, nota_max + 10))
                    nota_final = max(0, min(100, nota_base + bonus + random.uniform(-3, 3)))

                    # 90% entregan, 10% no entregan
                    probabilidad_entrega = 0.90 if perfil_nombre != 'bajo' else 0.75

                    if random.random() < probabilidad_entrega:
                        nota_obj = NotaTarea(
                            matriculacion=matriculacion,
                            tarea=tarea,
                            nota=round(nota_final, 1),
                            observaciones="Entregada"[:50]
                        )
                    else:
                        nota_obj = NotaTarea(
                            matriculacion=matriculacion,
                            tarea=tarea,
                            nota=0.0,
                            observaciones="No entregada"[:50]
                        )

                    notas_batch.append(nota_obj)

                    # Insertar en lotes de 100
                    if len(notas_batch) >= BATCH_SIZE:
                        with transaction.atomic():
                            NotaTarea.objects.bulk_create(notas_batch)
                        notas_creadas += len(notas_batch)
                        notas_batch = []
                        print(f"          ✅ {notas_creadas} notas creadas...")

                # Insertar lote final
                if notas_batch:
                    with transaction.atomic():
                        NotaTarea.objects.bulk_create(notas_batch)
                    notas_creadas += len(notas_batch)

                # Pausa breve para evitar sobrecargar la BD
                time.sleep(0.1)

    print(f"    ✅ COMPLETADO: {tareas_creadas} tareas, {notas_creadas} calificaciones")


def create_attendance_sample():
    """Crear MUESTRA de asistencias (no todas)"""

    gestion = Gestion.objects.get(anio=YEAR)

    # Solo tomar una muestra de horarios para evitar timeout
    horarios = list(Horario.objects.filter(trimestre__gestion=gestion)[:20])  # Solo 20 horarios
    matriculaciones = Matriculacion.objects.filter(gestion=gestion)

    print(f"  📊 Generando asistencias para MUESTRA de {len(horarios)} horarios...")

    asistencias_creadas = 0

    for i, horario in enumerate(horarios, 1):
        print(f"    📚 Horario {i}/{len(horarios)}: {horario.profesor_materia.materia.nombre}")

        # Solo alumnos del grupo específico
        alumnos_grupo = matriculaciones.filter(alumno__grupo=horario.grupo)

        # Solo 5 fechas de clase por horario (muestra)
        inicio = horario.trimestre.fecha_inicio

        fechas_clase = []
        fecha_actual = inicio
        while len(fechas_clase) < 5 and fecha_actual <= horario.trimestre.fecha_fin:
            if fecha_actual.weekday() + 1 == horario.dia_semana:
                fechas_clase.append(fecha_actual)
            fecha_actual += timedelta(days=7)

        # Crear asistencias en lotes
        asistencias_batch = []

        for fecha_clase in fechas_clase:
            for matriculacion in alumnos_grupo:
                perfil_nombre = get_student_profile(matriculacion)
                perfil = STUDENT_PROFILES.get(perfil_nombre, STUDENT_PROFILES['regular'])

                # Determinar estado
                rand = random.random()
                if rand < perfil['asistencia_rate']:
                    estado = EstadoAsistencia.PRESENTE
                elif rand < perfil['asistencia_rate'] + 0.05:
                    estado = EstadoAsistencia.TARDANZA
                elif rand < perfil['asistencia_rate'] + 0.08:
                    estado = EstadoAsistencia.JUSTIFICADA
                else:
                    estado = EstadoAsistencia.FALTA

                asistencia_obj = Asistencia(
                    matriculacion=matriculacion,
                    horario=horario,
                    fecha=fecha_clase,
                    estado=estado
                )
                asistencias_batch.append(asistencia_obj)

                # Insertar en lotes
                if len(asistencias_batch) >= BATCH_SIZE:
                    with transaction.atomic():
                        Asistencia.objects.bulk_create(asistencias_batch)
                    asistencias_creadas += len(asistencias_batch)
                    asistencias_batch = []

        # Lote final
        if asistencias_batch:
            with transaction.atomic():
                Asistencia.objects.bulk_create(asistencias_batch)
            asistencias_creadas += len(asistencias_batch)

        print(f"      ✅ {asistencias_creadas} asistencias hasta ahora...")

    print(f"    ✅ MUESTRA COMPLETADA: {asistencias_creadas} registros de asistencia")


def create_participation_sample():
    """Crear MUESTRA de participaciones"""

    gestion = Gestion.objects.get(anio=YEAR)
    horarios = list(Horario.objects.filter(trimestre__gestion=gestion)[:15])  # Solo 15 horarios
    matriculaciones = Matriculacion.objects.filter(gestion=gestion)

    print(f"  📊 Generando participaciones para MUESTRA de {len(horarios)} horarios...")

    participaciones_creadas = 0

    for i, horario in enumerate(horarios, 1):
        print(f"    📚 Horario {i}/{len(horarios)}: {horario.profesor_materia.materia.nombre}")

        alumnos_grupo = list(matriculaciones.filter(alumno__grupo=horario.grupo))

        # 3 fechas con participaciones por horario
        inicio = horario.trimestre.fecha_inicio
        fechas_participacion = []
        fecha_actual = inicio

        while len(fechas_participacion) < 3 and fecha_actual <= horario.trimestre.fecha_fin:
            if fecha_actual.weekday() + 1 == horario.dia_semana:
                fechas_participacion.append(fecha_actual)
            fecha_actual += timedelta(days=14)  # Cada 2 semanas

        participaciones_batch = []

        for fecha_clase in fechas_participacion:
            # Solo algunos alumnos participan por clase
            num_participantes = random.randint(3, min(8, len(alumnos_grupo)))
            participantes = random.sample(alumnos_grupo, num_participantes)

            for matriculacion in participantes:
                perfil_nombre = get_student_profile(matriculacion)
                perfil = STUDENT_PROFILES.get(perfil_nombre, STUDENT_PROFILES['regular'])

                if random.random() < perfil['participacion_freq']:
                    if perfil_nombre == 'excelente':
                        valor = random.randint(4, 5)
                        desc = "Excelente"
                    elif perfil_nombre == 'bueno':
                        valor = random.randint(3, 4)
                        desc = "Buena"
                    elif perfil_nombre == 'regular':
                        valor = random.randint(2, 3)
                        desc = "Regular"
                    else:
                        valor = random.randint(1, 2)
                        desc = "Básica"

                    participacion_obj = Participacion(
                        matriculacion=matriculacion,
                        horario=horario,
                        fecha=fecha_clase,
                        descripcion=desc[:50],
                        valor=valor
                    )
                    participaciones_batch.append(participacion_obj)

                    if len(participaciones_batch) >= BATCH_SIZE:
                        with transaction.atomic():
                            Participacion.objects.bulk_create(participaciones_batch)
                        participaciones_creadas += len(participaciones_batch)
                        participaciones_batch = []

        if participaciones_batch:
            with transaction.atomic():
                Participacion.objects.bulk_create(participaciones_batch)
            participaciones_creadas += len(participaciones_batch)

        print(f"      ✅ {participaciones_creadas} participaciones hasta ahora...")

    print(f"    ✅ MUESTRA COMPLETADA: {participaciones_creadas} participaciones")


def print_completion_summary():
    """Resumen final"""
    print("\n📊 RESUMEN DE DATOS CREADOS:")
    print("-" * 40)

    print(f"📋 Tareas: {Tarea.objects.count()}")
    print(f"📝 Notas de Tareas: {NotaTarea.objects.count()}")
    print(f"📅 Asistencias: {Asistencia.objects.count()}")
    print(f"🙋‍♂️ Participaciones: {Participacion.objects.count()}")

    if Asistencia.objects.exists():
        print(f"\n📊 Distribución de Asistencias:")
        for estado, nombre in EstadoAsistencia.choices:
            count = Asistencia.objects.filter(estado=estado).count()
            print(f"   • {nombre}: {count}")

    print(f"\n💾 Datos listos para Machine Learning!")
    print(f"   🎯 Dataset académico completo del año {YEAR}")


if __name__ == '__main__':
    main()
