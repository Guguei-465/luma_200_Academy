from rest_framework.permissions import BasePermission
from .models import CustomUser


class IsAdminOrAcademicCoordinator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [
                CustomUser.Role.SUPER_ADMIN,
                CustomUser.Role.ACADEMIC_COORDINATOR,
            ]
        )