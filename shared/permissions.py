from rest_framework.permissions import BasePermission


class IsDirector(BasePermission):
    """
    Permiso personalizado para permitir acceso solo a directores
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'tipo_usuario') and
            request.user.tipo_usuario == 'director'
        )


class IsProfesor(BasePermission):
    """
    Permiso personalizado para permitir acceso solo a profesores
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'tipo_usuario') and
            request.user.tipo_usuario == 'profesor'
        )


class IsAlumno(BasePermission):
    """
    Permiso personalizado para permitir acceso solo a alumnos
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'tipo_usuario') and
            request.user.tipo_usuario == 'alumno'
        )


class IsDirectorOrProfesor(BasePermission):
    """
    Permiso para directores y profesores
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request.user, 'tipo_usuario') and
            request.user.tipo_usuario in ['director', 'profesor']
        )
