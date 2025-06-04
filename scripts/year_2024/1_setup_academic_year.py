import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from academic.models import Gestion, Trimestre
from datetime import date


def setup_academic_year_2024():
    print("🗓️ Configurando año académico 2024...")

    # 1. DESACTIVAR GESTIÓN 2023
    try:
        gestion_2023 = Gestion.objects.get(anio=2023)
        gestion_2023.activa = False
        gestion_2023.save()
        print("✅ Gestión 2023 desactivada")
    except Gestion.DoesNotExist:
        print("⚠️ Gestión 2023 no encontrada")

    # 2. CREAR GESTIÓN 2024
    gestion_2024, created = Gestion.objects.get_or_create(
        anio=2024,
        defaults={
            'nombre': 'Gestión Académica 2024',
            'fecha_inicio': date(2024, 2, 1),
            'fecha_fin': date(2024, 11, 30),
            'activa': True
        }
    )
    if created:
        print("✅ Gestión 2024 creada y activada")
    else:
        # Asegurar que esté activa
        gestion_2024.activa = True
        gestion_2024.save()
        print("⚠️ Gestión 2024 ya existía, ahora está activa")

    # 3. CREAR TRIMESTRES 2024
    trimestres_data = [
        {
            'numero': 1,
            'nombre': 'Primer Trimestre 2024',
            'fecha_inicio': date(2024, 2, 1),
            'fecha_fin': date(2024, 4, 30)
        },
        {
            'numero': 2,
            'nombre': 'Segundo Trimestre 2024',
            'fecha_inicio': date(2024, 5, 1),
            'fecha_fin': date(2024, 8, 31)
        },
        {
            'numero': 3,
            'nombre': 'Tercer Trimestre 2024',
            'fecha_inicio': date(2024, 9, 1),
            'fecha_fin': date(2024, 11, 30)
        }
    ]

    trimestres_created = 0
    for trimestre_data in trimestres_data:
        trimestre, created = Trimestre.objects.get_or_create(
            gestion=gestion_2024,
            numero=trimestre_data['numero'],
            defaults=trimestre_data
        )
        if created:
            print(f"✅ {trimestre_data['nombre']} creado")
            trimestres_created += 1
        else:
            print(f"⚠️ {trimestre_data['nombre']} ya existía")

    print(f"\n📊 Resumen:")
    print(f"📊 Gestión activa: {Gestion.objects.get(activa=True).nombre}")
    print(f"📊 Trimestres 2024: {Trimestre.objects.filter(gestion=gestion_2024).count()}")
    print(f"📊 Nuevos trimestres creados: {trimestres_created}")

    # Verificar estado general
    print(f"\n🔍 Estado general del sistema:")
    print(f"📊 Total gestiones: {Gestion.objects.count()}")
    print(f"📊 Total trimestres: {Trimestre.objects.count()}")


if __name__ == '__main__':
    setup_academic_year_2024()