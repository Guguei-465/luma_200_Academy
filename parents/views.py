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

        if user.role == user.Role.SUPER_ADMIN:
            return ParentStudent.objects.select_related(
                "parent__user",
                "student",
            )

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