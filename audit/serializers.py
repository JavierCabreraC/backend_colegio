from .models import Bitacora
from rest_framework import serializers

class BitacoraSerializer(serializers.ModelSerializer):
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Bitacora
        fields = [
            'id', 'usuario', 'usuario_email', 'usuario_nombre',
            'tipo_accion', 'ip', 'fecha_hora', 'created_at'
        ]
        read_only_fields = ['id', 'fecha_hora', 'created_at']

    def get_usuario_nombre(self, obj):
        """Obtener nombre completo del usuario según su tipo"""
        try:
            if obj.usuario.tipo_usuario == 'director':
                director = obj.usuario.director
                return f"{director.nombres} {director.apellidos}"
            elif obj.usuario.tipo_usuario == 'profesor':
                profesor = obj.usuario.profesor
                return f"{profesor.nombres} {profesor.apellidos}"
            elif obj.usuario.tipo_usuario == 'alumno':
                alumno = obj.usuario.alumno
                return f"{alumno.nombres} {alumno.apellidos}"
        except:
            pass
        return obj.usuario.email
