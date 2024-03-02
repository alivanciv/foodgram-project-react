from rest_framework import permissions


class IsOwner(permissions.IsAuthenticated):

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)


class IsAdminOrReadOnly(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_staff)
