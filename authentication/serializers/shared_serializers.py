from ..models import Usuario
from rest_framework import serializers
from django.contrib.auth import authenticate
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
