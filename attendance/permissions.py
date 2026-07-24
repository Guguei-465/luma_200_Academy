from rest_framework.permissions import BasePermission

from assignments.models import TeacherAssignment
from accounts.models import CustomUser


class IsAssignedClassTeacher(BasePermission):
    """
    Allows access only to:
    - Super Admin
    - Academic Coordinator
    - Assigned active class teacher
    """

    def has_permission(self, request, view):

        # User must be authenticated
        if not request.user.is_authenticated:
            return False

        # Super Admin
        if request.user.role == CustomUser.Role.SUPER_ADMIN:
            return True

        # Academic Coordinator
        if request.user.role == CustomUser.Role.ACADEMIC_COORDINATOR:
            return True

        # Only teachers beyond this point
        if request.user.role != CustomUser.Role.TEACHER:
            return False

        # Teacher profile must exist
        if not hasattr(request.user, "teacher_profile"):
            return False

        classroom_id = request.data.get("classroom")

        # Some endpoints (mark/submit) don't send classroom directly.
        # They perform object-level verification inside the view.
        if classroom_id is None:
            return True

        return TeacherAssignment.objects.filter(
            teacher=request.user.teacher_profile,
            classroom_id=classroom_id,
            is_active=True,
            is_class_teacher=True,
        ).exists()