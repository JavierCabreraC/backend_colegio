import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Usuario, Alumno
from academic.models import Grupo, Nivel, Gestion, Matriculacion
from datetime import date
import random
import time
from django.db import transaction


def create_new_students_2024():
    print("👨‍🎓 Creando nuevos estudiantes para 1° nivel (2024)...")

    # Obtener datos necesarios
    try:
        gestion_2024 = Gestion.objects.get(anio=2024)
        nivel_1 = Nivel.objects.get(numero=1)
        grupos_1 = Grupo.objects.filter(nivel=nivel_1).order_by('letra')
    except Exception as e:
        print(f"❌ Error obteniendo datos: {e}")
        return

    print(f"📊 Grupos de 1° nivel: {grupos_1.count()}")
    for grupo in grupos_1:
        existing = Alumno.objects.filter(grupo=grupo).count()
        print(f"   1°{grupo.letra}: {existing} estudiantes existentes")

    # Datos para generar estudiantes
    nombres_masculinos = [
        'Carlos', 'Luis', 'José', 'Miguel', 'Pedro', 'Juan', 'Diego', 'Fernando',
        'Andrés', 'Roberto', 'Daniel', 'Alejandro', 'Marco', 'Sergio', 'Ricardo',
        'Pablo', 'Javier', 'Eduardo', 'Raúl', 'Gonzalo'
    ]

    nombres_femeninos = [
        'María', 'Ana', 'Carmen', 'Rosa', 'Elena', 'Patricia', 'Isabel', 'Lucía',
        'Fernanda', 'Carla', 'Andrea', 'Paola', 'Daniela', 'Gabriela', 'Mónica',
        'Claudia', 'Valeria', 'Sofía', 'Natalia', 'Alejandra'
    ]

    apellidos = [
        'García', 'López', 'Martínez', 'González', 'Rodríguez', 'Fernández', 'Morales',
        'Vargas', 'Herrera', 'Mendoza', 'Chávez', 'Rojas', 'Sánchez', 'Torrez',
        'Vega', 'Flores', 'Castro', 'Ruiz', 'Peña', 'Aguilar', 'Romero', 'Durán',
        'Silva', 'Campos', 'Ortiz', 'Jiménez'
    ]

    created_count = 0
    matriculated_count = 0

    for grupo in grupos_1:
        print(f"\n📋 Creando estudiantes para 1°{grupo.letra}...")

        # Verificar cuántos ya existen
        existing_count = Alumno.objects.filter(grupo=grupo).count()
        students_needed = 10 - existing_count

        if students_needed <= 0:
            print(f"   ✅ Grupo ya completo ({existing_count}/10)")
            continue

        print(f"   📊 Necesarios: {students_needed} estudiantes")

        for i in range(existing_count + 1, 11):
            success = create_single_student_2024(
                grupo, i, gestion_2024, nombres_masculinos,
                nombres_femeninos, apellidos
            )

            if success:
                created_count += 1
                matriculated_count += 1
                print(f"   ✅ Estudiante {i}/10 creado")
            else:
                print(f"   ❌ Error creando estudiante {i}/10")

            # Pausa entre estudiantes para evitar saturar
            time.sleep(0.5)

        # Pausa más larga entre grupos
        time.sleep(1)

    print(f"\n📊 Resumen:")
    print(f"✅ Nuevos estudiantes creados: {created_count}")
    print(f"📝 Nuevas matriculaciones: {matriculated_count}")

    # Verificación final
    print(f"\n📋 Estado final de 1° nivel:")
    total_2024 = 0
    for grupo in grupos_1:
        count = Alumno.objects.filter(grupo=grupo).count()
        total_2024 += count
        status = "✅" if count == 10 else "⚠️"
        print(f"   {status} 1°{grupo.letra}: {count}/10 estudiantes")

    print(f"\n📊 Total estudiantes 1° nivel: {total_2024}/20")
    print(f"📊 Total matriculaciones 2024: {Matriculacion.objects.filter(gestion=gestion_2024).count()}")


def create_single_student_2024(grupo, numero, gestion, nombres_m, nombres_f, apellidos, max_retries=3):
    """Crea un estudiante con reintentos en caso de error"""

    for attempt in range(max_retries):
        try:
            with transaction.atomic():
                # Generar datos
                genero = random.choice(['M', 'F'])
                nombre = random.choice(nombres_m if genero == 'M' else nombres_f)
                apellido1 = random.choice(apellidos)
                apellido2 = random.choice(apellidos)

                # Matrícula 2024 con formato: 2024 + nivel + grupo + número
                matricula = f"2024{grupo.nivel.numero:02d}{grupo.letra}{numero:02d}"
                email = f"estudiante.{nombre.lower()}.{apellido1.lower()}.2024.{numero}@colegio.com"
                ci_base = f"CI24{grupo.nivel.numero:02d}{ord(grupo.letra):02d}{numero:03d}"

                # Verificar si ya existe
                if Usuario.objects.filter(email=email).exists():
                    return True  # Ya existe, consideramos éxito

                if Alumno.objects.filter(matricula=matricula).exists():
                    print(f"      ⚠️ Matrícula {matricula} ya existe")
                    return False

                # Edad apropiada para 1° (13 años)
                año_nacimiento = 2024 - 13
                mes_nacimiento = random.randint(1, 12)
                dia_nacimiento = random.randint(1, 28)

                # Crear usuario
                usuario = Usuario.objects.create_user(
                    email=email,
                    password='estudiante123',
                    tipo_usuario='alumno'
                )

                # Crear alumno
                alumno = Alumno.objects.create(
                    usuario=usuario,
                    matricula=matricula,
                    nombres=nombre,
                    apellidos=f"{apellido1} {apellido2}",
                    fecha_nacimiento=date(año_nacimiento, mes_nacimiento, dia_nacimiento),
                    genero=genero,
                    telefono=f"7{random.randint(1000000, 9999999)}",
                    direccion=f"Calle {random.choice(['Libertad', 'Bolivar', 'Sucre', 'Murillo'])} {random.randint(100, 999)}",
                    nombre_tutor=f"{random.choice(nombres_m + nombres_f)} {random.choice(apellidos)}",
                    telefono_tutor=f"7{random.randint(1000000, 9999999)}",
                    grupo=grupo
                )

                # Matricular en 2024
                Matriculacion.objects.create(
                    alumno=alumno,
                    gestion=gestion,
                    fecha_matriculacion=date(2024, 1, 15),
                    activa=True,
                    observaciones='Nuevo ingreso 2024'
                )

                return True

        except Exception as e:
            print(f"      ⚠️ Intento {attempt + 1} falló: {str(e)[:80]}...")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponencial

    return False


if __name__ == '__main__':
    random.seed(2024)  # Nueva semilla para 2024
    create_new_students_2024()