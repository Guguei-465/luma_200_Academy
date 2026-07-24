from rest_framework.permissions import BasePermission

from assignments.models import TeacherAssignment

from .models import Assessment


# =====================================================
# Super Admin
# =====================================================
class IsSuperAdmin(BasePermission):
    """
    Allows access only to Super Admins.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "SUPER_ADMIN"
        )


# =====================================================
# Academic Coordinator
# =====================================================
class IsAcademicCoordinator(BasePermission):
    """
    Allows access only to Academic Coordinators.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "ACADEMIC_COORDINATOR"
        )


# =====================================================
# Teacher
# =====================================================
class IsTeacher(BasePermission):
    """
    Allows access only to Teachers.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "TEACHER"
        )


# =====================================================
# Parent
# =====================================================
class IsParent(BasePermission):
    """
    Allows access only to Parents.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "PARENT"
        )


# =====================================================
# Teacher or Academic Coordinator
# =====================================================
class IsTeacherOrAcademicCoordinator(BasePermission):
    """
    Allows Teachers and Academic Coordinators.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in (
                "TEACHER",
                "ACADEMIC_COORDINATOR",
            )
        )


# =====================================================
# Super Admin or Academic Coordinator
# =====================================================
class IsAdminOrAcademicCoordinator(BasePermission):
    """
    Allows Super Admins and Academic Coordinators.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in (
                "SUPER_ADMIN",
                "ACADEMIC_COORDINATOR",
            )
        )


# =====================================================
# Parent Read Only
# =====================================================
class IsParentReadOnly(BasePermission):
    """
    Parents can only view results.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role == "PARENT" and
            request.method in (
                "GET",
                "HEAD",
                "OPTIONS",
            )
        )


# =====================================================
# Assigned Teacher
# =====================================================
class IsAssignedTeacher(BasePermission):
    """
    Allows only the assigned teacher to enter marks
    for a particular assessment.
    """

    message = (
        "You are not assigned to teach this class and subject."
    )

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if request.user.role == "SUPER_ADMIN":
            return True

        if request.user.role == "ACADEMIC_COORDINATOR":
            return True

        if request.user.role != "TEACHER":
            return False

        assessment_id = (
            request.data.get("assessment")
            or request.query_params.get("assessment")
        )

        if not assessment_id:
            return False

        try:
            assessment = Assessment.objects.get(pk=assessment_id)
        except Assessment.DoesNotExist:
            return False

        if not hasattr(request.user, "teacher_profile"):
            return False

        return TeacherAssignment.objects.filter(
            teacher=request.user.teacher_profile,
            classroom=assessment.classroom,
            subject=assessment.subject,
            is_active=True,
        ).exists()


# =====================================================
# Assigned Teacher (Object Level)
# =====================================================
class IsAssignedTeacherObject(BasePermission):
    """
    Object-level permission for updating or deleting results.
    """

    message = (
        "You are not assigned to this assessment."
    )

    def has_object_permission(self, request, view, obj):

        if request.user.role == "SUPER_ADMIN":
            return True

        if request.user.role == "ACADEMIC_COORDINATOR":
            return True

        if request.user.role != "TEACHER":
            return False

        if not hasattr(request.user, "teacher_profile"):
            return False

        assessment = obj.submission.assessment

        return TeacherAssignment.objects.filter(
            teacher=request.user.teacher_profile,
            classroom=assessment.classroom,
            subject=assessment.subject,
            is_active=True,
        ).exists()