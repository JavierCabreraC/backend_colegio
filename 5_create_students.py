import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Usuario, Alumno
from academic.models import Grupo, Gestion, Matriculacion
from datetime import date
import random

def create_students():
    print("👨‍🎓 Creando estudiantes...")
    
    # Obtener gestión 2023 y grupos
    gestion_2023 = Gestion.objects.get(anio=2023)
    grupos = Grupo.objects.all().order_by('nivel__numero', 'letra')
    
    # Nombres y apellidos bolivianos
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
    matriculated_count = 0
    
    for grupo in grupos:
        print(f"\n📋 Creando estudiantes para {grupo.nivel.numero}°{grupo.letra}...")
        
        # Crear 10 estudiantes por grupo
        for i in range(1, 11):
            # Generar datos aleatorios
            genero = random.choice(['M', 'F'])
            if genero == 'M':
                nombre = random.choice(nombres_masculinos)
            else:
                nombre = random.choice(nombres_femeninos)
            
            apellido1 = random.choice(apellidos)
            apellido2 = random.choice(apellidos)
            
            # Generar matrícula única
            matricula = f"2023{grupo.nivel.numero:02d}{grupo.letra}{i:02d}"
            
            # Generar email
            email = f"estudiante.{nombre.lower()}.{apellido1.lower()}{i}@colegio.com"
            
            # Generar CI único
            ci_base = f"CI{grupo.nivel.numero:02d}{ord(grupo.letra):02d}{i:03d}"
            
            # Calcular edad apropiada para el nivel
            edad_base = 12 + grupo.nivel.numero  # 1° = 13 años, 6° = 18 años
            año_nacimiento = 2023 - edad_base
            mes_nacimiento = random.randint(1, 12)
            dia_nacimiento = random.randint(1, 28)
            
            # Crear usuario si no existe
            if not Usuario.objects.filter(email=email).exists():
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
                    direccion=f"Calle {random.choice(['Libertad', 'Bolivar', 'Sucre', 'Murillo', 'Ballivián'])} {random.randint(100, 999)}",
                    nombre_tutor=f"{random.choice(nombres_masculinos if random.choice([True, False]) else nombres_femeninos)} {random.choice(apellidos)}",
                    telefono_tutor=f"7{random.randint(1000000, 9999999)}",
                    grupo=grupo
                )
                
                # Matricular en la gestión 2023
                matriculacion = Matriculacion.objects.create(
                    alumno=alumno,
                    gestion=gestion_2023,
                    fecha_matriculacion=date(2023, 1, 15),
                    activa=True,
                    observaciones='Matriculación inicial 2023'
                )
                
                print(f"   ✅ {nombre} {apellido1} - {matricula}")
                created_count += 1
                matriculated_count += 1
            else:
                print(f"   ⚠️ {email} ya existía")
    
    print(f"\n📊 Estudiantes creados: {created_count}")
    print(f"📊 Matriculaciones creadas: {matriculated_count}")
    print(f"📊 Total estudiantes: {Alumno.objects.count()}")
    print(f"📊 Total matriculaciones 2023: {Matriculacion.objects.filter(gestion=gestion_2023).count()}")
    
    # Mostrar estadísticas por grupo
    print("\n📋 Distribución por grupos:")
    for grupo in grupos:
        count = Alumno.objects.filter(grupo=grupo).count()
        print(f"   {grupo.nivel.numero}°{grupo.letra}: {count} estudiantes")
    
    # Mostrar algunas credenciales de ejemplo
    print("\n🔐 Ejemplos de credenciales de estudiantes:")
    print("   Email: estudiante.carlos.garcia1@colegio.com / estudiante123")
    print("   Email: estudiante.maria.lopez1@colegio.com / estudiante123")
    print("   (Patrón: estudiante.[nombre].[apellido][numero]@colegio.com)")

if __name__ == '__main__':
    # Establecer semilla para reproducibilidad
    random.seed(2023)
    create_students()