import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Usuario, Profesor
from academic.models import Materia, ProfesorMateria
from datetime import date


def create_professors():
    print("👨‍🏫 Creando profesores...")

    # Datos de los 12 profesores (uno por materia)
    profesores_data = [
        {
            'email': 'prof.matematicas@colegio.com',
            'password': 'prof123',
            'nombres': 'Roberto Carlos',
            'apellidos': 'Morales Vega',
            'cedula_identidad': 'CI001001',
            'fecha_nacimiento': date(1985, 3, 15),
            'genero': 'M',
            'telefono': '72345001',
            'direccion': 'Av. Brasil 100',
            'especialidad': 'Matemáticas',
            'fecha_contratacion': date(2020, 1, 15),
            'materia_codigo': 'MAT001'
        },
        {
            'email': 'prof.lengua@colegio.com',
            'password': 'prof123',
            'nombres': 'María Elena',
            'apellidos': 'Fernández Castro',
            'cedula_identidad': 'CI001002',
            'fecha_nacimiento': date(1982, 7, 22),
            'genero': 'F',
            'telefono': '72345002',
            'direccion': 'Calle Murillo 250',
            'especialidad': 'Literatura',
            'fecha_contratacion': date(2019, 3, 1),
            'materia_codigo': 'LEN001'
        },
        {
            'email': 'prof.ingles@colegio.com',
            'password': 'prof123',
            'nombres': 'James Michael',
            'apellidos': 'Thompson Silva',
            'cedula_identidad': 'CI001003',
            'fecha_nacimiento': date(1988, 11, 8),
            'genero': 'M',
            'telefono': '72345003',
            'direccion': 'Barrio Norte 305',
            'especialidad': 'Inglés',
            'fecha_contratacion': date(2021, 8, 10),
            'materia_codigo': 'ING001'
        },
        {
            'email': 'prof.fisica@colegio.com',
            'password': 'prof123',
            'nombres': 'Carlos Alberto',
            'apellidos': 'Mendoza Ruiz',
            'cedula_identidad': 'CI001004',
            'fecha_nacimiento': date(1980, 4, 12),
            'genero': 'M',
            'telefono': '72345004',
            'direccion': 'Av. Grigotá 410',
            'especialidad': 'Física',
            'fecha_contratacion': date(2018, 2, 5),
            'materia_codigo': 'FIS001'
        },
        {
            'email': 'prof.quimica@colegio.com',
            'password': 'prof123',
            'nombres': 'Ana Patricia',
            'apellidos': 'López Herrera',
            'cedula_identidad': 'CI001005',
            'fecha_nacimiento': date(1984, 9, 25),
            'genero': 'F',
            'telefono': '72345005',
            'direccion': 'Calle Libertad 515',
            'especialidad': 'Química',
            'fecha_contratacion': date(2020, 7, 20),
            'materia_codigo': 'QUI001'
        },
        {
            'email': 'prof.biologia@colegio.com',
            'password': 'prof123',
            'nombres': 'Luis Fernando',
            'apellidos': 'García Torrez',
            'cedula_identidad': 'CI001006',
            'fecha_nacimiento': date(1986, 1, 30),
            'genero': 'M',
            'telefono': '72345006',
            'direccion': 'Barrio San Juan 620',
            'especialidad': 'Biología',
            'fecha_contratacion': date(2019, 9, 12),
            'materia_codigo': 'BIO001'
        },
        {
            'email': 'prof.historia@colegio.com',
            'password': 'prof123',
            'nombres': 'Carmen Rosa',
            'apellidos': 'Vargas Peña',
            'cedula_identidad': 'CI001007',
            'fecha_nacimiento': date(1981, 6, 18),
            'genero': 'F',
            'telefono': '72345007',
            'direccion': 'Av. Banzer 725',
            'especialidad': 'Historia',
            'fecha_contratacion': date(2017, 11, 8),
            'materia_codigo': 'HIS001'
        },
        {
            'email': 'prof.geografia@colegio.com',
            'password': 'prof123',
            'nombres': 'Pedro Ramón',
            'apellidos': 'Chávez Moreno',
            'cedula_identidad': 'CI001008',
            'fecha_nacimiento': date(1983, 12, 5),
            'genero': 'M',
            'telefono': '72345008',
            'direccion': 'Calle Cochabamba 830',
            'especialidad': 'Geografía',
            'fecha_contratacion': date(2020, 4, 15),
            'materia_codigo': 'GEO001'
        },
        {
            'email': 'prof.civica@colegio.com',
            'password': 'prof123',
            'nombres': 'Isabel Cristina',
            'apellidos': 'Rojas Sánchez',
            'cedula_identidad': 'CI001009',
            'fecha_nacimiento': date(1987, 2, 14),
            'genero': 'F',
            'telefono': '72345009',
            'direccion': 'Barrio Equipetrol 935',
            'especialidad': 'Ciencias Sociales',
            'fecha_contratacion': date(2021, 1, 25),
            'materia_codigo': 'EDC001'
        },
        {
            'email': 'prof.educacionfisica@colegio.com',
            'password': 'prof123',
            'nombres': 'Marco Antonio',
            'apellidos': 'Durán Flores',
            'cedula_identidad': 'CI001010',
            'fecha_nacimiento': date(1989, 8, 7),
            'genero': 'M',
            'telefono': '72345010',
            'direccion': 'Av. Santos Dumont 1040',
            'especialidad': 'Educación Física',
            'fecha_contratacion': date(2022, 3, 10),
            'materia_codigo': 'EDF001'
        },
        {
            'email': 'prof.arte@colegio.com',
            'password': 'prof123',
            'nombres': 'Lucía Esperanza',
            'apellidos': 'Romero Aguilar',
            'cedula_identidad': 'CI001011',
            'fecha_nacimiento': date(1985, 10, 20),
            'genero': 'F',
            'telefono': '72345011',
            'direccion': 'Calle Warnes 1145',
            'especialidad': 'Artes Plásticas',
            'fecha_contratacion': date(2020, 8, 5),
            'materia_codigo': 'ART001'
        },
        {
            'email': 'prof.tecnologia@colegio.com',
            'password': 'prof123',
            'nombres': 'Diego Alejandro',
            'apellidos': 'Quiroga Medina',
            'cedula_identidad': 'CI001012',
            'fecha_nacimiento': date(1990, 5, 3),
            'genero': 'M',
            'telefono': '72345012',
            'direccion': 'Barrio Las Palmas 1250',
            'especialidad': 'Informática',
            'fecha_contratacion': date(2021, 6, 18),
            'materia_codigo': 'TEC001'
        }
    ]

    created_count = 0
    for prof_data in profesores_data:
        # Crear usuario
        if not Usuario.objects.filter(email=prof_data['email']).exists():
            usuario = Usuario.objects.create_user(
                email=prof_data['email'],
                password=prof_data['password'],
                tipo_usuario='profesor'
            )

            # Crear profesor
            profesor = Profesor.objects.create(
                usuario=usuario,
                nombres=prof_data['nombres'],
                apellidos=prof_data['apellidos'],
                cedula_identidad=prof_data['cedula_identidad'],
                fecha_nacimiento=prof_data['fecha_nacimiento'],
                genero=prof_data['genero'],
                telefono=prof_data['telefono'],
                direccion=prof_data['direccion'],
                especialidad=prof_data['especialidad'],
                fecha_contratacion=prof_data['fecha_contratacion']
            )

            # Asignar materia al profesor
            materia = Materia.objects.get(codigo=prof_data['materia_codigo'])
            ProfesorMateria.objects.create(
                profesor=profesor,
                materia=materia
            )

            print(f"✅ {prof_data['nombres']} {prof_data['apellidos']} creado/a - {materia.nombre}")
            created_count += 1
        else:
            print(f"⚠️ {prof_data['email']} ya existía")

    print(f"\n📊 Profesores creados: {created_count}")
    print(f"📊 Total profesores: {Profesor.objects.count()}")
    print(f"📊 Asignaciones profesor-materia: {ProfesorMateria.objects.count()}")

    # Mostrar credenciales
    print("\n🔐 Credenciales de profesores:")
    for profesor in Profesor.objects.all().order_by('nombres'):
        # Obtener todas las materias del profesor (podría tener múltiples)
        materias = ProfesorMateria.objects.filter(profesor=profesor)
        materias_nombres = [pm.materia.nombre for pm in materias]
        materias_str = ", ".join(materias_nombres)
        print(f"   {profesor.usuario.email} / prof123 - {materias_str}")


if __name__ == '__main__':
    create_professors()