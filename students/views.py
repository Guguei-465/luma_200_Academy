from django.db import transaction

from rest_framework import generics, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend

from .models import Student, StudentTransfer
from .serializers import (
    StudentSerializer,
    StudentTransferSerializer,
)

from accounts.permisions import IsAdminOrAcademicCoordinator


# ==========================================
# List Students
# ==========================================
class StudentListView(generics.ListAPIView):
    queryset = Student.objects.select_related(
        "classroom",
        "classroom__class_teacher__user",
        "parent",
        "parent__user",
    )

    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "classroom",
        "parent",
        "gender",
        "status",
    ]

    search_fields = [
        "admission_number",
        "assessment_number",
        "first_name",
        "last_name",
        "parent__user__first_name",
        "parent__user__last_name",
    ]

    ordering_fields = [
        "admission_number",
        "first_name",
        "last_name",
        "date_admitted",
        "created_at",
    ]

    ordering = [
        "admission_number",
    ]


# ==========================================
# Retrieve Student
# ==========================================
class StudentDetailView(generics.RetrieveAPIView):
    queryset = Student.objects.select_related(
        "classroom",
        "classroom__class_teacher__user",
        "parent",
        "parent__user",
    )

    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]


# ==========================================
# Create Student
# ==========================================
class StudentCreateView(generics.CreateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# ==========================================
# Update Student
# ==========================================
class StudentUpdateView(generics.UpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# ==========================================
# Delete Student
# ==========================================
class StudentDeleteView(generics.DestroyAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# ==========================================
# Transfer Student
# ==========================================
class StudentTransferView(APIView):
    permission_classes = [IsAdminOrAcademicCoordinator]

    @transaction.atomic
    def post(self, request):

        serializer = StudentTransferSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        transfer = serializer.save(
            transferred_by=request.user
        )

        student = transfer.student
        student.classroom = transfer.to_classroom
        student.save()

        return Response(
            {
                "message": "Student transferred successfully.",
                "transfer": StudentTransferSerializer(
                    transfer
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


# ==========================================
# List Student Transfers
# ==========================================
class StudentTransferListView(generics.ListAPIView):
    queryset = StudentTransfer.objects.select_related(
        "student",
        "from_classroom",
        "to_classroom",
        "transferred_by",
    )

    serializer_class = StudentTransferSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = [
        "student",
        "from_classroom",
        "to_classroom",
        "transfer_date",
    ]

    search_fields = [
        "student__admission_number",
        "student__first_name",
        "student__last_name",
    ]

    ordering_fields = [
        "transfer_date",
        "created_at",
    ]

    ordering = [
        "-transfer_date",
    ]


# ==========================================
# Retrieve Student Transfer
# ==========================================
class StudentTransferDetailView(generics.RetrieveAPIView):
    queryset = StudentTransfer.objects.select_related(
        "student",
        "from_classroom",
        "to_classroom",
        "transferred_by",
    )

    serializer_class = StudentTransferSerializer
    permission_classes = [IsAuthenticated]