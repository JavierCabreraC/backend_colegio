#!/usr/bin/env python3
"""
Script para generar datos académicos completos del año 2022
"""

import os
import django
import random
import sys
from datetime import date, timedelta, datetime, time
from faker import Faker

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

# Importar modelos
from authentication.models import Usuario, Profesor, Alumno
from academic.models import (
    Nivel, Grupo, Materia, Aula, ProfesorMateria,
    Gestion, Trimestre, Horario, Matriculacion
)
from evaluations.models import (
    Examen, NotaExamen, Tarea, NotaTarea,
    Asistencia, Participacion, EstadoAsistencia
)

fake = Faker('es_ES')
random.seed(2022)

# Configuración
YEAR = 2022
STUDENTS_PER_GROUP = 20
TOTAL_STUDENTS = 240

# Materias adicionales (CÓDIGOS MÁS CORTOS)
NUEVAS_MATERIAS = [
    ('BIO', 'Biología', 'Ciencias Naturales', 4),
    ('GEO', 'Geografía', 'Geografía Bolivia', 3),  # ✅ Reducido
    ('HIS', 'Historia', 'Historia Universal', 3),
    ('EDF', 'Ed. Física', 'Deportes', 2),  # ✅ Reducido
    ('ING', 'Inglés', 'Idioma Extranjero', 3),
    ('ART', 'Artes', 'Expresión Artística', 2),  # ✅ Reducido
    ('MUS', 'Música', 'Educación Musical', 2)
]

# Perfiles de estudiantes para ML
STUDENT_PROFILES = {
    'excelente': {
        'peso': 15,
        'nota_base': (85, 98),
        'asistencia_rate': 0.96,
        'participacion_freq': 0.85,
        'tendencia': 'estable'
    },
    'bueno': {
        'peso': 35,
        'nota_base': (70, 84),
        'asistencia_rate': 0.90,
        'participacion_freq': 0.65,
        'tendencia': 'mejora'
    },
    'regular': {
        'peso': 35,
        'nota_base': (55, 69),
        'asistencia_rate': 0.78,
        'participacion_freq': 0.45,
        'tendencia': 'irregular'
    },
    'bajo': {
        'peso': 15,
        'nota_base': (25, 54),
        'asistencia_rate': 0.65,
        'participacion_freq': 0.25,
        'tendencia': 'declive'
    }
}

def main():
    """Función principal"""
    print("🚀 INICIANDO CREACIÓN DEL AÑO ACADÉMICO 2022 - VERSIÓN CORREGIDA")
    print("=" * 70)

    try:
        # 1. Completar estructura básica
        print("\n🏫 PASO 1: Completando estructura básica...")
        create_basic_structure()

        # 2. Completar profesores
        print("\n👨‍🏫 PASO 2: Completando profesores...")
        create_additional_professors()

        # 3. Crear año académico 2022
        print("\n📅 PASO 3: Creando año académico 2022...")
        create_academic_year_2022()

        # 4. Crear alumnos
        print("\n🎓 PASO 4: Creando alumnos...")
        create_students()

        # 5. Asignar profesores a materias
        print("\n📋 PASO 5: Asignando profesores a materias...")
        create_assignments()

        # 6. Crear horarios
        print("\n🗓️ PASO 6: Creando horarios...")
        create_schedules()

        # 7. Generar datos académicos
        print("\n📊 PASO 7: Generando datos académicos...")
        create_academic_data()

        print("\n" + "=" * 70)
        print("🎉 CREACIÓN COMPLETADA EXITOSAMENTE")
        print_final_summary()

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def create_basic_structure():
    """Crear niveles, grupos, materias adicionales, aulas"""

    # 1. Niveles (1° a 6° secundaria) - TEXTOS CORTOS
    for i in range(1, 7):
        nivel, created = Nivel.objects.get_or_create(
            numero=i,
            defaults={
                'nombre': f'{i}° Secundaria',  # ✅ 13 caracteres máximo
                'descripcion': f'Nivel {i}'     # ✅ 7 caracteres máximo
            }
        )
        if created:
            print(f"  ✅ Nivel {i}° creado")

    # 2. Grupos (A y B por cada nivel)
    grupos_creados = 0
    for nivel in Nivel.objects.all():
        for letra in ['A', 'B']:
            grupo, created = Grupo.objects.get_or_create(
                nivel=nivel,
                letra=letra,
                defaults={'capacidad_maxima': 25}
            )
            if created:
                grupos_creados += 1
                print(f"  ✅ Grupo {nivel.numero}°{letra} creado")

    # 3. Materias adicionales - DESCRIPCIONES CORTAS
    materias_creadas = 0
    for codigo, nombre, desc, horas in NUEVAS_MATERIAS:
        materia, created = Materia.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'descripcion': desc[:40],  # ✅ Truncar a 40 caracteres
                'horas_semanales': horas
            }
        )
        if created:
            materias_creadas += 1
            print(f"  ✅ Materia {codigo} - {nombre} creada")

    # 4. Aulas (15 aulas) - DESCRIPCIONES CORTAS
    aulas_creadas = 0
    for i in range(1, 16):
        aula, created = Aula.objects.get_or_create(
            nombre=f'Aula {i:02d}',
            defaults={
                'capacidad': random.randint(30, 40),
                'descripcion': f'Sala {i}'  # ✅ Descripción corta
            }
        )
        if created:
            aulas_creadas += 1

    print(f"  📊 Resumen: {grupos_creados} grupos, {materias_creadas} materias, {aulas_creadas} aulas creadas")

def create_additional_professors():
    """Crear profesores adicionales - DIRECCIONES CORTAS"""

    profesores_data = [
        {
            'email': 'profesor6@sistema.com',
            'password': 'prof303',
            'nombres': 'Ana Lucía',
            'apellidos': 'Morales Vera',
            'cedula_identidad': '66666666',
            'fecha_nacimiento': date(1986, 4, 12),
            'genero': 'F',
            'telefono': '77890123',
            'direccion': 'Barrio Equipetrol Norte'[:60],  # ✅ Truncar
            'especialidad': 'Biología',
            'fecha_contratacion': date(2019, 3, 1)
        },
        {
            'email': 'profesor7@sistema.com',
            'password': 'prof404',
            'nombres': 'Diego Alejandro',
            'apellidos': 'Sánchez Rojas',
            'cedula_identidad': '77777777',
            'fecha_nacimiento': date(1983, 9, 28),
            'genero': 'M',
            'telefono': '78901234',
            'direccion': 'Radial 10 y 4to Anillo'[:60],  # ✅ Truncar
            'especialidad': 'Geografía',
            'fecha_contratacion': date(2017, 8, 15)
        },
        {
            'email': 'profesor8@sistema.com',
            'password': 'prof505',
            'nombres': 'Patricia Isabel',
            'apellidos': 'Flores Gutierrez',
            'cedula_identidad': '88888888',
            'fecha_nacimiento': date(1988, 1, 17),
            'genero': 'F',
            'telefono': '79012345',
            'direccion': 'Villa Primero de Mayo'[:60],  # ✅ Truncar
            'especialidad': 'Educación Física',
            'fecha_contratacion': date(2020, 2, 10)
        },
        {
            'email': 'profesor9@sistema.com',
            'password': 'prof606',
            'nombres': 'Michael James',
            'apellidos': 'Thompson Wilson',
            'cedula_identidad': '99999999',
            'fecha_nacimiento': date(1985, 6, 5),
            'genero': 'M',
            'telefono': '70123890',
            'direccion': 'Av. San Martín 567'[:60],  # ✅ Truncar
            'especialidad': 'Inglés',
            'fecha_contratacion': date(2018, 9, 1)
        },
        {
            'email': 'profesor10@sistema.com',
            'password': 'prof707',
            'nombres': 'Carla Beatriz',
            'apellidos': 'Medina Castro',
            'cedula_identidad': '10101010',
            'fecha_nacimiento': date(1984, 11, 22),
            'genero': 'F',
            'telefono': '71234890',
            'direccion': 'Zona Norte, Calle 21'[:60],  # ✅ Truncar
            'especialidad': 'Artes',
            'fecha_contratacion': date(2019, 6, 1)
        },
        {
            'email': 'profesor11@sistema.com',
            'password': 'prof808',
            'nombres': 'Rodrigo Sebastián',
            'apellidos': 'Vargas Peña',
            'cedula_identidad': '11111100',
            'fecha_nacimiento': date(1981, 8, 14),
            'genero': 'M',
            'telefono': '72345890',
            'direccion': 'Barrio Las Palmas'[:60],  # ✅ Truncar
            'especialidad': 'Música',
            'fecha_contratacion': date(2016, 4, 15)
        }
    ]

    profesores_creados = 0
    for profesor_data in profesores_data:
        email = profesor_data['email']

        if not Usuario.objects.filter(email=email).exists():
            # Crear usuario
            usuario = Usuario.objects.create_user(
                email=profesor_data['email'],
                password=profesor_data['password'],
                tipo_usuario='profesor'
            )

            # Crear perfil de profesor
            profesor = Profesor.objects.create(
                usuario=usuario,
                nombres=profesor_data['nombres'],
                apellidos=profesor_data['apellidos'],
                cedula_identidad=profesor_data['cedula_identidad'],
                fecha_nacimiento=profesor_data['fecha_nacimiento'],
                genero=profesor_data['genero'],
                telefono=profesor_data['telefono'],
                direccion=profesor_data['direccion'],
                especialidad=profesor_data['especialidad'][:20],  # ✅ Truncar especialidad
                fecha_contratacion=profesor_data['fecha_contratacion']
            )

            profesores_creados += 1
            print(f"  ✅ Profesor creado: {profesor_data['nombres']} {profesor_data['apellidos']} - {profesor_data['especialidad']}")

    print(f"  📊 Total profesores ahora: {Profesor.objects.count()}")

