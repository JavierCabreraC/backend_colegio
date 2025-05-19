from rest_framework import status
from .serializers import LoginSerializer
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from audit.utils import registrar_accion_bitacora
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        # AGREGAR: Registrar login en bitácora
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
