#!/usr/bin/env python3
"""
Script complementario para generar datos faltantes del año 2022:
- Tareas y NotasTareas
- Asistencias
- Participaciones
Utiliza los datos ya existentes creados por el script anterior
"""

import os
import django
import random
import sys
from datetime import date, timedelta, datetime
from faker import Faker

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

# Importar modelos
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

# Configuración
YEAR = 2022

# Perfiles de estudiantes (mismo que el script anterior)
STUDENT_PROFILES = {
    'excelente': {
        'nota_base': (85, 98),
        'asistencia_rate': 0.96,
        'participacion_freq': 0.85,
        'tarea_bonus': 10  # Bonus en tareas
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
        'tarea_bonus': -5  # Penalización en tareas
    }
}


def main():
    """Función principal"""
    print("🚀 COMPLEMENTANDO DATOS ACADÉMICOS 2022")
    print("📝 Creando: Tareas, Notas de Tareas, Asistencias y Participaciones")
    print("=" * 65)

    try:
        # Verificar que existen los datos base
        verify_base_data()

        # 1. Crear tareas y notas de tareas
        print("\n📋 PASO 1: Creando tareas y calificaciones...")
        create_tasks_and_grades()

        # 2. Crear asistencias
        print("\n📅 PASO 2: Generando asistencias...")
        create_attendance_records()

        # 3. Crear participaciones
        print("\n🙋‍♂️ PASO 3: Registrando participaciones...")
        create_participation_records()

        print("\n" + "=" * 65)
        print("🎉 DATOS COMPLEMENTARIOS CREADOS EXITOSAMENTE")
        print_completion_summary()

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def verify_base_data():
    """Verificar que existen los datos necesarios del script anterior"""
    print("🔍 Verificando datos existentes...")

    gestion = Gestion.objects.filter(anio=YEAR).first()
    if not gestion:
        raise Exception(f"No se encontró la gestión {YEAR}. Ejecuta primero el script principal.")

    trimestres = Trimestre.objects.filter(gestion=gestion).count()
    if trimestres == 0:
        raise Exception("No se encontraron trimestres. Ejecuta primero el script principal.")

    matriculaciones = Matriculacion.objects.filter(gestion=gestion).count()
    if matriculaciones == 0:
        raise Exception("No se encontraron matriculaciones. Ejecuta primero el script principal.")

    profesor_materias = ProfesorMateria.objects.count()
    if profesor_materias == 0:
        raise Exception("No se encontraron asignaciones profesor-materia. Ejecuta primero el script principal.")

    horarios = Horario.objects.filter(trimestre__gestion=gestion).count()

    print(f"  ✅ Gestión {YEAR}: {gestion.nombre}")
    print(f"  ✅ Trimestres: {trimestres}")
    print(f"  ✅ Matriculaciones: {matriculaciones}")
    print(f"  ✅ Asignaciones profesor-materia: {profesor_materias}")
    print(f"  ✅ Horarios: {horarios}")
    print("  📊 Datos base verificados correctamente")


def get_student_profile(matriculacion):
    """Obtener perfil del estudiante desde las observaciones"""
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
        return 'regular'  # Default


