import os
import sys
import django
from pathlib import Path
from create_directores import create_directors
from create_profesores import create_profesores


# Configuración
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

def main():
    print("🚀 Iniciando creación de datos de prueba...")
    print("=" * 60)

    # Ejecutar scripts
    create_directors()
    print("\n" + "-" * 40 + "\n")
    create_profesores()

    print("=" * 60)
    print("🎉 ¡Creación de datos completada!")

    # Estadísticas finales
    from authentication.models import Usuario, Director, Profesor
    print(f"\n📊 RESUMEN FINAL:")
    print(f"Total usuarios: {Usuario.objects.count()}")
    print(f"Directores: {Director.objects.count()}")
    print(f"Profesores: {Profesor.objects.count()}")


if __name__ == '__main__':
    main()
