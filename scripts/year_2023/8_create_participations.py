import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from evaluations.models import Participacion, Asistencia
from academic.models import Matriculacion, Horario, Gestion
import random
import time
from django.db import transaction


def create_participations_optimized():
    print("🙋 Creando registros de participación (optimizado)...")

    # Obtener datos necesarios
    gestion_2023 = Gestion.objects.get(anio=2023)

    # Obtener asistencias presentes en lotes más pequeños para no saturar memoria
    total_presentes = Asistencia.objects.filter(
        estado='P',
        matriculacion__gestion=gestion_2023
    ).count()

    print(f"📊 Total asistencias 'Presente': {total_presentes:,}")
    print(f"📊 Participaciones estimadas (30%): {int(total_presentes * 0.3):,}")

    batch_size = 500  # Procesar asistencias en lotes
    participation_batch_size = 100  # Insertar participaciones en lotes
    total_participaciones = 0
    offset = 0

    participaciones_to_create = []

    while offset < total_presentes:
        print(f"📈 Procesando lote {offset:,} - {min(offset + batch_size, total_presentes):,}")

        # Obtener lote de asistencias
        asistencias_lote = Asistencia.objects.filter(
            estado='P',
            matriculacion__gestion=gestion_2023
        ).select_related('matriculacion', 'horario')[offset:offset + batch_size]

        for asistencia in asistencias_lote:
            # 30% de probabilidad de participación
            if random.random() < 0.3:
                # Verificar si ya existe (básico, para evitar duplicados obvios)
                if not Participacion.objects.filter(
                        matriculacion=asistencia.matriculacion,
                        horario=asistencia.horario,
                        fecha=asistencia.fecha
                ).exists():

                    descripcion, valor = generate_participation_data()

                    participacion = Participacion(
                        matriculacion=asistencia.matriculacion,
                        horario=asistencia.horario,
                        fecha=asistencia.fecha,
                        descripcion=descripcion,
                        valor=valor
                    )
                    participaciones_to_create.append(participacion)

                    # Insertar participaciones en lotes
                    if len(participaciones_to_create) >= participation_batch_size:
                        created = bulk_create_participations_with_retry(participaciones_to_create)
                        total_participaciones += created
                        participaciones_to_create = []
                        time.sleep(0.1)  # Pequeña pausa

        offset += batch_size
        time.sleep(0.5)  # Pausa entre lotes de asistencias

    # Insertar participaciones restantes
    if participaciones_to_create:
        created = bulk_create_participations_with_retry(participaciones_to_create)
        total_participaciones += created

    print(f"\n📊 Total participaciones creadas: {total_participaciones:,}")
    print(f"📊 Total participaciones en BD: {Participacion.objects.count():,}")

    # Estadísticas por valor de participación
    print("\n📈 Distribución de participaciones por valor:")
    for valor in range(1, 6):
        count = Participacion.objects.filter(valor=valor).count()
        porcentaje = (count / total_participaciones * 100) if total_participaciones > 0 else 0
        descripcion_valor = get_participation_description(valor)
        print(f"   Valor {valor} ({descripcion_valor}): {count:,} ({porcentaje:.1f}%)")

    # Top 5 estudiantes más participativos (solo si no hay demasiados datos)
    if total_participaciones < 50000:  # Solo mostrar si es manejable
        show_top_participants()
    else:
        print("\n💡 Demasiados datos para mostrar top participantes (optimización)")


def bulk_create_participations_with_retry(participaciones_list, max_retries=3):
    """Inserción masiva de participaciones con reintentos"""
    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Filtrar duplicados básicos
                unique_participaciones = []
                seen = set()

                for participacion in participaciones_list:
                    key = (participacion.matriculacion_id, participacion.horario_id, participacion.fecha)
                    if key not in seen:
                        seen.add(key)
                        unique_participaciones.append(participacion)

                if unique_participaciones:
                    Participacion.objects.bulk_create(unique_participaciones, ignore_conflicts=True)
                    return len(unique_participaciones)
                return 0

        except Exception as e:
            print(f"      ⚠️ Error en lote participaciones (intento {attempt + 1}): {str(e)[:80]}...")
            if attempt == max_retries - 1:
                print(f"      ❌ Lote fallido después de {max_retries} intentos")
                return 0
            time.sleep(2 ** attempt)

    return 0


def show_top_participants():
    """Muestra top 5 estudiantes más participativos"""
    print("\n🏆 Top 5 estudiantes más participativos:")
    from django.db.models import Count

    try:
        top_participaciones = Participacion.objects.values(
            'matriculacion__alumno__nombres',
            'matriculacion__alumno__apellidos',
            'matriculacion__alumno__grupo__nivel__numero',
            'matriculacion__alumno__grupo__letra'
        ).annotate(
            total_participaciones=Count('id')
        ).order_by('-total_participaciones')[:5]

        for i, estudiante in enumerate(top_participaciones, 1):
            print(
                f"   {i}. {estudiante['matriculacion__alumno__nombres']} {estudiante['matriculacion__alumno__apellidos']} "
                f"({estudiante['matriculacion__alumno__grupo__nivel__numero']}°{estudiante['matriculacion__alumno__grupo__letra']}) "
                f"- {estudiante['total_participaciones']} participaciones")
    except Exception as e:
        print(f"   ⚠️ Error mostrando top participantes: {e}")


def generate_participation_data():
    """Genera descripción y valor realista de participación"""
    participaciones_tipos = [
        ("Respuesta correcta", [4, 5]),
        ("Pregunta relevante", [3, 4, 5]),
        ("Participación voluntaria", [3, 4]),
        ("Ayuda a compañeros", [4, 5]),
        ("Presentación oral", [3, 4, 5]),
        ("Respuesta parcial", [2, 3]),
        ("Intento de respuesta", [2, 3]),
        ("Contribución al debate", [3, 4, 5]),
        ("Explicación de procedimiento", [4, 5]),
        ("Corrección de error", [3, 4])
    ]

    descripcion, valores_posibles = random.choice(participaciones_tipos)
    valor = random.choice(valores_posibles)

    return descripcion, valor


def get_participation_description(valor):
    """Retorna descripción del valor de participación"""
    descripciones = {
        1: "Muy básica",
        2: "Básica",
        3: "Regular",
        4: "Buena",
        5: "Excelente"
    }
    return descripciones.get(valor, "Unknown")


if __name__ == '__main__':
    random.seed(2023)
    create_participations_optimized()