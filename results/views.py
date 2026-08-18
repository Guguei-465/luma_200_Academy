from django.db import transaction
from django.utils import timezone

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
<<<<<<< HEAD
from rest_framework.exceptions import PermissionDenied
=======
<<<<<<< HEAD
from rest_framework.exceptions import PermissionDenied
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
    IsTeacher,
    IsTeacherOrAcademicCoordinator,
    IsAdminOrAcademicCoordinator,
    IsAssignedTeacher,
    IsAssignedTeacherObject,
)

from .services import (
    process_result,
    process_submission,
)


# =====================================================
# GRADE SCALE
# =====================================================

class GradeScaleViewSet(viewsets.ModelViewSet):

    queryset = GradeScale.objects.all()

    serializer_class = GradeScaleSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminOrAcademicCoordinator,
    ]


# =====================================================
# ASSESSMENT TYPE
# =====================================================

class AssessmentTypeViewSet(viewsets.ModelViewSet):

    queryset = AssessmentType.objects.all()

    serializer_class = AssessmentTypeSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminOrAcademicCoordinator,
    ]


# =====================================================
# ASSESSMENT
# =====================================================

class AssessmentViewSet(viewsets.ModelViewSet):

    queryset = Assessment.objects.select_related(
        "subject",
        "classroom",
        "created_by",
    )

    serializer_class = AssessmentSerializer

    permission_classes = [
        IsAuthenticated,
        IsTeacherOrAcademicCoordinator,
    ]

    def perform_create(self, serializer):

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
        # A Teacher (as opposed to Academic Coordinator) must be
        # assigned to the classroom/subject they're creating an
        # assessment for — otherwise a teacher could fabricate
        # assessments for classes they don't teach.
        if getattr(self.request.user, "role", None) == "TEACHER":

            from assignments.models import TeacherAssignment

            classroom = serializer.validated_data.get("classroom")
            subject = serializer.validated_data.get("subject")

            is_assigned = TeacherAssignment.objects.filter(
                teacher__user=self.request.user,
                classroom=classroom,
                subject=subject,
                is_active=True,
            ).exists()

            if not is_assigned:
                raise PermissionDenied(
                    "You are not assigned to this class/subject."
                )

<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
        serializer.save(
            created_by=self.request.user
        )


# =====================================================
# LEARNING OUTCOME
# =====================================================

class LearningOutcomeViewSet(viewsets.ModelViewSet):

    queryset = LearningOutcome.objects.select_related(
        "classroom",
        "subject",
    )

    serializer_class = LearningOutcomeSerializer

    permission_classes = [
        IsAuthenticated,
        IsTeacherOrAcademicCoordinator,
    ]

# =====================================================
# REPORT COMMENTS
# =====================================================

class ReportCommentViewSet(viewsets.ModelViewSet):

    queryset = ReportComment.objects.select_related(
        "grade",
    )

    serializer_class = ReportCommentSerializer

    permission_classes = [
        IsAuthenticated,
        IsAdminOrAcademicCoordinator,
    ]


# =====================================================
# RESULT SUBMISSION
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

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
        # Same T2 assignment check for teachers creating a
        # ResultSubmission directly against an assessment.
        if getattr(self.request.user, "role", None) == "TEACHER":

            from assignments.models import TeacherAssignment

            assessment = serializer.validated_data.get("assessment")

            if assessment is not None:

                is_assigned = TeacherAssignment.objects.filter(
                    teacher__user=self.request.user,
                    classroom=assessment.classroom,
                    subject=assessment.subject,
                    is_active=True,
                ).exists()

                if not is_assigned:
                    raise PermissionDenied(
                        "You are not assigned to this class/subject."
                    )

