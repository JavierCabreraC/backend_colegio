import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Usuario, Alumno
from academic.models import Grupo, Gestion, Matriculacion
from datetime import date
import random
import time


def complete_students():
    print("🔧 Completando estudiantes faltantes...")

    # Verificar estado actual
    gestion_2023 = Gestion.objects.get(anio=2023)
    grupos = Grupo.objects.all().order_by('nivel__numero', 'letra')

    print("📊 Estado actual por grupo:")
    total_existentes = 0
    grupos_incompletos = []

    for grupo in grupos:
        count = Alumno.objects.filter(grupo=grupo).count()
        print(f"   {grupo.nivel.numero}°{grupo.letra}: {count}/10 estudiantes")
        total_existentes += count

        if count < 10:
            grupos_incompletos.append((grupo, count))

    print(f"\n📊 Total estudiantes existentes: {total_existentes}/120")
    print(f"📊 Grupos incompletos: {len(grupos_incompletos)}")

    if not grupos_incompletos:
        print("✅ Todos los grupos están completos!")
        return

    # Datos para generar estudiantes
    nombres_masculinos = [
        'Carlos', 'Luis', 'José', 'Miguel', 'Pedro', 'Juan', 'Diego', 'Fernando',
        'Andrés', 'Roberto', 'Daniel', 'Alejandro', 'Marco', 'Sergio', 'Ricardo'
    ]

    nombres_femeninos = [
        'María', 'Ana', 'Carmen', 'Rosa', 'Elena', 'Patricia', 'Isabel', 'Lucía',
        'Fernanda', 'Carla', 'Andrea', 'Paola', 'Daniela', 'Gabriela', 'Mónica'
    ]

    apellidos = [
        'García', 'López', 'Martínez', 'González', 'Rodríguez', 'Fernández', 'Morales',
        'Vargas', 'Herrera', 'Mendoza', 'Chávez', 'Rojas', 'Sánchez', 'Torrez',
        'Vega', 'Flores', 'Castro', 'Ruiz', 'Peña', 'Aguilar', 'Romero', 'Durán'
    ]

    created_count = 0

    # Completar grupos incompletos
    for grupo, count_actual in grupos_incompletos:
        print(f"\n📋 Completando {grupo.nivel.numero}°{grupo.letra} (tiene {count_actual}/10)...")

        for i in range(count_actual + 1, 11):  # Desde donde se quedó hasta 10
            try:
                # Generar datos
                genero = random.choice(['M', 'F'])
                nombre = random.choice(nombres_masculinos if genero == 'M' else nombres_femeninos)
                apellido1 = random.choice(apellidos)
                apellido2 = random.choice(apellidos)

                matricula = f"2023{grupo.nivel.numero:02d}{grupo.letra}{i:02d}"
                email = f"estudiante.{nombre.lower()}.{apellido1.lower()}{i}@colegio.com"
                ci_base = f"CI{grupo.nivel.numero:02d}{ord(grupo.letra):02d}{i:03d}"

                # Verificar si ya existe
                if Usuario.objects.filter(email=email).exists():
                    print(f"   ⚠️ {email} ya existe, omitiendo...")
                    continue

                # Calcular edad
                edad_base = 12 + grupo.nivel.numero
                año_nacimiento = 2023 - edad_base
                mes_nacimiento = random.randint(1, 12)
                dia_nacimiento = random.randint(1, 28)

                # Crear con pausa para evitar sobrecarga
                print(f"   🔄 Creando {nombre} {apellido1}...")

                usuario = Usuario.objects.create_user(
                    email=email,
                    password='estudiante123',
                    tipo_usuario='alumno'
                )

                time.sleep(0.2)  # Pausa pequeña

                alumno = Alumno.objects.create(
                    usuario=usuario,
                    matricula=matricula,
                    nombres=nombre,
                    apellidos=f"{apellido1} {apellido2}",
                    fecha_nacimiento=date(año_nacimiento, mes_nacimiento, dia_nacimiento),
                    genero=genero,
                    telefono=f"7{random.randint(1000000, 9999999)}",
                    direccion=f"Calle {random.choice(['Libertad', 'Bolivar', 'Sucre'])} {random.randint(100, 999)}",
                    nombre_tutor=f"{random.choice(nombres_masculinos)} {random.choice(apellidos)}",
                    telefono_tutor=f"7{random.randint(1000000, 9999999)}",
                    grupo=grupo
                )

                time.sleep(0.2)  # Pausa pequeña

                matriculacion = Matriculacion.objects.create(
                    alumno=alumno,
                    gestion=gestion_2023,
                    fecha_matriculacion=date(2023, 1, 15),
                    activa=True,
                    observaciones='Matriculación completada'
                )

                print(f"   ✅ {nombre} {apellido1} - {matricula}")
                created_count += 1

                time.sleep(0.3)  # Pausa entre estudiantes

            except Exception as e:
                print(f"   ❌ Error creando estudiante {i}: {e}")
                time.sleep(1)  # Pausa más larga en caso de error
                continue

        time.sleep(1)  # Pausa entre grupos

    print(f"\n📊 Estudiantes completados: {created_count}")
    print(f"📊 Total estudiantes final: {Alumno.objects.count()}")
    print(f"📊 Total matriculaciones 2023: {Matriculacion.objects.filter(gestion=gestion_2023).count()}")

    # Verificación final
    print("\n📋 Estado final por grupos:")
    for grupo in grupos:
        count = Alumno.objects.filter(grupo=grupo).count()
        status = "✅" if count == 10 else "⚠️"
        print(f"   {status} {grupo.nivel.numero}°{grupo.letra}: {count}/10 estudiantes")


if __name__ == '__main__':
    random.seed(2023)
    complete_students()