from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import status

from accounts.models import CustomUser, ParentProfile, TeacherProfile
from accounts.serializers import UserSerializer

from students.models import Student, StudentTransfer
from students.serializers import (
    StudentSerializer,
    StudentListSerializer,
    StudentTransferSerializer,
)


# =====================================================
# SECURITY
# =====================================================

class IsAdminOrCoordinatorForStudents(BasePermission):
    """
    Student records are managed by Super Admin /
    Academic Coordinator only.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in [
                CustomUser.Role.SUPER_ADMIN,
                CustomUser.Role.ACADEMIC_COORDINATOR,
            ]
        )


def _teacher_classroom_ids(user):
    """
    Return classroom IDs that this teacher is actively
    assigned to teach.
    """

    from assignments.models import TeacherAssignment

    try:
        teacher_profile = user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return []

    return list(
        TeacherAssignment.objects.filter(
            teacher=teacher_profile,
            is_active=True,
        ).values_list(
            "classroom_id",
            flat=True,
        )
    )


# =====================================================
# STUDENT LIST
# GET /api/students/
# =====================================================

class StudentListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        base_qs = Student.objects.select_related(
            "parent__user",
            "classroom",
        )

        # ---------------------------------------------
        # SUPER ADMIN / ACADEMIC COORDINATOR / ACCOUNTANT
        # ---------------------------------------------

        if user.role in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
            CustomUser.Role.ACCOUNTANT,
        ]:
            students = base_qs.all()

        # ---------------------------------------------
        # TEACHER
        # ---------------------------------------------

        elif user.role == CustomUser.Role.TEACHER:
            students = base_qs.filter(
                classroom_id__in=_teacher_classroom_ids(user)
            )

        # ---------------------------------------------
        # PARENT
        # ---------------------------------------------

        elif user.role == CustomUser.Role.PARENT:

            parent_profile = ParentProfile.objects.filter(
                user=user
            ).first()

            if parent_profile:
                students = base_qs.filter(
                    parent=parent_profile
                )
            else:
                students = Student.objects.none()

        # ---------------------------------------------
        # UNKNOWN ROLE
        # ---------------------------------------------

        else:
            students = Student.objects.none()

        # =================================================
        # FILTERS
        # =================================================

        classroom_id = request.query_params.get("classroom")
        status_param = request.query_params.get("status")
        gender_param = request.query_params.get("gender")
        search = request.query_params.get("search")

        if classroom_id:
            students = students.filter(
                classroom_id=classroom_id
            )

        if status_param:
            students = students.filter(
                status=status_param
            )

        if gender_param:
            students = students.filter(
                gender=gender_param
            )

        if search:
            students = students.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(admission_number__icontains=search)
                | Q(assessment_number__icontains=search)
            )

        serializer = StudentListSerializer(
            students,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data)


# =====================================================
# STUDENT DETAIL
# GET /api/students/<pk>/
# =====================================================

class StudentDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        student = get_object_or_404(
            Student.objects.select_related(
                "parent__user",
                "classroom",
            ),
            pk=pk,
        )

        user = request.user

        # ---------------------------------------------
        # ADMIN / COORDINATOR / ACCOUNTANT
        # ---------------------------------------------

        allowed = user.role in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
            CustomUser.Role.ACCOUNTANT,
        ]

        # ---------------------------------------------
        # TEACHER
        # ---------------------------------------------

        if not allowed and user.role == CustomUser.Role.TEACHER:
            allowed = (
                student.classroom_id
                in _teacher_classroom_ids(user)
            )

        # ---------------------------------------------
        # PARENT
        # ---------------------------------------------

        if not allowed and user.role == CustomUser.Role.PARENT:

            parent_profile = ParentProfile.objects.filter(
                user=user
            ).first()

            allowed = bool(
                parent_profile
                and student.parent_id == parent_profile.id
            )

        if not allowed:
            return Response(
                {
                    "error": (
                        "You do not have permission to view "
                        "this student."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudentSerializer(
            student,
            context={"request": request},
        )

        return Response(serializer.data)


# =====================================================
# CREATE STUDENT
# POST /api/students/create/
# =====================================================

class StudentCreateView(APIView):

    permission_classes = [
        IsAdminOrCoordinatorForStudents
    ]

    def post(self, request):

        serializer = StudentSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        student = serializer.save()

        return Response(
            StudentSerializer(
                student,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


# =====================================================
# UPDATE STUDENT
# PUT/PATCH /api/students/update/<pk>/
# =====================================================

class StudentUpdateView(APIView):

    permission_classes = [
        IsAdminOrCoordinatorForStudents
    ]

    def put(self, request, pk):

        student = get_object_or_404(
            Student,
            pk=pk,
        )

        serializer = StudentSerializer(
            student,
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        student = serializer.save()

        return Response(
            StudentSerializer(
                student,
                context={"request": request},
            ).data
        )

    def patch(self, request, pk):

        student = get_object_or_404(
            Student,
            pk=pk,
        )

        serializer = StudentSerializer(
            student,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        student = serializer.save()

        return Response(
            StudentSerializer(
                student,
                context={"request": request},
            ).data
        )


# =====================================================
# DELETE STUDENT
# DELETE /api/students/delete/<pk>/
# =====================================================

class StudentDeleteView(APIView):

    permission_classes = [
        IsAdminOrCoordinatorForStudents
    ]

    def delete(self, request, pk):

        student = get_object_or_404(
            Student,
            pk=pk,
        )

        student.delete()

        return Response(
            {
                "message": "Student deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT,
        )


# =====================================================
# STUDENT TRANSFER
# POST /api/students/transfer/
# =====================================================

class StudentTransferView(APIView):

    permission_classes = [
        IsAdminOrCoordinatorForStudents
    ]

    @transaction.atomic
    def post(self, request):

        serializer = StudentTransferSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        transfer = serializer.save(
            transferred_by=request.user
        )

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
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


# =====================================================
# TRANSFER LIST
# GET /api/students/transfers/
# =====================================================

class StudentTransferListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
            CustomUser.Role.ACCOUNTANT,
        ]:
            return Response(
                {
                    "error": (
                        "You do not have permission "
                        "to view transfers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        transfers = (
            StudentTransfer.objects
            .select_related(
                "student",
                "from_classroom",
                "to_classroom",
                "transferred_by",
            )
            .all()
        )

        serializer = StudentTransferSerializer(
            transfers,
            many=True,
            context={"request": request},
        )

        return Response(serializer.data)


# =====================================================
# TRANSFER DETAIL
# GET /api/students/transfers/<pk>/
# =====================================================

class StudentTransferDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):

        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
            CustomUser.Role.ACCOUNTANT,
        ]:
            return Response(
                {
                    "error": (
                        "You do not have permission "
                        "to view transfers."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        transfer = get_object_or_404(
            StudentTransfer.objects.select_related(
                "student",
                "from_classroom",
                "to_classroom",
                "transferred_by",
            ),
            pk=pk,
        )

        serializer = StudentTransferSerializer(
            transfer,
            context={"request": request},
        )

        return Response(serializer.data)


# =====================================================
# PARENT CHILDREN
# GET /api/students/parent/children/
# =====================================================

class ParentChildrenView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        parent = ParentProfile.objects.filter(
            user=request.user
        ).first()

        if not parent:
            return Response(
                {
                    "children_count": 0,
                    "children": [],
                    "message": "Parent profile not found.",
                },
                status=status.HTTP_200_OK,
            )

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

        serializer = StudentListSerializer(
            children,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "parent_id": parent.id,
                "children_count": children.count(),
                "children": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# =====================================================
# MY STUDENT RECORD
# GET /api/students/me/
# =====================================================

class MyStudentRecordView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        if user.role != CustomUser.Role.STUDENT:
            return Response(
                {
                    "error": (
                        "This endpoint is only for "
                        "student accounts."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        student = (
            Student.objects
            .select_related(
                "parent__user",
                "classroom",
                "classroom__class_teacher__user",
            )
            .filter(user=user)
            .first()
        )

        if not student:
            return Response(
                {
                    "linked": False,
                    "message": (
                        "Your login account has not been "
                        "linked to a classroom yet. Please "
                        "contact the academic coordinator."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        serializer = StudentSerializer(
            student,
            context={"request": request},
        )

        data = serializer.data
        data["linked"] = True

        return Response(
            data,
            status=status.HTTP_200_OK,
        )


# =====================================================
# UNLINKED STUDENT LOGIN ACCOUNTS
# GET /api/students/unlinked-users/
# =====================================================

class UnlinkedStudentUsersView(APIView):

    permission_classes = [
        IsAdminOrCoordinatorForStudents
    ]

    def get(self, request):

        users = (
            CustomUser.objects
            .filter(
                role=CustomUser.Role.STUDENT,
                student_record__isnull=True,
            )
            .order_by(
                "first_name",
                "last_name",
                "username",
            )
        )

        serializer = UserSerializer(
            users,
            many=True,
        )

        return Response(serializer.data)