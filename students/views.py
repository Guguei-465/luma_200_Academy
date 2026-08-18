from django.db import transaction
<<<<<<< HEAD
from django.db.models import Q
=======
<<<<<<< HEAD
from django.db.models import Q
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework import status

from accounts.models import CustomUser, ParentProfile, TeacherProfile
<<<<<<< HEAD
from accounts.serializers import UserSerializer
=======
=======
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.models import ParentProfile
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
from students.models import Student, StudentTransfer
from students.serializers import (
    StudentSerializer,
    StudentListSerializer,
    StudentTransferSerializer,
)


# =====================================================
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
# SECURITY
#
# None of the views below had ANY role restriction before —
# only IsAuthenticated. That meant any logged-in user of any
# role (including Parent) could list/view every student in the
# school, and could create/update/DELETE any student record.
# This directly violates the spec's role permission table
# ("Parent: ALL writes forbidden", "Teacher: cannot write
# Students") so every view here now enforces roles explicitly.
# =====================================================

class IsAdminOrCoordinatorForStudents(BasePermission):
    """
    Student records are managed by Super Admin / Academic
    Coordinator only — matches the spec's permission table.
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
    """Classroom IDs this teacher has an active assignment in."""

    from assignments.models import TeacherAssignment

    try:
        teacher_profile = user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return []

    return list(
        TeacherAssignment.objects.filter(
            teacher=teacher_profile,
            is_active=True,
        ).values_list("classroom_id", flat=True)
    )


# =====================================================
<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
# STUDENT LIST
# GET /api/students/
# =====================================================

class StudentListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
        user = request.user

        base_qs = Student.objects.select_related(
            "parent__user",
            "classroom",
        )

        if user.role in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
            CustomUser.Role.ACCOUNTANT,
        ]:
            students = base_qs.all()

        elif user.role == CustomUser.Role.TEACHER:
            students = base_qs.filter(
                classroom_id__in=_teacher_classroom_ids(user)
            )

        elif user.role == CustomUser.Role.PARENT:
            parent_profile = ParentProfile.objects.filter(
                user=user
            ).first()
            students = (
                base_qs.filter(parent=parent_profile)
                if parent_profile
                else Student.objects.none()
            )

        else:
            students = Student.objects.none()
<<<<<<< HEAD

        # =============================================
        # QUERY-PARAM FILTERS
        #
        # Same filtering shape used everywhere else in the
        # app (?classroom=<id>, ?status=, ?gender=, ?search=)
        # so every "students" screen — admin, coordinator,
        # teacher — can filter consistently.
        # =============================================

        classroom_id = request.query_params.get("classroom")
        status_param = request.query_params.get("status")
        gender_param = request.query_params.get("gender")
        search = request.query_params.get("search")

        if classroom_id:
            students = students.filter(classroom_id=classroom_id)

        if status_param:
            students = students.filter(status=status_param)

        if gender_param:
            students = students.filter(gender=gender_param)

        if search:
            students = students.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(admission_number__icontains=search)
                | Q(assessment_number__icontains=search)
            )
=======
=======
        students = Student.objects.select_related(
            "parent__user",
            "classroom",
        ).all()
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main

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

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
        user = request.user

        allowed = user.role in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
            CustomUser.Role.ACCOUNTANT,
        ]

        if not allowed and user.role == CustomUser.Role.TEACHER:
            allowed = student.classroom_id in _teacher_classroom_ids(user)

        if not allowed and user.role == CustomUser.Role.PARENT:
            parent_profile = ParentProfile.objects.filter(
                user=user
            ).first()
            allowed = bool(
                parent_profile and student.parent_id == parent_profile.id
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

<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
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

<<<<<<< HEAD
    permission_classes = [IsAdminOrCoordinatorForStudents]
=======
<<<<<<< HEAD
    permission_classes = [IsAdminOrCoordinatorForStudents]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main

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

<<<<<<< HEAD
    permission_classes = [IsAdminOrCoordinatorForStudents]
=======
<<<<<<< HEAD
    permission_classes = [IsAdminOrCoordinatorForStudents]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main

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

<<<<<<< HEAD
    permission_classes = [IsAdminOrCoordinatorForStudents]
=======
<<<<<<< HEAD
    permission_classes = [IsAdminOrCoordinatorForStudents]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main

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

<<<<<<< HEAD
    permission_classes = [IsAdminOrCoordinatorForStudents]
=======
<<<<<<< HEAD
    permission_classes = [IsAdminOrCoordinatorForStudents]
=======
    permission_classes = [IsAuthenticated]
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main

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

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
            CustomUser.Role.ACCOUNTANT,
        ]:
            return Response(
                {"error": "You do not have permission to view transfers."},
                status=status.HTTP_403_FORBIDDEN,
            )

<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
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

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
            CustomUser.Role.ACCOUNTANT,
        ]:
            return Response(
                {"error": "You do not have permission to view transfers."},
                status=status.HTTP_403_FORBIDDEN,
            )

<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
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
<<<<<<< HEAD
        )

# =====================================================
# MY STUDENT RECORD  (logged-in STUDENT role)
# GET /api/students/me/
#
# This is the endpoint the STUDENT-facing dashboard should
# call to find out its own classroom, class teacher, parent
# link, etc. Previously nothing connected a STUDENT login
# (CustomUser + StudentProfile) to the academic Student
# record (classroom, parent) — so a logged-in student had no
# way to ask "what class am I in", which is exactly the
# "student not assigned to class" symptom.
# =====================================================

class MyStudentRecordView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        if user.role != CustomUser.Role.STUDENT:
            return Response(
                {"error": "This endpoint is only for student accounts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        student = Student.objects.select_related(
            "parent__user",
            "classroom",
            "classroom__class_teacher__user",
        ).filter(user=user).first()

        if not student:
            return Response(
                {
                    "linked": False,
                    "message": (
                        "Your login account has not been linked to a "
                        "classroom yet. Please contact the academic "
                        "coordinator."
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

        return Response(data, status=status.HTTP_200_OK)


# =====================================================
# UNLINKED STUDENT LOGIN ACCOUNTS
# GET /api/students/unlinked-users/
#
# Returns CustomUser accounts with role=STUDENT that do NOT
# yet have a matching academic Student record. Used to
# populate the "link to existing login account" dropdown on
# the Add/Edit Student screen, instead of leaving that
# relationship to be guessed/duplicated by hand.
# =====================================================

class UnlinkedStudentUsersView(APIView):

    permission_classes = [IsAdminOrCoordinatorForStudents]

    def get(self, request):

        users = CustomUser.objects.filter(
            role=CustomUser.Role.STUDENT,
            student_record__isnull=True,
        ).order_by("first_name", "last_name", "username")

        serializer = UserSerializer(users, many=True)

        return Response(serializer.data)
=======
        )
>>>>>>> origin/main
