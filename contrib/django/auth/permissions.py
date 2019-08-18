from rest_framework.permissions import BasePermission


class TroodAuthPermissions(BasePermission):

    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        return True


class TroodABACPermission(BasePermission):

    def has_permission(self, request, view):
        return request.abac.check_permited(request, view)

    def has_object_permission(self, request, view, obj):
        return request.abac.check_permited(request, view)
