import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from academic.models import Materia

def create_subjects():
    print("📚 Creando materias...")
    
    materias_data = [
        {
            'codigo': 'MAT001',
            'nombre': 'Matemáticas',
            'descripcion': 'Álgebra, geometría y cálculo',
            'horas_semanales': 6
        },
        {
            'codigo': 'LEN001',
            'nombre': 'Lengua y Literatura',
            'descripcion': 'Gramática, lectura y redacción',
            'horas_semanales': 5
        },
        {
            'codigo': 'ING001',
            'nombre': 'Inglés',
            'descripcion': 'Idioma extranjero',
            'horas_semanales': 4
        },
        {
            'codigo': 'FIS001',
            'nombre': 'Física',
            'descripcion': 'Mecánica, termodinámica, óptica',
            'horas_semanales': 4
        },
        {
            'codigo': 'QUI001',
            'nombre': 'Química',
            'descripcion': 'Química general y orgánica',
            'horas_semanales': 4
        },
        {
            'codigo': 'BIO001',
            'nombre': 'Biología',
            'descripcion': 'Biología general y ecología',
            'horas_semanales': 4
        },
        {
            'codigo': 'HIS001',
            'nombre': 'Historia',
            'descripcion': 'Historia universal y nacional',
            'horas_semanales': 3
        },
        {
            'codigo': 'GEO001',
            'nombre': 'Geografía',
            'descripcion': 'Geografía física y humana',
            'horas_semanales': 3
        },
        {
            'codigo': 'EDC001',
            'nombre': 'Educación Cívica',
            'descripcion': 'Formación ciudadana',
            'horas_semanales': 2
        },
        {
            'codigo': 'EDF001',
            'nombre': 'Educación Física',
            'descripcion': 'Deportes y actividad física',
            'horas_semanales': 3
        },
        {
            'codigo': 'ART001',
            'nombre': 'Educación Artística',
            'descripcion': 'Arte, música y expresión',
            'horas_semanales': 2
        },
        {
            'codigo': 'TEC001',
            'nombre': 'Tecnología',
            'descripcion': 'Informática y tecnología',
            'horas_semanales': 3
        }
    ]
    
    created_count = 0
    for materia_data in materias_data:
        materia, created = Materia.objects.get_or_create(
            codigo=materia_data['codigo'],
            defaults=materia_data
        )
        if created:
            print(f"✅ {materia_data['nombre']} ({materia_data['codigo']}) creada")
            created_count += 1
        else:
            print(f"⚠️ {materia_data['nombre']} ya existía")
    
    print(f"\n📊 Materias creadas: {created_count}")
    print(f"📊 Total materias: {Materia.objects.count()}")
    
    # Mostrar resumen de materias
    print("\n📚 Lista de materias:")
    for materia in Materia.objects.all().order_by('codigo'):
        print(f"   {materia.codigo}: {materia.nombre} ({materia.horas_semanales}h/semana)")

if __name__ == '__main__':
    create_subjects()