def create_tasks_and_grades():
    """Crear tareas y notas de tareas"""

    gestion = Gestion.objects.get(anio=YEAR)
    trimestres = Trimestre.objects.filter(gestion=gestion)
    profesor_materias = ProfesorMateria.objects.all()
    matriculaciones = list(Matriculacion.objects.filter(gestion=gestion))

    tareas_creadas = 0
    notas_tareas_creadas = 0

    print("  📝 Generando tareas por trimestre y materia...")

    for trimestre in trimestres:
        print(f"    📅 {trimestre.nombre}...")

        for pm in profesor_materias:
            # 3-5 tareas por profesor-materia por trimestre
            num_tareas = random.randint(3, 5)

            for i in range(num_tareas):
                # Fechas realistas dentro del trimestre
                dias_trimestre = (trimestre.fecha_fin - trimestre.fecha_inicio).days
                dia_asignacion = random.randint(1, max(1, dias_trimestre - 14))
                fecha_asignacion = trimestre.fecha_inicio + timedelta(days=dia_asignacion)
                fecha_entrega = fecha_asignacion + timedelta(days=random.randint(3, 14))

                # Asegurar que la fecha de entrega no exceda el trimestre
                if fecha_entrega > trimestre.fecha_fin:
                    fecha_entrega = trimestre.fecha_fin

                # Crear tarea
                tarea = Tarea.objects.create(
                    profesor_materia=pm,
                    trimestre=trimestre,
                    titulo=f"Tarea {i + 1} - {pm.materia.nombre} T{trimestre.numero}"[:50],
                    descripcion=f"Actividad práctica {i + 1} del {trimestre.nombre}"[:50],
                    fecha_asignacion=fecha_asignacion,
                    fecha_entrega=fecha_entrega,
                    ponderacion=random.choice([10.0, 15.0, 20.0])
                )
                tareas_creadas += 1

                # Crear notas para todos los alumnos matriculados
                for matriculacion in matriculaciones:
                    perfil_nombre = get_student_profile(matriculacion)
                    perfil = STUDENT_PROFILES.get(perfil_nombre, STUDENT_PROFILES['regular'])

                    # Generar nota de tarea (generalmente más altas que exámenes)
                    nota_min, nota_max = perfil['nota_base']
                    bonus = perfil['tarea_bonus']

                    # Las tareas suelen tener mejores notas
                    nota_base = random.uniform(nota_min + 5, min(100, nota_max + 10))
                    nota_final = max(0, min(100, nota_base + bonus + random.uniform(-3, 3)))

                    # Algunos alumnos no entregan tareas (especialmente perfil bajo)
                    probabilidad_entrega = 0.95 if perfil_nombre != 'bajo' else 0.80

                    if random.random() < probabilidad_entrega:
                        NotaTarea.objects.create(
                            matriculacion=matriculacion,
                            tarea=tarea,
                            nota=round(nota_final, 1),
                            observaciones=f"Entregada - Perfil: {perfil_nombre}"[:50]
                        )
                    else:
                        # No entregada
                        NotaTarea.objects.create(
                            matriculacion=matriculacion,
                            tarea=tarea,
                            nota=0.0,
                            observaciones="No entregada"[:50]
                        )

                    notas_tareas_creadas += 1

    print(f"    ✅ {tareas_creadas} tareas creadas")
    print(f"    ✅ {notas_tareas_creadas} calificaciones de tareas registradas")


def create_attendance_records():
    """Crear registros de asistencia"""

    gestion = Gestion.objects.get(anio=YEAR)
    horarios = Horario.objects.filter(trimestre__gestion=gestion)
    matriculaciones = Matriculacion.objects.filter(gestion=gestion)

    asistencias_creadas = 0

    print("  📅 Generando asistencias por horario...")

    # Para cada horario, generar asistencias de ~15 clases durante el trimestre
    for horario in horarios:
        print(
            f"    📚 {horario.profesor_materia.materia.nombre} - Grupo {horario.grupo.nivel.numero}°{horario.grupo.letra}")

        # Obtener alumnos del grupo que están matriculados
        alumnos_grupo = matriculaciones.filter(alumno__grupo=horario.grupo)

        # Generar 15 fechas de clases durante el trimestre
        inicio_trimestre = horario.trimestre.fecha_inicio
        fin_trimestre = horario.trimestre.fecha_fin

        fecha_actual = inicio_trimestre
        clases_generadas = 0

        while fecha_actual <= fin_trimestre and clases_generadas < 15:
            # Solo generar si coincide con el día de la semana del horario
            if fecha_actual.weekday() + 1 == horario.dia_semana:  # Django: 1=Lunes

                for matriculacion in alumnos_grupo:
                    perfil_nombre = get_student_profile(matriculacion)
                    perfil = STUDENT_PROFILES.get(perfil_nombre, STUDENT_PROFILES['regular'])

                    # Determinar estado de asistencia basado en el perfil
                    rand = random.random()
                    asistencia_rate = perfil['asistencia_rate']

                    # Factores que afectan la asistencia
                    factor_clima = 0.9 if fecha_actual.month in [12, 1, 2] else 1.0  # Época lluviosa
                    factor_viernes = 0.85 if fecha_actual.weekday() == 4 else 1.0  # Viernes

                    asistencia_ajustada = asistencia_rate * factor_clima * factor_viernes

                    if rand < asistencia_ajustada:
                        estado = EstadoAsistencia.PRESENTE
                    elif rand < asistencia_ajustada + 0.05:
                        estado = EstadoAsistencia.TARDANZA
                    elif rand < asistencia_ajustada + 0.08:
                        estado = EstadoAsistencia.JUSTIFICADA
                    else:
                        estado = EstadoAsistencia.FALTA

                    # Crear registro de asistencia
                    Asistencia.objects.create(
                        matriculacion=matriculacion,
                        horario=horario,
                        fecha=fecha_actual,
                        estado=estado
                    )
                    asistencias_creadas += 1

                clases_generadas += 1

            fecha_actual += timedelta(days=1)

    print(f"    ✅ {asistencias_creadas} registros de asistencia creados")


def create_participation_records():
    """Crear registros de participación"""

    gestion = Gestion.objects.get(anio=YEAR)
    horarios = Horario.objects.filter(trimestre__gestion=gestion)
    matriculaciones = Matriculacion.objects.filter(gestion=gestion)

    participaciones_creadas = 0

    print("  🙋‍♂️ Generando participaciones en clases...")

    # Para cada horario, generar participaciones en ~8 clases
    for horario in horarios:
        alumnos_grupo = list(matriculaciones.filter(alumno__grupo=horario.grupo))

        if not alumnos_grupo:
            continue

        # 8 fechas de clases con participaciones
        inicio_trimestre = horario.trimestre.fecha_inicio
        fin_trimestre = horario.trimestre.fecha_fin

        fechas_participacion = []
        fecha_actual = inicio_trimestre

        while len(fechas_participacion) < 8 and fecha_actual <= fin_trimestre:
            if fecha_actual.weekday() + 1 == horario.dia_semana:
                fechas_participacion.append(fecha_actual)
            fecha_actual += timedelta(days=7)  # Saltar una semana

        for fecha_clase in fechas_participacion:
            # En cada clase, algunos alumnos participan
            num_participantes = random.randint(2, min(8, len(alumnos_grupo)))
            alumnos_participantes = random.sample(alumnos_grupo, num_participantes)

            for matriculacion in alumnos_participantes:
                perfil_nombre = get_student_profile(matriculacion)
                perfil = STUDENT_PROFILES.get(perfil_nombre, STUDENT_PROFILES['regular'])

                # Probabilidad de participar basada en el perfil
                if random.random() < perfil['participacion_freq']:
                    # Valor de participación basado en perfil
                    if perfil_nombre == 'excelente':
                        valor = random.randint(4, 5)
                        desc = "Participación excelente"
                    elif perfil_nombre == 'bueno':
                        valor = random.randint(3, 4)
                        desc = "Buena participación"
                    elif perfil_nombre == 'regular':
                        valor = random.randint(2, 3)
                        desc = "Participación regular"
                    else:  # bajo
                        valor = random.randint(1, 2)
                        desc = "Participación básica"

                    Participacion.objects.create(
                        matriculacion=matriculacion,
                        horario=horario,
                        fecha=fecha_clase,
                        descripcion=desc[:50],
                        valor=valor
                    )
                    participaciones_creadas += 1

    print(f"    ✅ {participaciones_creadas} participaciones registradas")


def print_completion_summary():
    """Mostrar resumen de datos complementarios creados"""
    print("\n📊 RESUMEN DE DATOS COMPLEMENTARIOS CREADOS:")
    print("-" * 55)

    print(f"📋 Tareas: {Tarea.objects.count()}")
    print(f"📝 Notas de Tareas: {NotaTarea.objects.count()}")
    print(f"📅 Asistencias: {Asistencia.objects.count()}")
    print(f"🙋‍♂️ Participaciones: {Participacion.objects.count()}")

    # Estadísticas por estado de asistencia
    print(f"\n📊 Distribución de Asistencias:")
    for estado, nombre in EstadoAsistencia.choices:
        count = Asistencia.objects.filter(estado=estado).count()
        total_asistencias = Asistencia.objects.count()
        porcentaje = (count / total_asistencias * 100) if total_asistencias > 0 else 0
        print(f"   • {nombre}: {count} ({porcentaje:.1f}%)")

    # Promedio de participaciones por alumno
    total_participaciones = Participacion.objects.count()
    total_alumnos = Matriculacion.objects.filter(gestion__anio=YEAR).count()
    promedio_participaciones = total_participaciones / total_alumnos if total_alumnos > 0 else 0

    print(f"\n🎯 Estadísticas Adicionales:")
    print(f"   • Promedio de participaciones por alumno: {promedio_participaciones:.1f}")
    print(f"   • Total de evaluaciones (exámenes + tareas): {Examen.objects.count() + Tarea.objects.count()}")
    print(f"   • Total de calificaciones: {NotaExamen.objects.count() + NotaTarea.objects.count()}")

    print(f"\n💾 Base de datos ahora contiene datos completos para ML!")
    print(f"   🎯 Año académico {YEAR} listo para entrenar modelos predictivos")


if __name__ == '__main__':
    main()

