from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.models import ParentProfile
from students.models import Student, StudentTransfer
from students.serializers import (
    StudentSerializer,
    StudentListSerializer,
    StudentTransferSerializer,
)


# =====================================================
# STUDENT LIST
# GET /api/students/
# =====================================================

class StudentListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        students = Student.objects.select_related(
            "parent__user",
            "classroom",
        ).all()

        serializer = StudentListSerializer(
            students,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data)


# =====================================================
# STUDENT DETAIL
# GET /api/students/int:pk/
# =====================================================

class StudentDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        student = get_object_or_404(
            Student.objects.select_related(
                "parent__user",
                "classroom",
            ),
            pk=pk
        )

        serializer = StudentSerializer(
            student,
            context={"request": request}
        )

        return Response(serializer.data)


# =====================================================
# CREATE STUDENT
# POST /api/students/create/
# =====================================================

class StudentCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = StudentSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():

            student = serializer.save()

            return Response(
                StudentSerializer(
                    student,
                    context={"request": request}
                ).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =====================================================
# UPDATE STUDENT
# PUT/PATCH /api/students/update/<int:pk>/
# =====================================================

class StudentUpdateView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):

        student = get_object_or_404(
            Student,
            pk=pk
        )

        serializer = StudentSerializer(
            student,
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():

            student = serializer.save()

            return Response(
                StudentSerializer(
                    student,
                    context={"request": request}
                ).data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request, pk):

        student = get_object_or_404(
            Student,
            pk=pk
        )

        serializer = StudentSerializer(
            student,
            data=request.data,
            partial=True,
            context={"request": request}
        )

        if serializer.is_valid():

            student = serializer.save()

            return Response(
                StudentSerializer(
                    student,
                    context={"request": request}
                ).data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# =====================================================
# DELETE STUDENT
# DELETE /api/students/delete/<int:pk>/
# =====================================================

class StudentDeleteView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        student = get_object_or_404(
            Student,
            pk=pk
        )

        student.delete()

        return Response(
            {
                "message": "Student deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT
        )


# =====================================================
# STUDENT TRANSFER
# POST /api/students/transfer/
# =====================================================

class StudentTransferView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        serializer = StudentTransferSerializer(
            data=request.data,
            context={"request": request}
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        transfer = serializer.save(
            transferred_by=request.user
        )

        # =============================================
        # Update student's classroom
        # =============================================

        student = transfer.student

        student.classroom = transfer.to_classroom

        student.save(
            update_fields=[
                "classroom",
                "updated_at",
            ]
        )

        return Response(
            StudentTransferSerializer(
                transfer,
                context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED
        )


# =====================================================
# TRANSFER LIST
# GET /api/students/transfers/
# =====================================================

class StudentTransferListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        transfers = StudentTransfer.objects.select_related(
            "student",
            "from_classroom",
            "to_classroom",
            "transferred_by",
        ).all()

        serializer = StudentTransferSerializer(
            transfers,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data)


# =====================================================
# TRANSFER DETAIL
# GET /api/students/transfers/<int:pk>/
# =====================================================

class StudentTransferDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        transfer = get_object_or_404(
            StudentTransfer.objects.select_related(
                "student",
                "from_classroom",
                "to_classroom",
                "transferred_by",
            ),
            pk=pk
        )

        serializer = StudentTransferSerializer(
            transfer,
            context={"request": request}
        )

        return Response(serializer.data)


# =====================================================
# PARENT CHILDREN
# GET /api/dashboard/parent/children/
# =====================================================

class ParentChildrenView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        # =================================================
        # STEP 1: FIND PARENT PROFILE FOR LOGGED-IN USER
        # =================================================

        parent = ParentProfile.objects.filter(
            user=request.user
        ).first()

        # =================================================
        # NO PARENT PROFILE
        # =================================================

        if not parent:
            return Response(
                {
                    "children_count": 0,
                    "children": [],
                    "message": "Parent profile not found."
                },
                status=200
            )

        # =================================================
        # STEP 2: GET ONLY THIS PARENT'S CHILDREN
        # =================================================

        children = (
            Student.objects
            .filter(parent=parent)
            .select_related(
                "parent",
                "parent__user",
                "classroom",
            )
            .order_by(
                "first_name",
                "last_name",
            )
        )

        # =================================================
        # STEP 3: SERIALIZE CHILDREN
        # =================================================

        serializer = StudentListSerializer(
            children,
            many=True,
            context={
                "request": request
            }
        )

        # =================================================
        # STEP 4: RETURN CHILDREN
        # =================================================

        return Response(
            {
                "parent_id": parent.id,
                "children_count": children.count(),
                "children": serializer.data,
            },
            status=200
        )