import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Alumno
from academic.models import Grupo, Nivel, Gestion, Matriculacion
from datetime import date
import time
from django.db import transaction


def promote_students_2024():
    print("📈 Promoviendo estudiantes al año 2024...")

    # Obtener gestiones
    try:
        gestion_2023 = Gestion.objects.get(anio=2023)
        gestion_2024 = Gestion.objects.get(anio=2024)
    except Gestion.DoesNotExist as e:
        print(f"❌ Error: {e}")
        return

    # Obtener todos los estudiantes matriculados en 2023
    matriculaciones_2023 = Matriculacion.objects.filter(gestion=gestion_2023, activa=True)
    print(f"📊 Estudiantes matriculados en 2023: {matriculaciones_2023.count()}")

    # Estadísticas por nivel actual
    print("\n📋 Distribución actual por niveles:")
    for nivel_num in range(1, 7):
        count = matriculaciones_2023.filter(alumno__grupo__nivel__numero=nivel_num).count()
        print(f"   {nivel_num}°: {count} estudiantes")

    promoted_count = 0
    graduated_count = 0
    matriculated_count = 0

    # Procesar promociones en lotes para evitar saturar la BD
    batch_size = 20
    total_students = matriculaciones_2023.count()
    processed = 0

    print(f"\n🔄 Iniciando promociones (lotes de {batch_size})...")

    for i in range(0, total_students, batch_size):
        batch_matriculaciones = matriculaciones_2023[i:i + batch_size]
        print(
            f"📦 Procesando lote {i // batch_size + 1} ({i + 1}-{min(i + batch_size, total_students)}/{total_students})")

        for matriculacion in batch_matriculaciones:
            alumno = matriculacion.alumno
            nivel_actual = alumno.grupo.nivel.numero
            grupo_actual_letra = alumno.grupo.letra

            try:
                with transaction.atomic():
                    if nivel_actual == 6:
                        # Estudiantes de 6° se gradúan
                        matriculacion.activa = False
                        matriculacion.observaciones = "Graduado 2023"
                        matriculacion.save()
                        graduated_count += 1
                        print(f"   🎓 {alumno.nombres} {alumno.apellidos} - GRADUADO")

                    else:
                        # Promover al siguiente nivel
                        nuevo_nivel_num = nivel_actual + 1
                        nuevo_nivel = Nivel.objects.get(numero=nuevo_nivel_num)
                        nuevo_grupo = Grupo.objects.get(nivel=nuevo_nivel, letra=grupo_actual_letra)

                        # Actualizar grupo del alumno
                        alumno.grupo = nuevo_grupo
                        alumno.save()

                        # Desactivar matriculación 2023
                        matriculacion.activa = False
                        matriculacion.observaciones = f"Promovido a {nuevo_nivel_num}°"
                        matriculacion.save()

                        # Crear nueva matriculación para 2024
                        nueva_matriculacion = Matriculacion.objects.create(
                            alumno=alumno,
                            gestion=gestion_2024,
                            fecha_matriculacion=date(2024, 1, 15),
                            activa=True,
                            observaciones=f"Promoción automática desde {nivel_actual}°"
                        )

                        promoted_count += 1
                        matriculated_count += 1
                        print(
                            f"   ✅ {alumno.nombres} {alumno.apellidos} - {nivel_actual}°{grupo_actual_letra} → {nuevo_nivel_num}°{grupo_actual_letra}")

                processed += 1

            except Exception as e:
                print(f"   ❌ Error procesando {alumno.nombres} {alumno.apellidos}: {e}")

        # Pausa entre lotes para no saturar la BD
        time.sleep(0.5)

        # Progreso cada 5 lotes
        if (i // batch_size + 1) % 5 == 0:
            print(f"   📊 Progreso: {processed}/{total_students} estudiantes procesados")

    print(f"\n📊 Resumen de promociones:")
    print(f"✅ Estudiantes promovidos: {promoted_count}")
    print(f"🎓 Estudiantes graduados: {graduated_count}")
    print(f"📝 Nuevas matriculaciones 2024: {matriculated_count}")

    # Verificar distribución final 2024
    print(f"\n📋 Nueva distribución 2024:")
    matriculaciones_2024 = Matriculacion.objects.filter(gestion=gestion_2024, activa=True)
    print(f"📊 Total matriculados 2024: {matriculaciones_2024.count()}")

    for nivel_num in range(1, 7):
        count = matriculaciones_2024.filter(alumno__grupo__nivel__numero=nivel_num).count()
        print(f"   {nivel_num}°: {count} estudiantes")

    print(f"\n💡 Nota: El nivel 1° está vacío y necesita nuevos estudiantes")


if __name__ == '__main__':
    promote_students_2024()