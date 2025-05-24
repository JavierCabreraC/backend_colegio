import json
import logging
from django.db.models import Q
from datetime import timedelta
from rest_framework import status
from django.utils import timezone
from shared.permissions import IsDirector
from django.core.paginator import Paginator
from rest_framework.response import Response
from .models import Usuario, Profesor, Alumno
from audit.utils import registrar_accion_bitacora
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .serializers import (
    LoginSerializer, ProfesorSerializer, ProfesorListSerializer,
    AlumnoSerializer, AlumnoListSerializer
)


logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        registrar_accion_bitacora(user, 'LOGIN', request)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'rol': user.tipo_usuario,
            'id': user.id
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_view(request):
    """
    Cierra la sesión del usuario y registra en bitácora
    """
    try:
        # Verificar autenticación
        jwt_auth = JWTAuthentication()
        user, token = jwt_auth.authenticate(request)

        if user is None:
            return Response(
                {'error': 'Token inválido o usuario no autenticado'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Obtener refresh token del body
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Invalidar refresh token (blacklist)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            pass  # Token ya inválido o no existe

        # Registrar logout en bitácora
        registrar_accion_bitacora(user, 'LOGOUT', request)

        return Response(
            {'message': 'Logout exitoso'},
            status=status.HTTP_200_OK
        )

    except InvalidToken:
        return Response(
            {'error': 'Token inválido'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return Response(
            {'error': f'Error en logout: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activity(request):
    """
    Ver actividad de usuarios (solo directores)
    """
    if request.user.tipo_usuario != 'director':
        return Response({'error': 'No autorizado'}, status=403)

    # from django.db.models import Q
    # from datetime import timedelta

    # Usuarios activos en los últimos 30 días
    fecha_limite = timezone.now() - timedelta(days=30)
    usuarios_activos = Usuario.objects.filter(
        last_login__gte=fecha_limite
    ).order_by('-last_login')

    # Usuarios que nunca se han logueado
    usuarios_sin_login = Usuario.objects.filter(
        Q(last_login__isnull=True)
    )

    data = {
        'usuarios_activos_30_dias': [
            {
                'email': user.email,
                'tipo': user.tipo_usuario,
                'last_login': user.last_login,
                'dias_desde_login': (timezone.now() - user.last_login).days if user.last_login else None
            }
            for user in usuarios_activos
        ],
        'usuarios_sin_login': [
            {
                'email': user.email,
                'tipo': user.tipo_usuario,
                'created_at': user.created_at
            }
            for user in usuarios_sin_login
        ],
        'total_usuarios': Usuario.objects.count(),
        'usuarios_activos': usuarios_activos.count(),
        'usuarios_inactivos': usuarios_sin_login.count()
    }

    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def profesor_list_create(request):
    """
    GET: Listar profesores con paginación y filtros
    POST: Crear nuevo profesor
    """

    if request.method == 'POST':
        print(f"\n{'=' * 50}")
        print(f"🔍 PAYLOAD RECIBIDO - Método: {request.method}")
        print(f"📍 Endpoint: {request.path}")
        print(f"📦 Data recibida:")
        print(json.dumps(request.data, indent=2, ensure_ascii=False, default=str))
        print(f"{'=' * 50}\n")

    if request.method == 'GET':
        # Parámetros de consulta
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        search = request.GET.get('search', '')
        especialidad = request.GET.get('especialidad', '')
        activo = request.GET.get('activo', '')

        # Filtrar profesores
        queryset = Profesor.objects.all().select_related('usuario').order_by('-created_at')

        if search:
            queryset = queryset.filter(
                Q(nombres__icontains=search) |
                Q(apellidos__icontains=search) |
                Q(usuario__email__icontains=search) |
                Q(cedula_identidad__icontains=search)
            )

        if especialidad:
            queryset = queryset.filter(especialidad__icontains=especialidad)

        if activo:
            activo_bool = activo.lower() == 'true'
            queryset = queryset.filter(usuario__activo=activo_bool)

        # Paginar
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        registrar_accion_bitacora(
            request.user,
            f'LISTAR_PROFESORES',
            request
        )

        # Serializar
        serializer = ProfesorListSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = ProfesorSerializer(data=request.data)
        if serializer.is_valid():
            print(f"✅ Datos validados correctamente para creación")
            try:
                profesor = serializer.save()
                print(f"✅ Profesor creado exitosamente: {profesor.nombres} {profesor.apellidos}")

                # Registrar en bitácora
                registrar_accion_bitacora(
                    request.user,
                    f'CREAR_PROFESOR',
                    request
                )

                return Response(
                    ProfesorSerializer(profesor).data,
                    status=status.HTTP_201_CREATED
                )

            except Exception as e:
                print(f"❌ Error al crear profesor: {str(e)}")
                return Response(
                    {'error': f'Error al crear: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        else:
            print(f"❌ Errores de validación en creación:")
            print(json.dumps(serializer.errors, indent=2, ensure_ascii=False))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def profesor_detail(request, pk):
    """
    GET: Ver detalle de profesor
    PUT: Actualizar profesor completo
    PATCH: Actualizar profesor parcial
    DELETE: Eliminar profesor
    """
    if request.method in ['PUT', 'PATCH', 'POST']:
        print(f"\n{'=' * 50}")
        print(f"🔍 PAYLOAD RECIBIDO - Método: {request.method}")
        print(f"📍 Endpoint: {request.path}")
        print(f"📋 Content-Type: {request.content_type}")
        print(f"📦 Data recibida:")
        print(json.dumps(request.data, indent=2, ensure_ascii=False, default=str))
        print(f"{'=' * 50}\n")

    try:
        profesor = Profesor.objects.select_related('usuario').get(pk=pk)
    except Profesor.DoesNotExist:
        return Response(
            {'error': 'Profesor no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = ProfesorSerializer(profesor)
        return Response(serializer.data)


    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ProfesorSerializer(profesor, data=request.data, partial=partial)

        if serializer.is_valid():
            print(f"✅ Datos validados correctamente")
            try:
                profesor_updated = serializer.save()
                print(f"✅ Profesor actualizado exitosamente")

                # Registrar en bitácora
                registrar_accion_bitacora(
                    request.user,
                    f'ACTUALIZAR_PROFESOR: {profesor_updated.nombres} {profesor_updated.apellidos}',
                    request
                )

                return Response(ProfesorSerializer(profesor_updated).data)

            except Exception as e:
                print(f"❌ Error al guardar: {str(e)}")
                return Response(
                    {'error': f'Error al guardar: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR

                )

        else:
            print(f"❌ Errores de validación:")
            print(json.dumps(serializer.errors, indent=2, ensure_ascii=False))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        nombre_completo = f"{profesor.nombres} {profesor.apellidos}"
        email = profesor.usuario.email

        # Eliminar profesor (cascade eliminará usuario)
        profesor.delete()

        # Registrar en bitácora
        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_PROFESOR',
            request
        )

        return Response(
            {'message': 'Profesor eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )


# Vistas CRUD para Alumnos
@api_view(['GET', 'POST'])
@permission_classes([IsDirector])
def alumno_list_create(request):
    """
    GET: Listar alumnos con paginación y filtros
    POST: Crear nuevo alumno
    """
    if request.method == 'GET':
        # Parámetros de consulta
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 20)
        search = request.GET.get('search', '')
        grupo = request.GET.get('grupo', '')
        nivel = request.GET.get('nivel', '')
        activo = request.GET.get('activo', '')

        # Filtrar alumnos
        queryset = Alumno.objects.all().select_related(
            'usuario', 'grupo', 'grupo__nivel'
        ).order_by('-created_at')

        if search:
            queryset = queryset.filter(
                Q(nombres__icontains=search) |
                Q(apellidos__icontains=search) |
                Q(usuario__email__icontains=search) |
                Q(matricula__icontains=search)
            )

        if grupo:
            queryset = queryset.filter(grupo_id=grupo)

        if nivel:
            queryset = queryset.filter(grupo__nivel__numero=nivel)

        if activo:
            activo_bool = activo.lower() == 'true'
            queryset = queryset.filter(usuario__activo=activo_bool)

        # Paginar
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Serializar
        serializer = AlumnoListSerializer(page_obj.object_list, many=True)

        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'next': page_obj.has_next(),
            'previous': page_obj.has_previous(),
            'results': serializer.data
        })

    elif request.method == 'POST':
        serializer = AlumnoSerializer(data=request.data)
        if serializer.is_valid():
            alumno = serializer.save()

            # Registrar en bitácora
            registrar_accion_bitacora(
                request.user,
                f'CREAR_ALUMNO: {alumno.matricula}',
                request
            )

            return Response(
                AlumnoSerializer(alumno).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsDirector])
def alumno_detail(request, pk):
    """
    GET: Ver detalle de alumno
    PUT: Actualizar alumno completo
    PATCH: Actualizar alumno parcial
    DELETE: Eliminar alumno
    """
    try:
        alumno = Alumno.objects.select_related(
            'usuario', 'grupo', 'grupo__nivel'
        ).get(pk=pk)
    except Alumno.DoesNotExist:
        return Response(
            {'error': 'Alumno no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = AlumnoSerializer(alumno)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = AlumnoSerializer(alumno, data=request.data, partial=partial)

        if serializer.is_valid():
            alumno_updated = serializer.save()

            # Registrar en bitácora
            registrar_accion_bitacora(
                request.user,
                f'ACTUALIZAR_ALUMNO',
                request
            )

            return Response(AlumnoSerializer(alumno_updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        nombre_completo = f"{alumno.nombres} {alumno.apellidos}"
        matricula = alumno.matricula
        email = alumno.usuario.email

        # Eliminar alumno (cascade eliminará usuario)
        alumno.delete()

        # Registrar en bitácora
        registrar_accion_bitacora(
            request.user,
            f'ELIMINAR_ALUMNO: {matricula}',
            request
        )

        return Response(
            {'message': 'Alumno eliminado exitosamente'},
            status=status.HTTP_204_NO_CONTENT
        )


# Vista de estadísticas básicas
@api_view(['GET'])
@permission_classes([IsDirector])
def dashboard_director(request):
    """Dashboard básico para directores"""
    from academic.models import Materia, Aula

    stats = {
        'total_profesores': Profesor.objects.count(),
        'profesores_activos': Profesor.objects.filter(usuario__activo=True).count(),
        'total_alumnos': Alumno.objects.count(),
        'alumnos_activos': Alumno.objects.filter(usuario__activo=True).count(),
        'total_materias': Materia.objects.count(),
        'total_aulas': Aula.objects.count(),
        'usuarios_total': Usuario.objects.count(),
        'usuarios_activos': Usuario.objects.filter(activo=True).count(),
    }

    # Últimos profesores registrados
    ultimos_profesores = Profesor.objects.select_related('usuario').order_by('-created_at')[:5]
    ultimos_alumnos = Alumno.objects.select_related('usuario').order_by('-created_at')[:5]

    return Response({
        'estadisticas': stats,
        'ultimos_profesores': ProfesorListSerializer(ultimos_profesores, many=True).data,
        'ultimos_alumnos': AlumnoListSerializer(ultimos_alumnos, many=True).data,
    })
