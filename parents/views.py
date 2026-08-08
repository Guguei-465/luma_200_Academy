from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.models import ParentProfile
from .permissions import IsSuperAdmin
from .models import ParentStudent
from .serializers import ParentStudentSerializer


# Create your views here.
class ParentStudentViewSet(viewsets.ModelViewSet):
    serializer_class = ParentStudentSerializer

    def get_queryset(self):
        user = self.request.user

        # Staff (super admin, academic coordinator, accountant, teacher) can view all parent records
        if user.role in [
            user.Role.SUPER_ADMIN,
            user.Role.ACCOUNTANT,
            user.Role.ACADEMIC_COORDINATOR,
            user.Role.TEACHER,
        ]:
            return ParentStudent.objects.select_related(
                "parent__user",
                "student",
            )

        # A parent sees only their own linked children
        parent = ParentProfile.objects.filter(
            user=user
        ).first()

        if not parent:
            return ParentStudent.objects.none()

        return ParentStudent.objects.filter(
            parent=parent
        ).select_related(
            "parent__user",
            "student",
        )

    def get_permissions(self):
        if self.action in [
            "create",
            "update",
            "partial_update",
            "destroy",
        ]:
            permission_classes = [
                IsSuperAdmin,
            ]
        else:
            permission_classes = [
                IsAuthenticated,
            ]

        return [permission() for permission in permission_classes]