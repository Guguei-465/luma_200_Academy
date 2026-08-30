from rest_framework.permissions import BasePermission


# =====================================================
# Helper
# =====================================================

def is_super_admin(user):
    return (
        user
        and user.is_authenticated
        and getattr(user, "role", None) == "SUPER_ADMIN"
    )


def is_academic_coordinator(user):
    return (
        user
        and user.is_authenticated
        and getattr(user, "role", None) == "ACADEMIC_COORDINATOR"
    )


def is_teacher(user):
    return (
        user
        and user.is_authenticated
        and getattr(user, "role", None) == "TEACHER"
    )


def is_admin_or_coordinator_or_teacher(user):
    """Helper: Allow Super Admin OR Coordinator OR Teacher"""
    return (
        is_super_admin(user)
        or is_academic_coordinator(user)
        or is_teacher(user)
    )


# =====================================================
# Super Admin
# =====================================================

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_super_admin(request.user)


# =====================================================
# Academic Coordinator
# =====================================================

class IsAcademicCoordinator(BasePermission):
    def has_permission(self, request, view):
        return is_academic_coordinator(request.user)


# =====================================================
# Teacher
# =====================================================

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return is_teacher(request.user)


# =====================================================
# Super Admin OR Academic Coordinator
# =====================================================

class IsAdminOrAcademicCoordinator(BasePermission):
    def has_permission(self, request, view):
        return (
            is_super_admin(request.user)
            or is_academic_coordinator(request.user)
        )


# =====================================================
# Teacher OR Academic Coordinator OR Super Admin ✅ NEW
# =====================================================

class IsTeacherOrAcademicCoordinator(BasePermission):
    """Allows Teachers, Academic Coordinators, OR Super Admins."""
    def has_permission(self, request, view):
        return is_admin_or_coordinator_or_teacher(request.user)


# =====================================================
# Assigned Teacher — ✅ NOW ALLOWS COORDINATOR & SUPER ADMIN
# =====================================================

class IsAssignedTeacher(BasePermission):
    """
    Allows:
    - ✅ Super Admin
    - ✅ Academic Coordinator
    - ✅ Assigned Teacher (create/write)
    """

    def has_permission(self, request, view):
        # ✅ Admin & Coordinator pass through immediately
        if is_super_admin(request.user) or is_academic_coordinator(request.user):
            return True
        # Teacher must be checked further
        return is_teacher(request.user)

    def has_object_permission(self, request, view, obj):
        # ✅ Admin & Coordinator can view ANY result
        if is_super_admin(request.user) or is_academic_coordinator(request.user):
            return True
        # Teacher: check assignment
        return _teacher_is_assigned_to_result(request.user, obj)


# =====================================================
# Assigned Teacher Object — ✅ NOW ALLOWS COORDINATOR & SUPER ADMIN
# =====================================================

class IsAssignedTeacherObject(BasePermission):
    """
    Object-level permission.
    - ✅ Super Admin & Coordinator: FULL ACCESS to ALL results
    - Teacher: only their assigned classroom+subject
    """

    def has_permission(self, request, view):
        return is_admin_or_coordinator_or_teacher(request.user)

    def has_object_permission(self, request, view, obj):
        if is_super_admin(request.user) or is_academic_coordinator(request.user):
            return True
        if not is_teacher(request.user):
            return False
        return _teacher_is_assigned_to_result(request.user, obj)


# =====================================================
# Assignment Checker
# =====================================================

def _teacher_is_assigned_to_result(user, result):
    """
    Checks whether the teacher is assigned to the
    classroom + subject for the result.
    """
    try:
        from assignments.models import TeacherAssignment
    except ImportError:
        return False

    try:
        assessment = result.submission.assessment
        if assessment is None:
            return False
        return TeacherAssignment.objects.filter(
            teacher__user=user,
            classroom=assessment.classroom,
            subject=assessment.subject,
        ).exists()
    except AttributeError:
        return False


# =====================================================
# Assessment Assignment Permission — ✅ NOW ALLOWS COORDINATOR & SUPER ADMIN
# =====================================================

class IsAssignedTeacherAssessment(BasePermission):
    def has_permission(self, request, view):
        return is_admin_or_coordinator_or_teacher(request.user)

    def has_object_permission(self, request, view, assessment):
        if is_super_admin(request.user) or is_academic_coordinator(request.user):
            return True
        if not is_teacher(request.user):
            return False
        try:
            from assignments.models import TeacherAssignment
        except ImportError:
            return False
        return TeacherAssignment.objects.filter(
            teacher__user=request.user,
            classroom=assessment.classroom,
            subject=assessment.subject,
        ).exists()


# =====================================================
# Result Submission Permission — ✅ NOW ALLOWS COORDINATOR & SUPER ADMIN
# =====================================================

class IsAssignedTeacherSubmission(BasePermission):
    def has_permission(self, request, view):
        return is_admin_or_coordinator_or_teacher(request.user)

    def has_object_permission(self, request, view, submission):
        if is_super_admin(request.user) or is_academic_coordinator(request.user):
            return True
        if not is_teacher(request.user):
            return False
        try:
            from assignments.models import TeacherAssignment
        except ImportError:
            return False
        if not submission.assessment:
            return False
        return TeacherAssignment.objects.filter(
            teacher__user=request.user,
            classroom=submission.assessment.classroom,
            subject=submission.assessment.subject,
        ).exists()