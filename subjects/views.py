from django.shortcuts import render
from rest_framework import viewsets
from .models import Subject
from .serializers import SubjectSerializer


# Create your views here.
class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer