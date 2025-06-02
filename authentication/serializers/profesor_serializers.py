from datetime import date
from rest_framework import serializers
from academic.models import ( Trimestre, Gestion,  ProfesorMateria, Horario )


class DashboardProfesorSerializer(serializers.Serializer):
    """Serializer para dashboard del profesor"""
    profesor_info = serializers.SerializerMethodField()
    materias_asignadas = serializers.SerializerMethodField()
    grupos_asignados = serializers.SerializerMethodField()
    horarios_hoy = serializers.SerializerMethodField()
    estadisticas = serializers.SerializerMethodField()
    gestion_activa = serializers.SerializerMethodField()
    trimestre_actual = serializers.SerializerMethodField()

    def get_profesor_info(self, obj):
        """Información básica del profesor"""
        return {
            'id': obj.usuario.id,
            'nombre_completo': f"{obj.nombres} {obj.apellidos}",
            'email': obj.usuario.email,
            'especialidad': obj.especialidad,
            'fecha_contratacion': obj.fecha_contratacion
        }

    def get_materias_asignadas(self, obj):
        """Materias que imparte el profesor"""
        materias = ProfesorMateria.objects.filter(
            profesor=obj
        ).select_related('materia')

        return [
            {
                'id': pm.materia.id,
                'codigo': pm.materia.codigo,
                'nombre': pm.materia.nombre,
                'horas_semanales': pm.materia.horas_semanales
            }
            for pm in materias
        ]

    def get_grupos_asignados(self, obj):
        """Grupos que atiende el profesor"""
        grupos = Horario.objects.filter(
            profesor_materia__profesor=obj
        ).values(
            'grupo__id', 'grupo__nivel__numero', 'grupo__letra'
        ).distinct()

        return [
            {
                'id': grupo['grupo__id'],
                'nombre': f"{grupo['grupo__nivel__numero']}° {grupo['grupo__letra']}"
            }
            for grupo in grupos
        ]

    def get_horarios_hoy(self, obj):
        """Clases de hoy del profesor"""
        hoy = date.today()
        dia_semana = hoy.weekday() + 1  # Django usa 1=Lunes

        if dia_semana > 5:  # Fin de semana
            return []

        horarios = Horario.objects.filter(
            profesor_materia__profesor=obj,
            dia_semana=dia_semana
        ).select_related(
            'profesor_materia__materia',
            'grupo', 'grupo__nivel',
            'aula'
        ).order_by('hora_inicio')

        return [
            {
                'id': h.id,
                'materia': h.profesor_materia.materia.nombre,
                'grupo': f"{h.grupo.nivel.numero}° {h.grupo.letra}",
                'aula': h.aula.nombre,
                'hora_inicio': h.hora_inicio,
                'hora_fin': h.hora_fin
            }
            for h in horarios
        ]

    def get_estadisticas(self, obj):
        """Estadísticas básicas del profesor"""
        total_materias = ProfesorMateria.objects.filter(profesor=obj).count()
        total_horarios = Horario.objects.filter(profesor_materia__profesor=obj).count()

        # Contar alumnos únicos en sus clases
        alumnos_ids = Horario.objects.filter(
            profesor_materia__profesor=obj
        ).values_list('grupo__alumno', flat=True).distinct()
        total_alumnos = len([aid for aid in alumnos_ids if aid])

        return {
            'total_materias': total_materias,
            'total_horarios_semanales': total_horarios,
            'total_alumnos': total_alumnos,
            'total_grupos': len(self.get_grupos_asignados(obj))
        }

    def get_gestion_activa(self, obj):
        """Gestión académica activa"""
        gestion = Gestion.objects.filter(activa=True).first()
        if gestion:
            return {
                'id': gestion.id,
                'anio': gestion.anio,
                'nombre': gestion.nombre
            }
        return None

    def get_trimestre_actual(self, obj):
        """Trimestre actual basado en fechas"""
        gestion = Gestion.objects.filter(activa=True).first()
        if not gestion:
            return None

        hoy = date.today()
        trimestre = Trimestre.objects.filter(
            gestion=gestion,
            fecha_inicio__lte=hoy,
            fecha_fin__gte=hoy
        ).first()

        if trimestre:
            return {
                'id': trimestre.id,
                'numero': trimestre.numero,
                'nombre': trimestre.nombre,
                'fecha_inicio': trimestre.fecha_inicio,
                'fecha_fin': trimestre.fecha_fin
            }
        return None

    class Meta:
        fields = [
            'profesor_info', 'materias_asignadas', 'grupos_asignados',
            'horarios_hoy', 'estadisticas', 'gestion_activa', 'trimestre_actual'
        ]
