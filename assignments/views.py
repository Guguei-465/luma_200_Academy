from rest_framework import generics, filters, viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from accounts.models import TeacherProfile
from .models import TeacherAssignment
from .serializers import TeacherAssignmentSerializer, TeacherProfileSerializer
from accounts.permisions import IsAdminOrAcademicCoordinator


# =====================================================
# ✅ Public Teacher List — for dropdowns
# =====================================================
class TeacherProfileListView(generics.ListAPIView):
    """Returns all teachers with active assignments — for frontend dropdowns"""
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TeacherProfile.objects.filter(
            assignments__is_active=True
        ).distinct().select_related("user")


# =====================================================
# Assignment CRUD
# =====================================================
class TeacherAssignmentCreateView(generics.CreateAPIView):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


class TeacherAssignmentListView(generics.ListAPIView):
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["teacher", "classroom", "subject", "term", "academic_year", "is_active", "is_class_teacher"]
    search_fields = ["teacher__user__first_name", "teacher__user__last_name", "teacher__user__username", "subject__name", "classroom__grade", "classroom__stream"]
    ordering_fields = ["academic_year", "term", "assigned_date", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        u = self.request.user
        qs = TeacherAssignment.objects.select_related("teacher__user", "classroom", "subject")
        if u.role in ["SUPER_ADMIN", "ACADEMIC_COORDINATOR"]:
            return qs
        if u.role == "TEACHER":
            return qs.filter(teacher__user=u, is_active=True)
        return TeacherAssignment.objects.none()


class TeacherAssignmentDetailView(generics.RetrieveAPIView):
    queryset = TeacherAssignment.objects.select_related("teacher__user", "classroom", "subject")
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


class TeacherAssignmentUpdateView(generics.UpdateAPIView):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


class TeacherAssignmentDeleteView(generics.DestroyAPIView):
    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


class TeacherProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """Logged-in teacher's own profile"""
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TeacherProfile.objects.filter(user=self.request.user)