def create_academic_year_2022():
    """Crear gestión 2022 con sus trimestres"""

    # Crear gestión 2022
    gestion, created = Gestion.objects.get_or_create(
        anio=YEAR,
        defaults={
            'nombre': f'Gestión Académica {YEAR}',
            'fecha_inicio': date(YEAR, 2, 1),
            'fecha_fin': date(YEAR, 11, 30),
            'activa': False
        }
    )

    if created:
        print(f"  ✅ Gestión {YEAR} creada")

        # Crear trimestres
        trimestres_data = [
            (1, 'Primer Trimestre 2022', date(YEAR, 2, 1), date(YEAR, 5, 15)),
            (2, 'Segundo Trimestre 2022', date(YEAR, 5, 16), date(YEAR, 8, 31)),
            (3, 'Tercer Trimestre 2022', date(YEAR, 9, 1), date(YEAR, 11, 30))
        ]

        for num, nombre, inicio, fin in trimestres_data:
            trimestre = Trimestre.objects.create(
                gestion=gestion,
                numero=num,
                nombre=nombre,
                fecha_inicio=inicio,
                fecha_fin=fin
            )
            print(f"  ✅ {nombre} creado ({inicio} - {fin})")
    else:
        print(f"  ⚠️ Gestión {YEAR} ya existía")

def create_students():
    """Crear 240 alumnos (20 por grupo) y matricularlos"""

    gestion = Gestion.objects.get(anio=YEAR)
    grupos = list(Grupo.objects.all().order_by('nivel__numero', 'letra'))

    alumno_counter = 1
    total_created = 0

    for grupo in grupos:
        print(f"  📚 Grupo {grupo.nivel.numero}°{grupo.letra}...")

        for i in range(STUDENTS_PER_GROUP):
            # Generar datos realistas
            genero = random.choice(['M', 'F'])
            nombres = fake.first_name_male() if genero == 'M' else fake.first_name_female()
            apellidos = f"{fake.last_name()} {fake.last_name()}"

            # Email único
            email = f"alumno{YEAR}{alumno_counter:03d}@sistema.com"

            if not Usuario.objects.filter(email=email).exists():
                # Crear usuario
                usuario = Usuario.objects.create_user(
                    email=email,
                    password='alumno123',
                    tipo_usuario='alumno'
                )

                # Edad apropiada para el nivel
                edad_base = 12 + grupo.nivel.numero
                fecha_nac = date(YEAR - edad_base, random.randint(1, 12), random.randint(1, 28))

                # Crear alumno - CAMPOS TRUNCADOS
                alumno = Alumno.objects.create(
                    usuario=usuario,
                    grupo=grupo,
                    matricula=f"{YEAR}{alumno_counter:03d}",
                    nombres=nombres[:100],  # Max 100
                    apellidos=apellidos[:100],  # Max 100
                    fecha_nacimiento=fecha_nac,
                    genero=genero,
                    telefono=f"6{random.randint(1000000, 9999999)}"[:10],  # Max 10
                    direccion=fake.address()[:60],  # Max 60
                    nombre_tutor=fake.name()[:50],  # Max 50
                    telefono_tutor=f"7{random.randint(1000000, 9999999)}"[:10]  # Max 10
                )

                # Asignar perfil de rendimiento
                profile_name = random.choices(
                    list(STUDENT_PROFILES.keys()),
                    weights=[p['peso'] for p in STUDENT_PROFILES.values()]
                )[0]

                # Matricular en gestión 2022
                Matriculacion.objects.create(
                    alumno=alumno,
                    gestion=gestion,
                    fecha_matriculacion=date(YEAR, 1, 15),
                    activa=True,
                    observaciones=f'Perfil: {profile_name}'[:50]  # ✅ Max 50
                )

                total_created += 1

            alumno_counter += 1

    print(f"  ✅ {total_created} alumnos creados y matriculados en {YEAR}")

