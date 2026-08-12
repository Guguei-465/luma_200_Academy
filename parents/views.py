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

        # Staff can see all students
        if user.role in [
            user.Role.SUPER_ADMIN,
            user.Role.ACCOUNTANT,
            user.Role.ACADEMIC_COORDINATOR,
            user.Role.TEACHER,
        ]:
            return Student.objects.select_related(
                "parent__user",
                "classroom",
            )

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