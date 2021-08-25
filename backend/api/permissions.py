from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Разрешить создание рецептов авторизированным и изменение владельцам"""
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.author == request.user
