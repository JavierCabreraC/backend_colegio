import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

from authentication.models import Usuario, Profesor
from academic.models import ProfesorMateria


def clean_professors():
    print("🧹 Limpiando profesores existentes...")

    # Eliminar todas las asignaciones profesor-materia
    count_pm = ProfesorMateria.objects.count()
    ProfesorMateria.objects.all().delete()
    print(f"✅ {count_pm} asignaciones profesor-materia eliminadas")

    # Eliminar todos los profesores
    count_prof = Profesor.objects.count()
    Profesor.objects.all().delete()
    print(f"✅ {count_prof} profesores eliminados")

    # Eliminar usuarios de tipo profesor
    count_users = Usuario.objects.filter(tipo_usuario='profesor').count()
    Usuario.objects.filter(tipo_usuario='profesor').delete()
    print(f"✅ {count_users} usuarios profesor eliminados")

    print("\n📊 Estado final:")
    print(f"👨‍🏫 Profesores: {Profesor.objects.count()}")
    print(f"📚 Asignaciones: {ProfesorMateria.objects.count()}")
    print(f"👥 Usuarios profesor: {Usuario.objects.filter(tipo_usuario='profesor').count()}")
    print("\n✅ Base de datos limpia. Ya puedes ejecutar 3_create_professors.py")


if __name__ == '__main__':
    clean_professors()