from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAdminUserOrReadOnly(BasePermission):
    """Проверка на залогиненного пользователя."""

    message = "Доступ разрешен только для авторизованных пользователей."

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
            and request.user.is_admin
        )

class IsAuthorOrReadOnly(permissions.BasePermission):
    """Проверка на права доступа для Автора."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
