from django.shortcuts import render
from rest_framework import generics

from .models import Exam
from .serializers import ExamSerializer
from accounts.permisions import IsAdminOrAcademicCoordinator


# Create your views here.
# =====================================================
# Create Exam
# =====================================================
class ExamCreateView(generics.CreateAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# =====================================================
# List Exams
# =====================================================
class ExamListView(generics.ListAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# =====================================================
# Retrieve Exam
# =====================================================
class ExamDetailView(generics.RetrieveAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# =====================================================
# Update Exam
# =====================================================
class ExamUpdateView(generics.UpdateAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]


# =====================================================
# Delete Exam
# =====================================================
class ExamDeleteView(generics.DestroyAPIView):
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer
    permission_classes = [IsAdminOrAcademicCoordinator]