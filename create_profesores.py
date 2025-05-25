import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Usuario, Profesor
from datetime import date


def create_profesores():
    print("👨‍🏫 Creando profesores de prueba...")

    profesores_data = [
        {
            'email': 'profesor1@sistema.com',
            'password': 'prof123',
            'nombres': 'María Elena',
            'apellidos': 'García Morales',
            'cedula_identidad': '11111111',
            'fecha_nacimiento': date(1985, 5, 20),
            'genero': 'F',
            'telefono': '72345678',
            'direccion': 'Barrio Norte 789, Santa Cruz',
            'especialidad': 'Matemáticas',
            'fecha_contratacion': date(2020, 3, 1)
        },
        {
            'email': 'profesor2@sistema.com',
            'password': 'prof456',
            'nombres': 'Roberto Carlos',
            'apellidos': 'Mendoza Silva',
            'cedula_identidad': '22222222',
            'fecha_nacimiento': date(1982, 11, 15),
            'genero': 'M',
            'telefono': '73456789',
            'direccion': 'Villa 1ro de Mayo 456',
            'especialidad': 'Física',
            'fecha_contratacion': date(2018, 8, 15)
        },
        {
            'email': 'profesor3@sistema.com',
            'password': 'prof789',
            'nombres': 'Carmen Rosa',
            'apellidos': 'Vásquez Torres',
            'cedula_identidad': '33333333',
            'fecha_nacimiento': date(1979, 7, 8),
            'genero': 'F',
            'telefono': '74567890',
            'direccion': 'Plan 3000 Sector 2',
            'especialidad': 'Química',
            'fecha_contratacion': date(2015, 2, 10)
        },
        {
            'email': 'profesor4@sistema.com',
            'password': 'prof101',
            'nombres': 'Fernando José',
            'apellidos': 'Ramírez Peña',
            'cedula_identidad': '44444444',
            'fecha_nacimiento': date(1987, 3, 25),
            'genero': 'M',
            'telefono': '75678901',
            'direccion': 'Av. Banzer Km 9',
            'especialidad': 'Lenguaje',
            'fecha_contratacion': date(2019, 7, 1)
        },
        {
            'email': 'profesor5@sistema.com',
            'password': 'prof202',
            'nombres': 'Silvia Beatriz',
            'apellidos': 'Choque Mamani',
            'cedula_identidad': '55555555',
            'fecha_nacimiento': date(1984, 12, 30),
            'genero': 'F',
            'telefono': '76789012',
            'direccion': 'Zona Sur, Calle Principal 123',
            'especialidad': 'Historia',
            'fecha_contratacion': date(2021, 1, 15)
        }
    ]

    # Crear cada profesor
    for i, profesor_data in enumerate(profesores_data, 1):
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
                especialidad=profesor_data['especialidad'],
                fecha_contratacion=profesor_data['fecha_contratacion']
            )

            print(f"✅ Profesor {i} creado: {email}")
            print(f"   {profesor_data['nombres']} {profesor_data['apellidos']} - {profesor_data['especialidad']}")
        else:
            print(f"⚠️  Profesor {i} ya existe: {email}")

    print(f"\n📊 Total profesores: {Profesor.objects.count()}")
    print("\n🔐 Credenciales creadas:")
    print("profesor1@sistema.com / prof123 (Matemáticas)")
    print("profesor2@sistema.com / prof456 (Física)")
    print("profesor3@sistema.com / prof789 (Química)")
    print("profesor4@sistema.com / prof101 (Lenguaje)")
    print("profesor5@sistema.com / prof202 (Historia)")


if __name__ == '__main__':
    create_profesores()
