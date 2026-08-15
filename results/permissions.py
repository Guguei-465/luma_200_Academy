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


# =====================================================
# Super Admin
# =====================================================

class IsSuperAdmin(BasePermission):
    """
    Allows access only to Super Administrators.
    """

    def has_permission(self, request, view):
        return is_super_admin(request.user)


# =====================================================
# Academic Coordinator
# =====================================================

class IsAcademicCoordinator(BasePermission):
    """
    Allows access only to Academic Coordinators.
    """

    def has_permission(self, request, view):
        return is_academic_coordinator(request.user)


# =====================================================
# Teacher
# =====================================================

class IsTeacher(BasePermission):
    """
    Allows access only to Teachers.
    """

    def has_permission(self, request, view):
        return is_teacher(request.user)


# =====================================================
# Super Admin OR Academic Coordinator
# =====================================================

class IsAdminOrAcademicCoordinator(BasePermission):
    """
    Allows Super Admin or Academic Coordinator.
    """

    def has_permission(self, request, view):
        return (
            is_super_admin(request.user)
            or is_academic_coordinator(request.user)
        )


# =====================================================
# Teacher OR Academic Coordinator
# =====================================================

class IsTeacherOrAcademicCoordinator(BasePermission):
    """
    Allows Teachers or Academic Coordinators.
    """

    def has_permission(self, request, view):
        return (
            is_teacher(request.user)
            or is_academic_coordinator(request.user)
        )


# =====================================================
# Assigned Teacher
# =====================================================

class IsAssignedTeacher(BasePermission):
    """
    Allows authenticated teachers who are assigned to
    the classroom and subject involved in the request.

    This permission is mainly used for creating and
    bulk-entering results.
    """

    def has_permission(self, request, view):

        if not is_teacher(request.user):
            return False

        return True

    def has_object_permission(self, request, view, obj):

        if not is_teacher(request.user):
            return False

        return _teacher_is_assigned_to_result(
            request.user,
            obj
        )


# =====================================================
# Assigned Teacher Object Permission
# =====================================================

class IsAssignedTeacherObject(BasePermission):
    """
    Object-level permission used when a teacher edits
    or deletes an existing Result.

    The teacher must be assigned to the subject/classroom
    represented by that result.
    """

    def has_permission(self, request, view):
        return is_teacher(request.user)

    def has_object_permission(self, request, view, obj):

        if not is_teacher(request.user):
            return False

        return _teacher_is_assigned_to_result(
            request.user,
            obj
        )


# =====================================================
# Assignment Checker
# =====================================================

def _teacher_is_assigned_to_result(user, result):
    """
    Checks whether the teacher is assigned to the
    classroom + subject for the result.

    The Luma system allows one teacher to teach
    multiple subjects and multiple classes.

    TeacherAssignment is therefore checked using BOTH:
        - teacher
        - classroom
        - subject
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
# Assessment Assignment Permission
# =====================================================

class IsAssignedTeacherAssessment(BasePermission):
    """
    Checks whether a teacher is assigned to the
    classroom and subject of an Assessment.
    """

    def has_permission(self, request, view):
        return is_teacher(request.user)

    def has_object_permission(self, request, view, assessment):

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
# Result Submission Permission
# =====================================================

class IsAssignedTeacherSubmission(BasePermission):
    """
    Allows a teacher to work with a ResultSubmission
    only when the teacher is assigned to the assessment's
    classroom and subject.
    """

    def has_permission(self, request, view):
        return is_teacher(request.user)

    def has_object_permission(self, request, view, submission):

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