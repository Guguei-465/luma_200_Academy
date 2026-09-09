from rest_framework.permissions import BasePermission

from accounts.models import CustomUser


class HasRolePermission(BasePermission):
    """
    Base permission class for role-based access.
    """

    allowed_roles = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in self.allowed_roles
        )


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


class IsParent(HasRolePermission):
    allowed_roles = [
        CustomUser.Role.PARENT,
    ]


class IsAdminOrAcademicCoordinator(HasRolePermission):
    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
        CustomUser.Role.ACADEMIC_COORDINATOR,
    ]


class IsAdminOrAccountant(HasRolePermission):
    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
        CustomUser.Role.ACCOUNTANT,
    ]


class IsAdminOrTeacher(HasRolePermission):
    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
        CustomUser.Role.TEACHER,
    ]


class IsDashboardUser(HasRolePermission):
    """
    Any authenticated staff member allowed to view the dashboard.
    """

    allowed_roles = [
        CustomUser.Role.SUPER_ADMIN,
        CustomUser.Role.ACADEMIC_COORDINATOR,
        CustomUser.Role.ACCOUNTANT,
        CustomUser.Role.TEACHER,
    ]