<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
        serializer.save(
            submitted_by=self.request.user
        )

    # =================================================
    # SUBMIT
    # =================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
            IsTeacher,
        ],
    )
    def submit(self, request, pk=None):

        submission = self.get_object()

        if (
            submission.approval_status
            != ResultSubmission.ApprovalStatus.DRAFT
        ):
            return Response(
                {
                    "detail": (
                        "Only draft submissions "
                        "can be submitted."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission.approval_status = (
            ResultSubmission.ApprovalStatus.PENDING
        )

        submission.submitted_by = request.user

        submission.submitted_at = timezone.now()

        submission.save(
            update_fields=[
                "approval_status",
                "submitted_by",
                "submitted_at",
                "updated_at",
            ]
        )

        return Response(
            {
                "message": (
                    "Results submitted successfully."
                )
            },
            status=status.HTTP_200_OK,
        )

    # =================================================
    # APPROVE
    # =================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
            IsAdminOrAcademicCoordinator,
        ],
    )
    def approve(self, request, pk=None):

        submission = self.get_object()

        if (
            submission.approval_status
            != ResultSubmission.ApprovalStatus.PENDING
        ):
            return Response(
                {
                    "detail": (
                        "Only pending submissions "
                        "can be approved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():

            submission.approval_status = (
                ResultSubmission.ApprovalStatus.APPROVED
            )

            submission.approved_by = request.user

            submission.approved_at = timezone.now()

            submission.save(
                update_fields=[
                    "approval_status",
                    "approved_by",
                    "approved_at",
                    "updated_at",
                ]
            )

            # -----------------------------------------
            # Process the complete submission
            # -----------------------------------------

            process_submission(submission)

        return Response(
            {
                "message": (
                    "Results approved and processed "
                    "successfully."
                )
            },
            status=status.HTTP_200_OK,
        )

    # =================================================
    # RETURN RESULTS
    # =================================================

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
            IsAdminOrAcademicCoordinator,
        ],
    )
    def return_results(self, request, pk=None):

        submission = self.get_object()

        if (
            submission.approval_status
            != ResultSubmission.ApprovalStatus.PENDING
        ):
            return Response(
                {
                    "detail": (
                        "Only pending submissions "
                        "can be returned."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        comments = request.data.get(
            "coordinator_comments",
            "",
        )

        submission.approval_status = (
            ResultSubmission.ApprovalStatus.RETURNED
        )

        submission.coordinator_comments = comments

        submission.save(
            update_fields=[
                "approval_status",
                "coordinator_comments",
                "updated_at",
            ]
        )

        return Response(
            {
                "message": (
                    "Results returned successfully."
                )
            },
            status=status.HTTP_200_OK,
        )


# =====================================================
# RESULT
# =====================================================

class ResultViewSet(viewsets.ModelViewSet):

    queryset = Result.objects.select_related(
        "student",
        "submission",
        "submission__assessment",
        "submission__assessment__subject",
        "submission__assessment__classroom",
        "grade",
    )

    serializer_class = ResultSerializer

    permission_classes = [
        IsAuthenticated,
        IsAssignedTeacher,
    ]

    # =================================================
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
    # SECURITY HELPER
    #
    # SPEC (T2 — Marks Entry Security):
    #   "John posts marks -> Grade 2 B, Science -> 403 Forbidden"
    #
    # DRF only calls has_object_permission() for actions that
    # load an existing object (retrieve/update/destroy). It is
    # NEVER called for create/bulk, since there is no object yet.
    # IsAssignedTeacher.has_permission() only checks "is this a
    # teacher", not "is this teacher assigned to this class and
    # subject" — so without this explicit check, ANY teacher could
    # post marks for ANY class/subject. This closes that gap.
    # =================================================

    def _verify_teacher_assigned_to_submission(self, submission):

        from assignments.models import TeacherAssignment

        assessment = getattr(submission, "assessment", None)

        if assessment is None:
            raise PermissionDenied(
                "This result submission has no assessment assigned."
            )

        is_assigned = TeacherAssignment.objects.filter(
            teacher__user=self.request.user,
            classroom=assessment.classroom,
            subject=assessment.subject,
            is_active=True,
        ).exists()

        if not is_assigned:
            raise PermissionDenied(
                "You are not assigned to this class/subject."
            )

    # =================================================
<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
    # CREATE
    # =================================================

    def perform_create(self, serializer):

<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
        submission = serializer.validated_data.get("submission")

        self._verify_teacher_assigned_to_submission(submission)

<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
        result = serializer.save(
            entered_by=self.request.user,
            last_modified_by=self.request.user,
        )

        # ---------------------------------------------
        # Process immediately
        #
        # This is safe because approved submissions
        # are protected by the serializer/permissions.
        # ---------------------------------------------

        process_result(result)

    # =================================================
    # PERMISSIONS
    # =================================================

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

    # =================================================
    # UPDATE
    # =================================================

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):

        instance = self.get_object()

        if (
            instance.submission.approval_status
            == ResultSubmission.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": (
                        "Approved results "
                        "cannot be edited."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            instance,
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = serializer.save(
            last_modified_by=request.user,
        )

        process_result(result)

        return Response(
            self.get_serializer(result).data
        )

    # =================================================
    # PARTIAL UPDATE
    # =================================================

    def partial_update(
        self,
        request,
        *args,
        **kwargs,
    ):

        instance = self.get_object()

        if (
            instance.submission.approval_status
            == ResultSubmission.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": (
                        "Approved results "
                        "cannot be edited."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        result = serializer.save(
            last_modified_by=request.user,
        )

        process_result(result)

        return Response(
            self.get_serializer(result).data
        )

    # =================================================
    # DELETE
    # =================================================

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):

        instance = self.get_object()

        if (
            instance.submission.approval_status
            == ResultSubmission.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": (
                        "Approved results "
                        "cannot be deleted."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().destroy(
            request,
            *args,
            **kwargs,
        )

    # =================================================
    # BULK RESULT ENTRY
    # =================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="bulk",
        permission_classes=[
            IsAuthenticated,
            IsAssignedTeacher,
        ],
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

            submission = (
                ResultSubmission.objects
                .select_related(
                    "assessment",
                    "assessment__subject",
                    "assessment__classroom",
                )
                .get(
                    pk=data["submission"]
                )
            )

        except ResultSubmission.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Result submission "
                        "not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ---------------------------------------------
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> origin/main
        # SECURITY (T2) — see _verify_teacher_assigned_to_submission
        # above. Same gap applies here: this is the endpoint the
        # marks-entry screen actually calls, and without this check
        # any teacher could bulk-post marks for a class/subject they
        # don't teach.
        # ---------------------------------------------

        self._verify_teacher_assigned_to_submission(submission)

        # ---------------------------------------------
<<<<<<< HEAD
=======
=======
>>>>>>> 15336f206b5e6fa74b9d0088b7591925a63cc45d
>>>>>>> origin/main
        # Approved submissions are locked
        # ---------------------------------------------

        if (
            submission.approval_status
            == ResultSubmission.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": (
                        "Approved submissions "
                        "cannot be modified."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = 0
        updated = 0

        with transaction.atomic():

            for item in data["results"]:

                result, was_created = (
                    Result.objects.update_or_create(

                        submission=submission,

                        student_id=item["student"],

                        defaults={
                            "status": item["status"],
                            "marks": item.get("marks"),
                            "remarks": item.get(
                                "remarks",
                                "",
                            ),
                            "entered_by": (
                                request.user
                            ),
                            "last_modified_by": (
                                request.user
                            ),
                        },
                    )
                )

                # -------------------------------------
                # Process this result
                # -------------------------------------

                process_result(result)

                if was_created:
                    created += 1
                else:
                    updated += 1

        return Response(
            {
                "message": (
                    "Bulk results saved "
                    "successfully."
                ),
                "created": created,
                "updated": updated,
                "total": created + updated,
            },
            status=status.HTTP_200_OK,
        )


# =====================================================
# STUDENT RESULT
# =====================================================

class StudentResultViewSet(
    viewsets.ReadOnlyModelViewSet
):

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
        "subject_position",
    ]

    ordering = [
        "student__first_name",
    ]


# =====================================================
# STUDENT TERM RESULT
# =====================================================

class StudentTermResultViewSet(
    viewsets.ReadOnlyModelViewSet
):

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

    # =================================================
    # REPORT CARD
    # =================================================

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def report_card(
        self,
        request,
        pk=None,
    ):

        term_result = self.get_object()

        subject_results = (
            StudentResult.objects
            .filter(
                student=term_result.student,
                classroom=term_result.classroom,
                term=term_result.term,
                academic_year=term_result.academic_year,
            )
            .select_related(
                "subject",
                "grade",
            )
        )

        serializer = StudentResultSerializer(
            subject_results,
            many=True,
        )

        return Response(
            {
                "student": str(
                    term_result.student
                ),

                "classroom": str(
                    term_result.classroom
                ),

                "term": term_result.term,

                "academic_year": (
                    term_result.academic_year
                ),

                "overall_grade": (
                    term_result.overall_grade.level
                    if term_result.overall_grade
                    else None
                ),

                "cbc_code": (
                    term_result.cbc_code
                ),

                "cbc_description": (
                    term_result.cbc_description
                ),

                "total_marks": (
                    term_result.total_marks
                ),

                "average_marks": (
                    term_result.average_marks
                ),

                "position": (
                    term_result.position
                ),

                "total_subjects": (
                    term_result.total_subjects
                ),

                "attendance_percentage": (
                    term_result.attendance_percentage
                ),

                "class_teacher_comment": (
                    term_result.class_teacher_comment
                ),

                "headteacher_comment": (
                    term_result.headteacher_comment
                ),

                "subjects": serializer.data,
            }
        )


# =====================================================
# STUDENT REPORT CARD API
# =====================================================

class StudentReportCardAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        student_id,
        academic_year,
        term,
    ):

        try:

            student = Student.objects.select_related(
                "classroom"
            ).get(
                pk=student_id
            )

        except Student.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Student not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # ---------------------------------------------
        # Subject results
        # ---------------------------------------------

        subjects = (
            StudentResult.objects
            .filter(
                student=student,
                academic_year=academic_year,
                term=term,
            )
            .select_related(
                "subject",
                "grade",
                "classroom",
            )
            .order_by(
                "subject__name"
            )
        )

        # ---------------------------------------------
        # Overall term result
        # ---------------------------------------------

        try:

            summary = (
                StudentTermResult.objects
                .select_related(
                    "overall_grade",
                    "classroom",
                )
                .get(
                    student=student,
                    academic_year=academic_year,
                    term=term,
                )
            )

        except StudentTermResult.DoesNotExist:

            summary = None

        # ---------------------------------------------
        # Student information
        # ---------------------------------------------

        student_data = {
            "id": student.id,

            "name": str(student),

            "admission_number": (
                getattr(
                    student,
                    "admission_number",
                    getattr(
                        student,
                        "admission_no",
                        None,
                    ),
                )
            ),

            "assessment_number": (
                getattr(
                    student,
                    "assessment_number",
                    None,
                )
            ),

            "classroom": (
                str(student.classroom)
                if getattr(
                    student,
                    "classroom",
                    None,
                )
                else None
            ),
        }

        # ---------------------------------------------
        # Subject information
        # ---------------------------------------------

        subject_data = []

        for item in subjects:

            subject_data.append(
                {
                    "id": item.id,

                    "subject": (
                        item.subject.name
                    ),

                    "total_score": (
                        item.total_score
                    ),

                    "average_score": (
                        item.average_score
                    ),

                    "grade": (
                        item.grade.level
                        if item.grade
                        else None
                    ),

                    "cbc_code": (
                        item.cbc_code
                    ),

                    "cbc_description": (
                        item.cbc_description
                    ),

                    "subject_position": (
                        item.subject_position
                    ),

                    "highest_score": (
                        item.highest_score
                    ),

                    "lowest_score": (
                        item.lowest_score
                    ),

                    "class_average": (
                        item.class_average
                    ),

                    "learners_assessed": (
                        item.learners_assessed
                    ),

                    "teacher_comment": (
                        item.teacher_comment
                    ),
                }
            )

        # ---------------------------------------------
        # Summary
        # ---------------------------------------------

        summary_data = None

        if summary:

            summary_data = {
                "total_marks": (
                    summary.total_marks
                ),

                "average_marks": (
                    summary.average_marks
                ),

                "overall_grade": (
                    summary.overall_grade.level
                    if summary.overall_grade
                    else None
                ),

                "cbc_code": (
                    summary.cbc_code
                ),

                "cbc_description": (
                    summary.cbc_description
                ),

                "position": (
                    summary.position
                ),

                "total_subjects": (
                    summary.total_subjects
                ),

                "attendance_percentage": (
                    summary.attendance_percentage
                ),

                "class_teacher_comment": (
                    summary.class_teacher_comment
                ),

                "headteacher_comment": (
                    summary.headteacher_comment
                ),
            }

        return Response(
            {
                "student": student_data,

                "academic_year": (
                    academic_year
                ),

                "term": term,

                "subjects": subject_data,

                "summary": summary_data,
            },
            status=status.HTTP_200_OK,
        )