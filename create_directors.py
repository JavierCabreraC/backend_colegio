## Script de prueba

import os
import django
import sys

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Usuario, Director
from datetime import date


def create_directors():
    print("🏫 Creando directores de prueba para el sistema académico...")

    # Datos de los directores
    directores_data = [
        {
            'email': 'director1@sistema.com',
            'password': 'director123',
            'nombres': 'Ana María',
            'apellidos': 'Gutiérrez López',
            'cedula_identidad': '12345678',
            'fecha_nacimiento': date(1975, 8, 15),
            'genero': 'F',
            'telefono': '70123456',
            'direccion': 'Av. Central 123, Santa Cruz'
        },
        {
            'email': 'director2@sistema.com',
            'password': 'director456',
            'nombres': 'Carlos Eduardo',
            'apellidos': 'Pérez Mendoza',
            'cedula_identidad': '87654321',
            'fecha_nacimiento': date(1980, 12, 3),
            'genero': 'M',
            'telefono': '71234567',
            'direccion': 'Calle Sucre 456, Santa Cruz'
        }
    ]

    # Crear cada director
    for i, director_data in enumerate(directores_data, 1):
        email = director_data['email']

        # Verificar si ya existe
        if Usuario.objects.filter(email=email).exists():
            print(f"⚠️  Director {i} ya existe: {email}")
            continue

        try:
            # Crear usuario
            usuario = Usuario.objects.create_user(
                email=director_data['email'],
                password=director_data['password'],
                tipo_usuario='director'
            )

            # Crear perfil de director
            director = Director.objects.create(
                usuario=usuario,
                nombres=director_data['nombres'],
                apellidos=director_data['apellidos'],
                cedula_identidad=director_data['cedula_identidad'],
                fecha_nacimiento=director_data['fecha_nacimiento'],
                genero=director_data['genero'],
                telefono=director_data['telefono'],
                direccion=director_data['direccion']
            )

            print(f"✅ Director {i} creado exitosamente: {email}")

        except Exception as e:
            print(f"❌ Error creando Director {i}: {str(e)}")

    # Mostrar estadísticas finales
    print("\n" + "=" * 50)
    print("📊 ESTADÍSTICAS DEL SISTEMA:")
    print("=" * 50)
    print(f"Total usuarios: {Usuario.objects.count()}")
    print(f"Total directores: {Director.objects.count()}")
    print(f"Usuarios director: {Usuario.objects.filter(tipo_usuario='director').count()}")
    print(f"Usuarios activos: {Usuario.objects.filter(activo=True).count()}")

    # Mostrar credenciales
    print("\n" + "=" * 50)
    print("🔐 CREDENCIALES DE ACCESO:")
    print("=" * 50)
    print("Director 1:")
    print("  Email: director1@sistema.com")
    print("  Password: director123")
    print()
    print("Director 2:")
    print("  Email: director2@sistema.com")
    print("  Password: director456")
    print("=" * 50)


if __name__ == '__main__':
    create_directors()
