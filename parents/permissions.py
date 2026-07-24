from rest_framework.permissions import BasePermission

from accounts.models import CustomUser


class IsSuperAdmin(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == CustomUser.Role.SUPER_ADMIN
        ) 