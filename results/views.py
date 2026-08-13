from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import APIView, action
from rest_framework.response import Response
from accounts import serializers
from students.models import Student
from .models import (
    GradeScale,
    AssessmentType,
    Assessment,
    LearningOutcome,
    ResultSubmission,
    Result,
    StudentResult,
    StudentTermResult,
    ReportComment,
)

from .serializers import (
    BulkResultSerializer,
    GradeScaleSerializer,
    AssessmentTypeSerializer,
    AssessmentSerializer,
    LearningOutcomeSerializer,
    ResultSubmissionSerializer,
    ResultSerializer,
    StudentResultSerializer,
    StudentTermResultSerializer,
    ReportCommentSerializer,
)

from .permissions import (
    IsSuperAdmin,
    IsAcademicCoordinator,
    IsTeacher,
    IsTeacherOrAcademicCoordinator,
    IsAdminOrAcademicCoordinator,
    IsAssignedTeacher,
    IsAssignedTeacherObject,
)
from rest_framework import filters


# =====================================================
# Grade Scale
# =====================================================
class GradeScaleViewSet(viewsets.ModelViewSet):

    queryset = GradeScale.objects.all()
    serializer_class = GradeScaleSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminOrAcademicCoordinator,
    ]

# =====================================================
# Assessment Types
# =====================================================
class AssessmentTypeViewSet(viewsets.ModelViewSet):

    queryset = AssessmentType.objects.all()
    serializer_class = AssessmentTypeSerializer
    permission_classes = [
        IsAuthenticated,
        IsAdminOrAcademicCoordinator,
    ]

# =====================================================
# Assessment
# =====================================================
class AssessmentViewSet(viewsets.ModelViewSet):
    queryset = Assessment.objects.select_related(
        "subject",
        "classroom",
        "created_by"
    )
    serializer_class = AssessmentSerializer

    permission_classes = [
        IsAuthenticated,
        IsTeacherOrAcademicCoordinator,
    ]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user
        )

# =====================================================
# Report Comments
# =====================================================
class ReportCommentViewSet(viewsets.ModelViewSet):

    queryset = ReportComment.objects.select_related(
        "grade"
    )

    serializer_class = ReportCommentSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminOrAcademicCoordinator,
    ]

# =====================================================
# Result Submission
# =====================================================
class ResultSubmissionViewSet(viewsets.ModelViewSet):

    queryset = ResultSubmission.objects.select_related(
        "assessment",
        "submitted_by",
        "approved_by",
    )

    serializer_class = ResultSubmissionSerializer

    permission_classes = [
        IsAuthenticated,
        IsTeacherOrAcademicCoordinator,
    ]

    def perform_create(self, serializer):
        serializer.save(
            submitted_by=self.request.user
        )

    # ------------------------------------------
    # Submit Results
    # ------------------------------------------
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
            IsTeacher,
        ]
    )
    def submit(self, request, pk=None):

        submission = self.get_object()

        if submission.approval_status != ResultSubmission.ApprovalStatus.DRAFT:
            return Response(
                {
                    "detail": "Only draft submissions can be submitted."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission.approval_status = ResultSubmission.ApprovalStatus.PENDING
        submission.submitted_by = request.user
        submission.submitted_at = timezone.now()

        submission.save()

        return Response(
            {
                "message": "Results submitted successfully."
            }
        )

    # ------------------------------------------
    # Approve Results
    # ------------------------------------------
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
            IsAdminOrAcademicCoordinator,
        ]
    )
    def approve(self, request, pk=None):

        submission = self.get_object()

        if submission.approval_status != ResultSubmission.ApprovalStatus.PENDING:
            return Response(
                {
                    "detail": "Only pending submissions can be approved."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission.approval_status = ResultSubmission.ApprovalStatus.APPROVED
        submission.approved_by = request.user
        submission.approved_at = timezone.now()

        submission.save()

        return Response(
            {
                "message": "Results approved successfully."
            }
        )

    # ------------------------------------------
    # Return Results
    # ------------------------------------------
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
            IsAdminOrAcademicCoordinator,
        ]
    )
    def return_results(self, request, pk=None):

        submission = self.get_object()

        comments = request.data.get(
            "coordinator_comments",
            ""
        )

        submission.approval_status = ResultSubmission.ApprovalStatus.RETURNED
        submission.coordinator_comments = comments

        submission.save()

        return Response(
            {
                "message": "Results returned successfully."
            }
        )
    
