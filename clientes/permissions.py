from rest_framework.permissions import BasePermission, SAFE_METHODS


ADMINISTRADOR_GROUP = 'administrador'
VENDEDOR_GROUP = 'vendedor'


def is_administrador(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name=ADMINISTRADOR_GROUP).exists()
    )


def is_vendedor(user):
    return (
        user.is_authenticated
        and user.groups.filter(name=VENDEDOR_GROUP).exists()
    )


class IsAdministradorOrVendedor(BasePermission):
    def has_permission(self, request, view):
        return is_administrador(request.user) or is_vendedor(request.user)


class IsAdministradorOrOwnClientReadOnly(BasePermission):
    def has_permission(self, request, view):
        return is_administrador(request.user) or (
            is_vendedor(request.user) and request.method in SAFE_METHODS
        )

    def has_object_permission(self, request, view, obj):
        return is_administrador(request.user) or (
            is_vendedor(request.user)
            and request.method in SAFE_METHODS
            and obj.responsavel_id == request.user.pk
        )


class IsAdministradorOrOwnNoteReadOnly(BasePermission):
    def has_permission(self, request, view):
        return is_administrador(request.user) or (
            is_vendedor(request.user) and request.method in SAFE_METHODS
        )

    def has_object_permission(self, request, view, obj):
        return is_administrador(request.user) or (
            is_vendedor(request.user)
            and request.method in SAFE_METHODS
            and obj.cliente.responsavel_id == request.user.pk
        )


class IsAdministrador(BasePermission):
    def has_permission(self, request, view):
        return is_administrador(request.user)
