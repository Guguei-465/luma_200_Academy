from rest_framework.permissions import BasePermission
from accounts.models import CustomUser

class HasRolePermission(BasePermission):
    """
    Allows access only to users with the required roles.
    """

    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in self.allowed_roles 
    

class IsSuperAdmin(HasRolePermission):
    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
    ]


class IsAcademicCoordinator(HasRolePermission):
    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
        CustomUser.Role.ACADEMIC_COORDINATOR,
    ]


class IsAccountant(HasRolePermission):
    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
        CustomUser.Role.ACCOUNTANT,
    ]


class IsTeacher(HasRolePermission):
    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
        CustomUser.Role.TEACHER,
    ]