def create_assignments():
    """Asignar profesores a materias"""

    # Mapeo corregido
    especialidad_materia = {
        'Matemáticas': ['MAT'],
        'Física': ['FIS'],
        'Química': ['QUI'],
        'Lenguaje': ['LIT'],  # Asumiendo que LIT existe
        'Historia': ['HIS'],
        'Biología': ['BIO'],
        'Geografía': ['GEO'],
        'Educación Física': ['EDF'],
        'Inglés': ['ING'],
        'Artes': ['ART'],
        'Música': ['MUS']
    }

    asignaciones_creadas = 0

    for profesor in Profesor.objects.all():
        especialidad = profesor.especialidad

        # Materia principal
        if especialidad in especialidad_materia:
            for codigo_materia in especialidad_materia[especialidad]:
                try:
                    materia = Materia.objects.get(codigo=codigo_materia)
                    pm, created = ProfesorMateria.objects.get_or_create(
                        profesor=profesor,
                        materia=materia
                    )
                    if created:
                        asignaciones_creadas += 1
                        print(f"  ✅ {profesor.nombres} {profesor.apellidos} → {materia.nombre}")
                except Materia.DoesNotExist:
                    print(f"  ⚠️ Materia {codigo_materia} no encontrada para {especialidad}")

        # Materia secundaria aleatoria
        if random.random() < 0.3:  # 30% enseñan segunda materia
            materias_disponibles = list(Materia.objects.exclude(
                profesormateria__profesor=profesor
            ))
            if materias_disponibles:
                materia_extra = random.choice(materias_disponibles)
                pm, created = ProfesorMateria.objects.get_or_create(
                    profesor=profesor,
                    materia=materia_extra
                )
                if created:
                    asignaciones_creadas += 1
                    print(f"  ✅ {profesor.nombres} {profesor.apellidos} → {materia_extra.nombre} (extra)")

    print(f"  📊 Total asignaciones: {asignaciones_creadas}")

def create_schedules():
    """Crear horarios básicos"""

    trimestres = Trimestre.objects.filter(gestion__anio=YEAR)
    grupos = Grupo.objects.all()
    aulas = list(Aula.objects.all())
    profesor_materias = list(ProfesorMateria.objects.all())

    if not profesor_materias:
        print("  ⚠️ No hay asignaciones profesor-materia. Saltando horarios.")
        return

    horarios_creados = 0

    for trimestre in trimestres:
        print(f"  📅 {trimestre.nombre}...")

        for grupo in grupos:
            # Máximo 6 materias por grupo para evitar conflictos
            materias_grupo = random.sample(
                profesor_materias,
                min(6, len(profesor_materias))
            )

            horario_idx = 0
            for dia in range(1, 6):  # Lunes a Viernes
                hora_inicio = time(8, 0)  # 8:00 AM

                # Máximo 2 períodos por día
                for periodo in range(2):
                    if horario_idx < len(materias_grupo):
                        pm = materias_grupo[horario_idx]
                        aula = random.choice(aulas)

                        # Hora fin
                        inicio_dt = datetime.combine(date.today(), hora_inicio)
                        fin_dt = inicio_dt + timedelta(minutes=50)
                        hora_fin = fin_dt.time()

                        # Crear horario sin validación compleja por ahora
                        try:
                            Horario.objects.create(
                                profesor_materia=pm,
                                grupo=grupo,
                                aula=aula,
                                trimestre=trimestre,
                                dia_semana=dia,
                                hora_inicio=hora_inicio,
                                hora_fin=hora_fin
                            )
                            horarios_creados += 1
                        except Exception as e:
                            print(f"    ⚠️ Error creando horario: {str(e)[:50]}...")

                        horario_idx += 1
                        hora_inicio = (fin_dt + timedelta(minutes=10)).time()

    print(f"  ✅ {horarios_creados} horarios creados")

