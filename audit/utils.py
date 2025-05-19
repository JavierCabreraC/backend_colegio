from .models import Bitacora


def registrar_accion_bitacora(usuario, tipo_accion, request):
    """
    Registra una acción en la bitácora

    Args:
        usuario: Instancia del modelo Usuario
        tipo_accion: String describiendo la acción (ej: 'LOGIN', 'LOGOUT')
        request: Request object de Django para obtener IP
    """
    # Obtener IP del cliente
    ip = get_client_ip(request)

    # Crear registro en bitácora
    Bitacora.objects.create(
        usuario=usuario,
        tipo_accion=tipo_accion,
        ip=ip
    )


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or 'Unknown'
