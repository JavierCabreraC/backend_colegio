# authentication/models.py
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin



# Enum para tipos de usuario
class TipoUsuario(models.TextChoices):
    DIRECTOR = 'director', 'Director'
    PROFESOR = 'profesor', 'Profesor' 
    ALUMNO = 'alumno', 'Alumno'


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('tipo_usuario', TipoUsuario.DIRECTOR)
        return self.create_user(email, password, **extra_fields)

# Usuario mantiene herencia de BaseEntity

class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    email = models.EmailField(unique=True)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices
    )
    activo = models.BooleanField(default=True)
    
    # Campos requeridos por Django
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['tipo_usuario']
    
    class Meta:
        db_table = 'usuarios'

# Los perfiles NO heredan de BaseEntity

class Director(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula_identidad = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=60, blank=True)
    
    class Meta:
        db_table = 'directores'


class Profesor(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cedula_identidad = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=60, blank=True)
    especialidad = models.CharField(max_length=20, blank=True)
    fecha_contratacion = models.DateField()
    
    class Meta:
        db_table = 'profesores'


class Alumno(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        primary_key=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    matricula = models.CharField(max_length=12, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    genero = models.CharField(max_length=1)
    telefono = models.CharField(max_length=10, blank=True)
    direccion = models.CharField(max_length=60, blank=True)
    nombre_tutor = models.CharField(max_length=50, blank=True)
    telefono_tutor = models.CharField(max_length=10, blank=True)
    grupo = models.ForeignKey('academic.Grupo', on_delete=models.PROTECT)
    
    class Meta:
        db_table = 'alumnos'