def create_academic_data():
    """Generar datos académicos básicos"""
    print("  🔄 Generando muestra de datos académicos...")

    gestion = Gestion.objects.get(anio=YEAR)
    trimestres = Trimestre.objects.filter(gestion=gestion)
    matriculaciones = list(Matriculacion.objects.filter(gestion=gestion))
    profesor_materias = list(ProfesorMateria.objects.all())

    if not profesor_materias:
        print("  ⚠️ No hay asignaciones. Saltando datos académicos.")
        return

    # Contadores
    examenes_creados = 0
    notas_creadas = 0

    print("    📝 Creando muestra de exámenes y notas...")

    # Solo crear una muestra para evitar timeouts
    for trimestre in trimestres[:2]:  # Solo 2 trimestres
        for pm in profesor_materias[:5]:  # Solo 5 profesor-materias
            # 1 examen por combinación
            examen = Examen.objects.create(
                profesor_materia=pm,
                trimestre=trimestre,
                numero_parcial=1,
                titulo=f"Examen {pm.materia.codigo} - T{trimestre.numero}"[:100],
                descripcion=f"Evaluación {trimestre.numero}"[:100],
                fecha_examen=fake.date_between(
                    start_date=trimestre.fecha_inicio,
                    end_date=trimestre.fecha_fin
                ),
                ponderacion=25.0
            )
            examenes_creados += 1

            # Crear notas para una muestra de alumnos
            muestra_alumnos = random.sample(matriculaciones, min(10, len(matriculaciones)))

            for matriculacion in muestra_alumnos:
                # Obtener perfil del alumno de las observaciones
                obs = matriculacion.observaciones or ''
                if 'excelente' in obs:
                    nota = random.uniform(85, 98)
                elif 'bueno' in obs:
                    nota = random.uniform(70, 84)
                elif 'regular' in obs:
                    nota = random.uniform(55, 69)
                else:
                    nota = random.uniform(25, 54)

                NotaExamen.objects.create(
                    matriculacion=matriculacion,
                    examen=examen,
                    nota=round(nota, 1),
                    observaciones=f"Nota T{trimestre.numero}"[:100]
                )
                notas_creadas += 1

    print(f"    ✅ Muestra creada: {examenes_creados} exámenes, {notas_creadas} notas")

def print_final_summary():
    """Mostrar resumen final"""
    print("\n📊 RESUMEN FINAL DEL AÑO ACADÉMICO 2022:")
    print("-" * 50)

    print(f"🏫 Estructura:")
    print(f"   • Niveles: {Nivel.objects.count()}")
    print(f"   • Grupos: {Grupo.objects.count()}")
    print(f"   • Materias: {Materia.objects.count()}")
    print(f"   • Aulas: {Aula.objects.count()}")

    print(f"\n👥 Personal:")
    print(f"   • Profesores: {Profesor.objects.count()}")
    print(f"   • Alumnos: {Alumno.objects.count()}")

    gestion_2022 = Gestion.objects.filter(anio=2022).first()
    if gestion_2022:
        print(f"\n📅 Gestión 2022:")
        print(f"   • Trimestres: {Trimestre.objects.filter(gestion=gestion_2022).count()}")
        print(f"   • Matriculaciones: {Matriculacion.objects.filter(gestion=gestion_2022).count()}")
        print(f"   • Horarios: {Horario.objects.filter(trimestre__gestion=gestion_2022).count()}")

    print(f"\n📊 Datos Académicos:")
    print(f"   • Asignaciones: {ProfesorMateria.objects.count()}")
    print(f"   • Exámenes: {Examen.objects.count()}")
    print(f"   • Notas: {NotaExamen.objects.count()}")

    print(f"\n🔐 Credenciales de Prueba:")
    print(f"   • Director: director1@sistema.com / director123")
    print(f"   • Profesor: profesor1@sistema.com / prof123")
    print(f"   • Alumno: alumno2022001@sistema.com / alumno123")

if __name__ == '__main__':
    main()

