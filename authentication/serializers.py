from .models import Usuario
from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar información adicional al token
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
