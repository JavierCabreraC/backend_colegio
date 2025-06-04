import os
import django
import subprocess
import sys
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_colegio.settings')
django.setup()

def run_script(script_name):
    """Ejecuta un script y maneja errores"""
    print(f"\n{'='*60}")
    print(f"🚀 EJECUTANDO: {script_name}")
    print(f"{'='*60}")
    
    try:
        start_time = datetime.now()
        
        # Ejecutar el script
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Mostrar output
        if result.stdout:
            print(result.stdout)
        
        print(f"✅ {script_name} completado exitosamente en {duration:.2f} segundos")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando {script_name}:")
        print(f"Código de salida: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"❌ Error inesperado en {script_name}: {str(e)}")
        return False

def main():
    """Ejecuta todos los scripts en orden"""
    print("🎓 INICIANDO CREACIÓN DEL AÑO ACADÉMICO 2023")
    print("=" * 60)
    
    # Lista de scripts en orden de ejecución
    scripts = [
        "1_setup_academic_year_2023.py",
        "2_create_subjects.py", 
        "3_create_professors.py",
        "4_create_schedules.py",
        "5_create_students.py",
        "6_create_evaluations.py",
        "7_create_attendance.py",
        "8_create_participations.py"
    ]
    
    start_total = datetime.now()
    successful_scripts = 0
    
    for script in scripts:
        if os.path.exists(script):
            success = run_script(script)
            if success:
                successful_scripts += 1
            else:
                print(f"\n⚠️ Deteniendo ejecución debido a error en {script}")
                break
        else:
            print(f"❌ Script no encontrado: {script}")
            break
    
    end_total = datetime.now()
    total_duration = (end_total - start_total).total_seconds()
    
    # Resumen final
    print(f"\n{'='*60}")
    print(f"📊 RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"✅ Scripts ejecutados exitosamente: {successful_scripts}/{len(scripts)}")
    print(f"⏱️ Tiempo total de ejecución: {total_duration:.2f} segundos")
    
    if successful_scripts == len(scripts):
        print(f"🎉 ¡AÑO ACADÉMICO 2023 CREADO EXITOSAMENTE!")
        
        # Mostrar estadísticas finales
        show_final_statistics()
    else:
        print(f"⚠️ Proceso incompleto. Revisar errores anteriores.")

def show_final_statistics():
    """Muestra estadísticas finales de la base de datos"""
    from authentication.models import Usuario, Director, Profesor, Alumno
    from academic.models import Gestion, Trimestre, Nivel, Grupo, Aula, Materia, ProfesorMateria, Horario, Matriculacion
    from evaluations.models import Examen, Tarea, NotaExamen, NotaTarea, Asistencia, Participacion
    
    print(f"\n📈 ESTADÍSTICAS FINALES DE LA BASE DE DATOS:")
    print(f"👥 Usuarios: {Usuario.objects.count()}")
    print(f"🏢 Directores: {Director.objects.count()}")
    print(f"👨‍🏫 Profesores: {Profesor.objects.count()}")
    print(f"👨‍🎓 Estudiantes: {Alumno.objects.count()}")
    print(f"📅 Gestiones: {Gestion.objects.count()}")
    print(f"📆 Trimestres: {Trimestre.objects.count()}")
    print(f"📚 Materias: {Materia.objects.count()}")
    print(f"🏫 Aulas: {Aula.objects.count()}")
    print(f"📋 Grupos: {Grupo.objects.count()}")
    print(f"⏰ Horarios: {Horario.objects.count()}")
    print(f"📝 Exámenes: {Examen.objects.count()}")
    print(f"📄 Tareas: {Tarea.objects.count()}")
    print(f"📊 Notas de exámenes: {NotaExamen.objects.count()}")
    print(f"📊 Notas de tareas: {NotaTarea.objects.count()}")
    print(f"✅ Registros de asistencia: {Asistencia.objects.count()}")
    print(f"🙋 Participaciones: {Participacion.objects.count()}")
    print(f"🎓 Matriculaciones 2023: {Matriculacion.objects.filter(gestion__anio=2023).count()}")

if __name__ == '__main__':
    main()