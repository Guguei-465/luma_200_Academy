from rest_framework.permissions import BasePermission

from accounts.models import CustomUser


class IsSuperAdmin(BasePermission):
    """
    Allows access only to Super Admin users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == CustomUser.Role.SUPER_ADMIN
        )


class IsNotificationRecipient(BasePermission):
    """
    Allows users to access only their own notifications.
    """

    def has_object_permission(self, request, view, obj):
        return obj.recipient == request.user