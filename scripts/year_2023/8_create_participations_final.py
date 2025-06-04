import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from evaluations.models import Participacion, Asistencia
from academic.models import Matriculacion, Horario, Gestion
import random
import time
from django.db import transaction
from django.db.models import Q


def create_participations_final():
    print("🙋 Creando registros de participación (versión final)...")

    # Obtener datos necesarios
    gestion_2023 = Gestion.objects.get(anio=2023)

    # Contar asistencias presentes sin cargarlas todas en memoria
    total_presentes = Asistencia.objects.filter(
        estado='P',
        matriculacion__gestion=gestion_2023
    ).count()

    print(f"📊 Total asistencias 'Presente': {total_presentes:,}")
    print(f"📊 Participaciones estimadas (30%): {int(total_presentes * 0.3):,}")

    # Verificar participaciones existentes
    existing_participations = Participacion.objects.count()
    print(f"📊 Participaciones existentes: {existing_participations:,}")

    if existing_participations > 0:
        print("⚠️ Ya existen participaciones. ¿Continuar? (se evitarán duplicados)")
        response = input("Continuar (s/n): ").lower()
        if response != 's':
            return

    batch_size = 1000  # Procesar más asistencias por lote
    participation_batch_size = 200  # Insertar más participaciones por lote
    total_participaciones = 0
    offset = 0

    participaciones_to_create = []
    processed_keys = set()  # Para evitar duplicados en memoria

    while offset < total_presentes:
        print(f"📈 Procesando lote {offset:,} - {min(offset + batch_size, total_presentes):,}")

        try:
            # Obtener lote de asistencias con datos relacionados
            asistencias_lote = Asistencia.objects.filter(
                estado='P',
                matriculacion__gestion=gestion_2023
            ).select_related(
                'matriculacion', 'horario'
            ).only(
                'matriculacion_id', 'horario_id', 'fecha'
            )[offset:offset + batch_size]

            asistencias_list = list(asistencias_lote)  # Forzar evaluación de la query
            print(f"   📋 Asistencias obtenidas: {len(asistencias_list)}")

            for asistencia in asistencias_list:
                # 30% de probabilidad de participación
                if random.random() < 0.3:
                    # Crear clave única para evitar duplicados
                    key = (asistencia.matriculacion_id, asistencia.horario_id, asistencia.fecha)

                    if key not in processed_keys:
                        processed_keys.add(key)

                        descripcion, valor = generate_participation_data()

                        participacion = Participacion(
                            matriculacion_id=asistencia.matriculacion_id,
                            horario_id=asistencia.horario_id,
                            fecha=asistencia.fecha,
                            descripcion=descripcion,
                            valor=valor
                        )
                        participaciones_to_create.append(participacion)

                        # Insertar participaciones en lotes
                        if len(participaciones_to_create) >= participation_batch_size:
                            created = bulk_create_participations_safe(participaciones_to_create)
                            total_participaciones += created
                            participaciones_to_create = []
                            processed_keys.clear()  # Limpiar memoria
                            time.sleep(0.2)  # Pausa para estabilidad

            offset += batch_size
            time.sleep(1)  # Pausa entre lotes para dar respiro a la conexión

        except Exception as e:
            print(f"   ❌ Error en lote {offset}: {e}")
            print("   🔄 Reintentando en 5 segundos...")
            time.sleep(5)
            # No incrementar offset para reintentar el mismo lote
            continue

    # Insertar participaciones restantes
    if participaciones_to_create:
        created = bulk_create_participations_safe(participaciones_to_create)
        total_participaciones += created

    print(f"\n📊 Total participaciones creadas: {total_participaciones:,}")

    # Estadísticas finales con manejo de errores
    try:
        total_final = Participacion.objects.count()
        print(f"📊 Total participaciones en BD: {total_final:,}")

        # Estadísticas por valor de participación
        print("\n📈 Distribución de participaciones por valor:")
        for valor in range(1, 6):
            count = Participacion.objects.filter(valor=valor).count()
            porcentaje = (count / total_final * 100) if total_final > 0 else 0
            descripcion_valor = get_participation_description(valor)
            print(f"   Valor {valor} ({descripcion_valor}): {count:,} ({porcentaje:.1f}%)")

    except Exception as e:
        print(f"⚠️ Error obteniendo estadísticas finales: {e}")

    print("\n✅ Proceso de participaciones completado")


def bulk_create_participations_safe(participaciones_list, max_retries=5):
    """Inserción masiva de participaciones con manejo robusto de errores"""
    if not participaciones_list:
        return 0

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Usar ignore_conflicts para manejar duplicados automáticamente
                Participacion.objects.bulk_create(
                    participaciones_list,
                    ignore_conflicts=True,
                    batch_size=50  # Lotes más pequeños para estabilidad
                )
                return len(participaciones_list)

        except Exception as e:
            error_msg = str(e)
            print(f"      ⚠️ Error en inserción (intento {attempt + 1}/{max_retries}): {error_msg[:100]}...")

            if attempt == max_retries - 1:
                print(f"      ❌ Lote fallido después de {max_retries} intentos")
                return 0

            # Pausa incremental con reconexión
            wait_time = (2 ** attempt) + random.uniform(0, 2)
            print(f"      ⏱️ Esperando {wait_time:.1f} segundos antes del siguiente intento...")
            time.sleep(wait_time)

            # Intentar reconectar cerrando la conexión actual
            from django.db import connection
            connection.close()

    return 0


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
    create_participations_final()