from django.shortcuts import render

from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated

from .models import Timetable
from .serializers import TimetableSerializer
from accounts.permisions import IsAdminOrAcademicCoordinator

# Create your views here.
# List Timetable
class TimetableListView(generics.ListAPIView):
    queryset = Timetable.objects.select_related(
        "assignment",
        "assignment__teacher",
        "assignment__teacher__user",
        "assignment__subject",
        "assignment__classroom",
    )

    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    search_fields = [
        "assignment__teacher__user__first_name",
        "assignment__teacher__user__last_name",
        "assignment__subject__name",
        "assignment__classroom__grade",
        "assignment__classroom__stream",
        "day",
        "term",
        "academic_year",
    ]

    ordering_fields = [
        "day",
        "start_time",
        "end_time",
        "academic_year",
    ]

    filterset_fields = [
        "academic_year",
        "term",
        "day",
        "assignment__teacher",
        "assignment__classroom",
        "assignment__subject",
    ]


# Retrieve Timetable
class TimetableDetailView(generics.RetrieveAPIView):
    queryset = Timetable.objects.select_related(
        "assignment",
        "assignment__teacher",
        "assignment__teacher__user",
        "assignment__subject",
        "assignment__classroom",
    )

    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]


# Create Timetable
class TimetableCreateView(generics.CreateAPIView):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# Update Timetable
class TimetableUpdateView(generics.UpdateAPIView):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# Delete Timetable
class TimetableDeleteView(generics.DestroyAPIView):
    queryset = Timetable.objects.all()
    serializer_class = TimetableSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]

# =====================================================
# My Timetable (Teacher)
# =====================================================
class MyTimetableView(generics.ListAPIView):

    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        if not hasattr(self.request.user, "teacher_profile"):
            return Timetable.objects.none()

        return Timetable.objects.select_related(
            "assignment",
            "assignment__teacher",
            "assignment__teacher__user",
            "assignment__subject",
            "assignment__classroom",
        ).filter(
            assignment__teacher=self.request.user.teacher_profile,
            is_active=True,
        ).order_by(
            "day",
            "start_time",
        )
    
# =====================================================
# Classroom Timetable
# =====================================================
class ClassroomTimetableView(generics.ListAPIView):

    serializer_class = TimetableSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        classroom_id = self.kwargs["classroom_id"]

        return Timetable.objects.select_related(
            "assignment",
            "assignment__teacher",
            "assignment__teacher__user",
            "assignment__subject",
            "assignment__classroom",
        ).filter(
            assignment__classroom_id=classroom_id,
            is_active=True,
        ).order_by(
            "day",
            "start_time",
        )    