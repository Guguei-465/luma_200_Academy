from django.db.models import Prefetch

from rest_framework import generics, filters, viewsets
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import TeacherProfile
from accounts.permisions import IsAdminOrAcademicCoordinator

from .models import TeacherAssignment
from .serializers import (
    TeacherAssignmentSerializer,
    TeacherProfileSerializer,
)


# =====================================================
# CREATE ASSIGNMENT
# =====================================================

class TeacherAssignmentCreateView(generics.CreateAPIView):

    queryset = TeacherAssignment.objects.all()

    serializer_class = TeacherAssignmentSerializer

    permission_classes = [
        IsAdminOrAcademicCoordinator
    ]


# =====================================================
# LIST ASSIGNMENTS
# =====================================================

class TeacherAssignmentListView(generics.ListAPIView):

    serializer_class = TeacherAssignmentSerializer

    permission_classes = [
        IsAuthenticated
    ]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "teacher",
        "classroom",
        "subject",
        "term",
        "academic_year",
        "is_active",
        "is_class_teacher",
    ]

    search_fields = [
        "teacher__user__first_name",
        "teacher__user__last_name",
        "teacher__user__username",
        "teacher__employee_number",
        "subject__name",
        "classroom__grade",
        "classroom__stream",
    ]

    ordering_fields = [
        "academic_year",
        "term",
        "assigned_date",
        "created_at",
    ]

    ordering = [
        "-created_at"
    ]

    def get_queryset(self):

        user = self.request.user

        queryset = TeacherAssignment.objects.select_related(
            "teacher__user",
            "classroom",
            "subject",
        )

        # =================================================
        # ADMIN / ACADEMIC COORDINATOR
        # =================================================

        if user.role in [
            "SUPER_ADMIN",
            "ACADEMIC_COORDINATOR",
        ]:
            return queryset

        # =================================================
        # TEACHER
        # =================================================

        if user.role == "TEACHER":

            return queryset.filter(
                teacher__user=user,
                is_active=True,
            )

        # =================================================
        # OTHER USERS
        # =================================================

        return queryset.none()


# =====================================================
# RETRIEVE ASSIGNMENT
# =====================================================

class TeacherAssignmentDetailView(generics.RetrieveAPIView):

    queryset = TeacherAssignment.objects.select_related(
        "teacher__user",
        "classroom",
        "subject",
    )

    serializer_class = TeacherAssignmentSerializer

    permission_classes = [
        IsAdminOrAcademicCoordinator
    ]


# =====================================================
# UPDATE ASSIGNMENT
# =====================================================

class TeacherAssignmentUpdateView(generics.UpdateAPIView):

    queryset = TeacherAssignment.objects.all()

    serializer_class = TeacherAssignmentSerializer

    permission_classes = [
        IsAdminOrAcademicCoordinator
    ]


# =====================================================
# DELETE ASSIGNMENT
# =====================================================

class TeacherAssignmentDeleteView(generics.DestroyAPIView):

    queryset = TeacherAssignment.objects.all()

    serializer_class = TeacherAssignmentSerializer

    permission_classes = [
        IsAdminOrAcademicCoordinator
    ]


# =====================================================
# TEACHER PROFILE
# =====================================================

class TeacherProfileViewSet(viewsets.ModelViewSet):

    serializer_class = TeacherProfileSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        user = self.request.user

        # Admin and coordinator can see all teachers
        if user.role in [
            "SUPER_ADMIN",
            "ACADEMIC_COORDINATOR",
        ]:
            return TeacherProfile.objects.select_related(
                "user"
            ).all()

        # Teacher can see own profile
        return TeacherProfile.objects.filter(
            user=user
        ).select_related(
            "user"
        )