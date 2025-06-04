import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from academic.models import Gestion, Trimestre, Nivel, Grupo, Aula
from datetime import date

def setup_academic_year_2023():
    print("🗓️ Configurando año académico 2023...")
    
    # 1. CREAR GESTIÓN 2023
    gestion_2023, created = Gestion.objects.get_or_create(
        anio=2023,
        defaults={
            'nombre': 'Gestión Académica 2023',
            'fecha_inicio': date(2023, 2, 1),
            'fecha_fin': date(2023, 11, 30),
            'activa': True
        }
    )
    if created:
        print("✅ Gestión 2023 creada")
    else:
        print("⚠️ Gestión 2023 ya existía")
    
    # 2. CREAR TRIMESTRES
    trimestres_data = [
        {
            'numero': 1,
            'nombre': 'Primer Trimestre 2023',
            'fecha_inicio': date(2023, 2, 1),
            'fecha_fin': date(2023, 4, 30)
        },
        {
            'numero': 2,
            'nombre': 'Segundo Trimestre 2023',
            'fecha_inicio': date(2023, 5, 1),
            'fecha_fin': date(2023, 8, 31)
        },
        {
            'numero': 3,
            'nombre': 'Tercer Trimestre 2023',
            'fecha_inicio': date(2023, 9, 1),
            'fecha_fin': date(2023, 11, 30)
        }
    ]
    
    for trimestre_data in trimestres_data:
        trimestre, created = Trimestre.objects.get_or_create(
            gestion=gestion_2023,
            numero=trimestre_data['numero'],
            defaults=trimestre_data
        )
        if created:
            print(f"✅ {trimestre_data['nombre']} creado")
    
    # 3. CREAR NIVELES (1° a 6° secundaria)
    for i in range(1, 7):
        nivel, created = Nivel.objects.get_or_create(
            numero=i,
            defaults={
                'nombre': f'{i}° de Secundaria',
                'descripcion': f'Nivel {i}'
            }
        )
        if created:
            print(f"✅ Nivel {i}° creado")
    
    # 4. CREAR GRUPOS (A y B para cada nivel)
    niveles = Nivel.objects.all()
    for nivel in niveles:
        for letra in ['A', 'B']:
            grupo, created = Grupo.objects.get_or_create(
                nivel=nivel,
                letra=letra,
                defaults={'capacidad_maxima': 40}
            )
            if created:
                print(f"✅ Grupo {nivel.numero}°{letra} creado")
    
    # 5. CREAR AULAS
    aulas_data = [
        {'nombre': 'Aula 101', 'capacidad': 45, 'descripcion': 'Aula principal'},
        {'nombre': 'Aula 102', 'capacidad': 45, 'descripcion': 'Aula secundaria'},
        {'nombre': 'Aula 201', 'capacidad': 40, 'descripcion': 'Aula segundo piso'},
        {'nombre': 'Aula 202', 'capacidad': 40, 'descripcion': 'Aula segundo piso'},
        {'nombre': 'Lab Ciencias', 'capacidad': 30, 'descripcion': 'Laboratorio'},
        {'nombre': 'Lab Computación', 'capacidad': 35, 'descripcion': 'Sala de cómputo'},
        {'nombre': 'Aula 301', 'capacidad': 40, 'descripcion': 'Aula tercer piso'},
        {'nombre': 'Aula 302', 'capacidad': 40, 'descripcion': 'Aula tercer piso'},
        {'nombre': 'Gimnasio', 'capacidad': 50, 'descripcion': 'Educación física'},
        {'nombre': 'Aula Arte', 'capacidad': 30, 'descripcion': 'Taller de arte'},
        {'nombre': 'Biblioteca', 'capacidad': 25, 'descripcion': 'Sala de estudio'},
        {'nombre': 'Auditorio', 'capacidad': 100, 'descripcion': 'Eventos generales'}
    ]
    
    for aula_data in aulas_data:
        aula, created = Aula.objects.get_or_create(
            nombre=aula_data['nombre'],
            defaults=aula_data
        )
        if created:
            print(f"✅ {aula_data['nombre']} creada")
    
    print(f"\n📊 Resumen:")
    print(f"📊 Gestiones: {Gestion.objects.count()}")
    print(f"📊 Trimestres: {Trimestre.objects.filter(gestion=gestion_2023).count()}")
    print(f"📊 Niveles: {Nivel.objects.count()}")
    print(f"📊 Grupos: {Grupo.objects.count()}")
    print(f"📊 Aulas: {Aula.objects.count()}")

if __name__ == '__main__':
    setup_academic_year_2023()