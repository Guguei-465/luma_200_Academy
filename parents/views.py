from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import ParentProfile
from students.models import Student
from students.serializers import StudentSerializer


class ParentChildrenViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user

<<<<<<< HEAD
        # Admin/Coordinator/Accountant legitimately need the
        # full roster.
=======
        # Staff can see all students
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
        if user.role in [
            user.Role.SUPER_ADMIN,
            user.Role.ACCOUNTANT,
            user.Role.ACADEMIC_COORDINATOR,
<<<<<<< HEAD
=======
            user.Role.TEACHER,
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
        ]:
            return Student.objects.select_related(
                "parent__user",
                "classroom",
            )

<<<<<<< HEAD
        # Teachers only see students in classrooms they're
        # actively assigned to — consistent with the scoping
        # enforced in students.views.StudentListView. Without
        # this, a teacher could bypass that restriction simply
        # by calling this endpoint instead.
        if user.role == user.Role.TEACHER:

            from assignments.models import TeacherAssignment

            teacher_profile = getattr(user, "teacher_profile", None)

            if not teacher_profile:
                return Student.objects.none()

            classroom_ids = TeacherAssignment.objects.filter(
                teacher=teacher_profile,
                is_active=True,
            ).values_list("classroom_id", flat=True)

            return Student.objects.filter(
                classroom_id__in=classroom_ids
            ).select_related(
                "parent__user",
                "classroom",
            )

=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
        # Find logged-in parent's profile
        parent = ParentProfile.objects.filter(
            user=user
        ).first()

        # User has no parent profile
        if not parent:
            return Student.objects.none()

        # Return ONLY this parent's children
        return Student.objects.filter(
            parent=parent
        ).select_related(
            "parent__user",
            "classroom",
        )