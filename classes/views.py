from django.shortcuts import render
from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import ClassRoom
from .serializers import ClassRoomSerializer
from accounts.permisions import IsAdminOrAcademicCoordinator


# Create your views here.
# List all classrooms
class ClassRoomListView(generics.ListAPIView):
    queryset = ClassRoom.objects.select_related(
        "class_teacher",
        "class_teacher__user",
    )
    serializer_class = ClassRoomSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "grade",
        "stream",
    ]

    search_fields = [
        "grade",
        "stream",
        "class_teacher__user__first_name",
        "class_teacher__user__last_name",
    ]

    ordering_fields = [
        "grade",
        "stream",
        "capacity",
        "created_at",
    ]

# Retrieve one classroom
class ClassRoomDetailView(generics.RetrieveAPIView):
    queryset = ClassRoom.objects.select_related("class_teacher", "class_teacher__user")
    serializer_class = ClassRoomSerializer
    permission_classes = [IsAuthenticated]


# Create classroom
class ClassRoomCreateView(generics.CreateAPIView):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# Update classroom
class ClassRoomUpdateView(generics.UpdateAPIView):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# Delete classroom
class ClassRoomDeleteView(generics.DestroyAPIView):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassRoomSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]