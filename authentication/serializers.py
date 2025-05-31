from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Usuario, Director, Profesor, Alumno
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['rol'] = self.user.tipo_usuario
        data['id'] = self.user.id
        return data

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Credenciales inválidas')
            if not user.activo:
                raise serializers.ValidationError('Usuario inactivo')

            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Email y contraseña son requeridos')

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer base para usuarios"""
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'tipo_usuario', 'activo',
            'is_staff', 'is_active', 'created_at', 'updated_at', 'password'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        # Extraer password si existe
        password = validated_data.pop('password', None)

        # Actualizar campos normales
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Actualizar password solo si se proporciona
        if password:
            instance.set_password(password)

        instance.save()
        return instance

    def validate_email(self, value):
        """Validar que el email sea único, excepto para el usuario actual"""
        if self.instance and self.instance.email == value:
            return value

        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está en uso.")
        return value

class ProfesorSerializer(serializers.ModelSerializer):
    """Serializer para CRUD de profesores"""
    usuario = UsuarioSerializer()
    nombre_completo = serializers.SerializerMethodField()
    edad = serializers.SerializerMethodField()

    class Meta:
        model = Profesor
        fields = [
            'usuario', 'nombre_completo', 'nombres', 'apellidos',
            'cedula_identidad', 'fecha_nacimiento', 'edad', 'genero',
            'telefono', 'direccion', 'especialidad', 'fecha_contratacion',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"

    def get_edad(self, obj):
        from datetime import date
        if obj.fecha_nacimiento:
            today = date.today()
            return today.year - obj.fecha_nacimiento.year - (
                    (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
            )
        return None

    def create(self, validated_data):
        usuario_data = validated_data.pop('usuario')
        usuario_data['tipo_usuario'] = 'profesor'

        # Crear usuario
        usuario = UsuarioSerializer().create(usuario_data)

        # Crear profesor
        profesor = Profesor.objects.create(usuario=usuario, **validated_data)
        return profesor

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', None)

        # Actualizar datos del profesor
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Actualizar usuario si hay datos
        if usuario_data:
            usuario_serializer = UsuarioSerializer(
                instance.usuario,
                data=usuario_data,
                partial=True
            )
            if usuario_serializer.is_valid():
                usuario_serializer.save()
            else:
                # IMPORTANTE: Propagar errores del usuario
                raise serializers.ValidationError({
                    'usuario': usuario_serializer.errors
                })

        return instance


class ProfesorListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de profesores"""
    email = serializers.CharField(source='usuario.email', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    activo = serializers.BooleanField(source='usuario.activo', read_only=True)

    class Meta:
        model = Profesor
        fields = [
            'usuario', 'email', 'nombre_completo', 'cedula_identidad',
            'telefono', 'especialidad', 'fecha_contratacion', 'activo'
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"

class AlumnoSerializer(serializers.ModelSerializer):
    """Serializer para CRUD de alumnos"""
    usuario = UsuarioSerializer()
    nombre_completo = serializers.SerializerMethodField()
    edad = serializers.SerializerMethodField()
    grupo_nombre = serializers.CharField(source='grupo.nivel.nombre', read_only=True)
    grupo_letra = serializers.CharField(source='grupo.letra', read_only=True)

    class Meta:
        model = Alumno
        fields = [
            'usuario', 'grupo', 'grupo_nombre', 'grupo_letra', 'matricula',
            'nombre_completo', 'nombres', 'apellidos', 'fecha_nacimiento',
            'edad', 'genero', 'telefono', 'direccion',
            'nombre_tutor', 'telefono_tutor', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"

    def get_edad(self, obj):
        from datetime import date
        if obj.fecha_nacimiento:
            today = date.today()
            return today.year - obj.fecha_nacimiento.year - (
                    (today.month, today.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day)
            )
        return None

    def create(self, validated_data):
        usuario_data = validated_data.pop('usuario')
        usuario_data['tipo_usuario'] = 'alumno'

        # Crear usuario
        usuario = UsuarioSerializer().create(usuario_data)

        # Crear alumno
        alumno = Alumno.objects.create(usuario=usuario, **validated_data)
        return alumno

    def update(self, instance, validated_data):
        usuario_data = validated_data.pop('usuario', None)

        # Actualizar datos del alumno
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Actualizar usuario si hay datos
        if usuario_data:
            usuario_serializer = UsuarioSerializer(instance.usuario, data=usuario_data, partial=True)
            if usuario_serializer.is_valid():
                usuario_serializer.save()

        return instance

class AlumnoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de alumnos"""
    email = serializers.CharField(source='usuario.email', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    grupo_completo = serializers.SerializerMethodField()
    activo = serializers.BooleanField(source='usuario.activo', read_only=True)

    class Meta:
        model = Alumno
        fields = [
            'usuario', 'email', 'nombre_completo', 'matricula',
            'grupo', 'grupo_completo', 'telefono', 'activo'
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"

    def get_grupo_completo(self, obj):
        if obj.grupo:
            return f"{obj.grupo.nivel.numero}° {obj.grupo.letra}"
        return None

class DirectorSerializer(serializers.ModelSerializer):
    """Serializer para directores (para completitud)"""
    usuario = UsuarioSerializer()
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Director
        fields = [
            'usuario', 'nombre_completo', 'nombres', 'apellidos',
            'cedula_identidad', 'fecha_nacimiento', 'genero',
            'telefono', 'direccion', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_nombre_completo(self, obj):
        return f"{obj.nombres} {obj.apellidos}"
