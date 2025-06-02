import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Usuario, Director
from datetime import date


def create_directors():
    print("🏫 Creando directores de prueba...")

    # DIRECTOR 1
    if not Usuario.objects.filter(email='director1@sistema.com').exists():
        usuario1 = Usuario.objects.create_user(
            email='director1@sistema.com',
            password='director123',
            tipo_usuario='director'
        )

        Director.objects.create(
            usuario=usuario1,
            nombres='Ana María',
            apellidos='Gutiérrez López',
            cedula_identidad='12345678',
            fecha_nacimiento=date(1975, 8, 15),
            genero='F',
            telefono='70123456',
            direccion='Av. Central 123, Santa Cruz'
        )
        print("✅ Director 1 creado: director1@sistema.com")

    # DIRECTOR 2
    if not Usuario.objects.filter(email='director2@sistema.com').exists():
        usuario2 = Usuario.objects.create_user(
            email='director2@sistema.com',
            password='director456',
            tipo_usuario='director'
        )

        Director.objects.create(
            usuario=usuario2,
            nombres='Carlos Eduardo',
            apellidos='Pérez Mendoza',
            cedula_identidad='87654321',
            fecha_nacimiento=date(1980, 12, 3),
            genero='M',
            telefono='71234567',
            direccion='Calle Sucre 456, Santa Cruz'
        )
        print("✅ Director 2 creado: director2@sistema.com")

    print(f"\n📊 Total usuarios: {Usuario.objects.count()}")
    print(f"📊 Total directores: {Director.objects.count()}")
    print("\n🔐 Credenciales:")
    print("Director 1: director1@sistema.com / director123")
    print("Director 2: director2@sistema.com / director456")


if __name__ == '__main__':
    create_directors()