# =====================================================
# Result
# =====================================================
class ResultViewSet(viewsets.ModelViewSet):

    queryset = Result.objects.select_related(
        "student",
        "submission",
        "grade",
    )

    serializer_class = ResultSerializer

    permission_classes = [
        IsAuthenticated,
        IsAssignedTeacher,
    ]

    def perform_create(self, serializer):
        serializer.save(
            entered_by=self.request.user
        )

    def get_permissions(self):

        if self.action in [
            "update",
            "partial_update",
            "destroy",
        ]:
            return [
                IsAuthenticated(),
                IsAssignedTeacherObject(),
            ]

        return super().get_permissions()

    def update(self, request, *args, **kwargs):

        instance = self.get_object()

        if (
            instance.submission.approval_status
            == ResultSubmission.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": "Approved results cannot be edited."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):

        instance = self.get_object()

        if (
            instance.submission.approval_status
            == ResultSubmission.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": "Approved results cannot be deleted."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(request, *args, **kwargs)

    # =====================================================
    # Bulk Result Entry
    # =====================================================
    @action(
        detail=False,
        methods=["post"],
        url_path="bulk",
        permission_classes=[
            IsAuthenticated,
            IsAssignedTeacher,
        ]
    )
    def bulk(self, request):

        serializer = BulkResultSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        try:
            submission = ResultSubmission.objects.get(
                pk=data["submission"]
            )
        except ResultSubmission.DoesNotExist:
            return Response(
                {
                    "detail": "Result submission not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            submission.approval_status
            == ResultSubmission.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": "Approved submissions cannot be modified."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = 0
        updated = 0

        with transaction.atomic():

            for item in data["results"]:

                _, was_created = Result.objects.update_or_create(

                    submission=submission,
                    student_id=item["student"],

                    defaults={
                        "status": item["status"],
                        "marks": item.get("marks"),
                        "remarks": item.get("remarks", ""),
                        "entered_by": request.user,
                    }
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

        return Response(
            {
                "message": "Bulk results saved successfully.",
                "created": created,
                "updated": updated,
                "total": created + updated,
            },
            status=status.HTTP_200_OK,
        )


# =====================================================
# Student Result
# =====================================================
class StudentResultViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = StudentResult.objects.select_related(
        "student",
        "subject",
        "grade",
        "classroom",
    )

    serializer_class = StudentResultSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "student__first_name",
        "student__last_name",
        "student__admission_no",
        "subject__name",
    ]

    ordering_fields = [
        "average_score",
        "total_score",
    ]

    ordering = [
        "student__first_name",
    ]

# =====================================================
# Student Term Result
# =====================================================
class StudentTermResultViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = StudentTermResult.objects.select_related(
        "student",
        "classroom",
        "overall_grade",
    )

    serializer_class = StudentTermResultSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        "student__first_name",
        "student__last_name",
        "student__admission_no",
    ]

    ordering_fields = [
        "average_marks",
        "position",
    ]

    ordering = [
        "position",
    ]

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def report_card(self, request, pk=None):

        term_result = self.get_object()

        subject_results = StudentResult.objects.filter(
            student=term_result.student,
            classroom=term_result.classroom,
            term=term_result.term,
            academic_year=term_result.academic_year,
        ).select_related(
            "subject",
            "grade",
        )

        serializer = StudentResultSerializer(
            subject_results,
            many=True,
        )

        return Response(
            {
                "student": str(term_result.student),
                "classroom": str(term_result.classroom),
                "term": term_result.term,
                "academic_year": term_result.academic_year,
                "overall_grade": (
                    term_result.overall_grade.level
                    if term_result.overall_grade
                    else None
                ),
                "average_marks": term_result.average_marks,
                "position": term_result.position,
                "subjects": serializer.data,
            }
        )


class LearningOutcomeViewSet(viewsets.ModelViewSet):
    queryset = LearningOutcome.objects.all()
    serializer_class = LearningOutcomeSerializer

class StudentReportCardAPIView(APIView):

    def get(self, request, student_id, academic_year, term):

        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {
                    "detail": "Student not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        subjects = StudentResult.objects.filter(
            student=student,
            academic_year=academic_year,
            term=term,
        ).select_related(
            "subject",
            "grade",
        )

        try:
            summary = StudentTermResult.objects.select_related(
                "overall_grade"
            ).get(
                student=student,
                academic_year=academic_year,
                term=term,
            )
        except StudentTermResult.DoesNotExist:
            summary = None

        data = {
            "student": {
                "id": student.id,
                "name": str(student),
                "admission_number": student.admission_number,
                "assessment_number": student.assessment_number,
                "classroom": str(student.classroom),
            },

            "subjects": [

                {
                    "subject": item.subject.name,
                    "total_score": item.total_score,
                    "average_score": item.average_score,
                    "grade": item.grade.level if item.grade else None,
                    "cbc_code": item.cbc_code,
                    "cbc_description": item.cbc_description,
                    "teacher_comment": item.teacher_comment,
                }

                for item in subjects
            ],

            "summary": None if summary is None else {

                "total_marks": summary.total_marks,
                "average_marks": summary.average_marks,
                "overall_grade": summary.overall_grade.level if summary.overall_grade else None,
                "position": summary.position,
                "total_subjects": summary.total_subjects,
                "attendance_percentage": summary.attendance_percentage,
                "class_teacher_comment": summary.class_teacher_comment,
                "headteacher_comment": summary.headteacher_comment,
            }
        }

        return Response(data)
