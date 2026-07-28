from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from accounts.models import TeacherProfile
from .serializers import TeacherProfileSerializer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import TeacherAssignment
from .serializers import TeacherAssignmentSerializer
from accounts.permisions import IsAdminOrAcademicCoordinator


# =====================================================
# Create Assignment
# =====================================================
class TeacherAssignmentCreateView(generics.CreateAPIView):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# =====================================================
# List Assignments
# =====================================================
class TeacherAssignmentListView(generics.ListAPIView):
    queryset = TeacherAssignment.objects.select_related(
        "teacher__user",
        "classroom",
        "subject",
    )
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]

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


# =====================================================
# Retrieve Assignment
# =====================================================
class TeacherAssignmentDetailView(generics.RetrieveAPIView):
    queryset = TeacherAssignment.objects.select_related(
        "teacher__user",
        "classroom",
        "subject",
    )
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# =====================================================
# Update Assignment
# =====================================================
class TeacherAssignmentUpdateView(generics.UpdateAPIView):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# =====================================================
# Delete Assignment
# =====================================================
class TeacherAssignmentDeleteView(generics.DestroyAPIView):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


class TeacherProfileViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TeacherProfile.objects.filter(user=self.request.user)
 
