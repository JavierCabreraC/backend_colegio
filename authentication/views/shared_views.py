import logging
from ..models import Usuario
from datetime import timedelta
from django.db.models import Q
from rest_framework import status
from django.utils import timezone
from rest_framework.response import Response
from audit.utils import registrar_accion_bitacora
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers.shared_serializers import LoginSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Autenticación universal para todos los tipos de usuario"""
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
    """Cierra la sesión del usuario y registra en bitácora"""
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
    """Ver actividad de usuarios (solo directores)"""
    if request.user.tipo_usuario != 'director':
        return Response({'error': 'No autorizado'}, status=403)

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

