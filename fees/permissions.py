from rest_framework.permissions import BasePermission
from accounts.models import CustomUser


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == CustomUser.Role.SUPER_ADMIN
        )


class IsAccountant(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == CustomUser.Role.ACCOUNTANT
        )


class IsSuperAdminOrAccountant(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [
                CustomUser.Role.SUPER_ADMIN,
                CustomUser.Role.ACCOUNTANT,
            ]
        )


class IsAcademicCoordinator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == CustomUser.Role.ACADEMIC_COORDINATOR
        )


class IsSuperAdminAccountantOrAcademicCoordinator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in [
                CustomUser.Role.SUPER_ADMIN,
                CustomUser.Role.ACCOUNTANT,
                CustomUser.Role.ACADEMIC_COORDINATOR,
            ]
        )