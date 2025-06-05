import os
import sys
import django
from pathlib import Path


# Configurar Django
def setup_django():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir
    while project_root.parent != project_root:
        if (project_root / 'manage.py').exists():
            break
        project_root = project_root.parent
    sys.path.insert(0, str(project_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
    django.setup()


setup_django()

from audit.models import Bitacora
from authentication.models import Usuario, Profesor
from datetime import datetime, timedelta
import random
import time
from django.db import transaction


def create_audit_logs():
    print("📋 Creando registros de bitácora para profesores...")

    # Obtener algunos profesores (no todos)
    try:
        # Seleccionar solo 5-6 profesores que "usan más el sistema"
        all_profesores = list(Profesor.objects.all())
        if len(all_profesores) < 6:
            selected_profesores = all_profesores
        else:
            selected_profesores = random.sample(all_profesores, 6)

        print(f"📊 Profesores seleccionados para bitácora: {len(selected_profesores)}")
        for prof in selected_profesores:
            print(f"   👨‍🏫 {prof.nombres} {prof.apellidos}")

    except Exception as e:
        print(f"❌ Error obteniendo profesores: {e}")
        return

    # Tipos de acciones típicas de profesores
    acciones_profesores = [
        "login",
        "logout",
        "ver_horarios",
        "registrar_nota",
        "modificar_nota",
        "ver_estudiantes",
        "tomar_asistencia",
        "crear_examen",
        "modificar_examen",
        "ver_participaciones",
        "generar_reporte",
        "actualizar_perfil",
        "ver_calendario",
        "consultar_notas"
    ]

    # IPs típicas (simuladas)
    ips_tipicas = [
        "192.168.1.45",
        "192.168.1.67",
        "192.168.1.23",
        "10.0.0.15",
        "10.0.0.28",
        "172.16.1.10",
        "192.168.0.105"
    ]

    total_registros = 0
    batch_size = 50

    # Generar registros para 2023 y 2024
    for anio in [2023, 2024]:
        print(f"\n📅 Generando registros para {anio}...")

        # Fechas del año escolar
        if anio == 2023:
            fecha_inicio = datetime(2023, 2, 1)
            fecha_fin = datetime(2023, 11, 30)
        else:  # 2024
            fecha_inicio = datetime(2024, 2, 1)
            # Para 2024, hasta hoy o fin de año
            fecha_fin = min(datetime.now(), datetime(2024, 11, 30))

        registros_to_create = []

        for profesor in selected_profesores:
            # Cada profesor tiene diferente frecuencia de uso
            freq_seed = profesor.usuario.id % 3

            if freq_seed == 0:  # Usuario frecuente
                acciones_por_mes = random.randint(15, 25)
            elif freq_seed == 1:  # Usuario ocasional
                acciones_por_mes = random.randint(8, 15)
            else:  # Usuario poco frecuente
                acciones_por_mes = random.randint(3, 8)

            # Generar acciones distribuidas en el año
            current_date = fecha_inicio
            while current_date <= fecha_fin:
                # Solo días laborables (lunes a viernes)
                if current_date.weekday() < 5:
                    # Probabilidad de actividad en este día
                    if random.random() < 0.3:  # 30% probabilidad por día
                        num_acciones = random.randint(1, 4)

                        for _ in range(num_acciones):
                            accion = random.choice(acciones_profesores)
                            ip = random.choice(ips_tipicas)

                            # Hora aleatoria durante el día (7:00 AM - 6:00 PM)
                            hora_base = current_date.replace(hour=7, minute=0, second=0)
                            minutos_aleatorios = random.randint(0, 11 * 60)  # 11 horas
                            fecha_hora = hora_base + timedelta(minutes=minutos_aleatorios)

                            registro = Bitacora(
                                usuario=profesor.usuario,
                                tipo_accion=accion,
                                ip=ip,
                                fecha_hora=fecha_hora
                            )
                            registros_to_create.append(registro)

                            # Insertar en lotes
                            if len(registros_to_create) >= batch_size:
                                created = bulk_create_logs_safe(registros_to_create)
                                total_registros += created
                                registros_to_create = []
                                time.sleep(0.1)

                current_date += timedelta(days=1)

        # Insertar registros restantes del año
        if registros_to_create:
            created = bulk_create_logs_safe(registros_to_create)
            total_registros += created

        print(f"   ✅ Año {anio} completado")

    print(f"\n📊 Total registros de bitácora creados: {total_registros}")

    # Estadísticas finales
    try:
        total_final = Bitacora.objects.count()
        print(f"📊 Total registros en bitácora: {total_final}")

        # Top 5 acciones más frecuentes
        print(f"\n📈 Top 5 acciones más registradas:")
        from django.db.models import Count

        top_acciones = Bitacora.objects.values('tipo_accion').annotate(
            count=Count('tipo_accion')
        ).order_by('-count')[:5]

        for i, accion in enumerate(top_acciones, 1):
            print(f"   {i}. {accion['tipo_accion']}: {accion['count']} veces")

        # Actividad por profesor
        print(f"\n👨‍🏫 Actividad por profesor:")
        actividad_profesores = Bitacora.objects.values(
            'usuario__profesor__nombres',
            'usuario__profesor__apellidos'
        ).annotate(
            total_acciones=Count('id')
        ).order_by('-total_acciones')

        for prof in actividad_profesores:
            if prof['usuario__profesor__nombres']:  # Solo profesores, no otros usuarios
                print(
                    f"   {prof['usuario__profesor__nombres']} {prof['usuario__profesor__apellidos']}: {prof['total_acciones']} acciones")

        # Distribución por año
        for anio in [2023, 2024]:
            count = Bitacora.objects.filter(
                fecha_hora__year=anio
            ).count()
            print(f"📊 Registros {anio}: {count}")

    except Exception as e:
        print(f"⚠️ Error en estadísticas finales: {e}")


def bulk_create_logs_safe(logs_list, max_retries=3):
    """Inserción masiva de logs con reintentos"""
    if not logs_list:
        return 0

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Los logs de bitácora normalmente no tienen duplicados
                # porque incluyen timestamp exacto, pero usamos ignore_conflicts por seguridad
                Bitacora.objects.bulk_create(logs_list, ignore_conflicts=True)
                return len(logs_list)

        except Exception as e:
            print(f"      ⚠️ Error en lote de logs (intento {attempt + 1}): {str(e)[:80]}...")
            if attempt == max_retries - 1:
                print(f"      ❌ Lote fallido después de {max_retries} intentos")
                return 0
            time.sleep(2 ** attempt)

    return 0


if __name__ == '__main__':
    random.seed(2024)  # Para reproducibilidad
    create_audit_logs()