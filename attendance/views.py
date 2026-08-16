from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import CustomUser, TeacherProfile
from assignments.models import TeacherAssignment
from notifiations.services import create_notification

from students.models import Student

from attendance.models import Attendance, AttendanceSubmission

from attendance.serializers import (
    BulkAttendanceSerializer,
    CreateAttendanceSubmissionSerializer,
    AttendanceDetailSerializer,
    StudentAttendanceHistorySerializer,
)

from attendance.permissions import IsAssignedClassTeacher


# ============================================================
# APPROVAL STATUS HELPERS
# ============================================================
#
# Your AttendanceSubmission model does not have:
#
# AttendanceSubmission.ApprovalStatus
#
# So we safely get the actual database value from the model's
# approval_status field choices.
#
# This keeps the views compatible with your existing model.
# ============================================================

def get_approval_status_value(label):
    """
    Return the actual database value for an approval_status label.

    Example:
        get_approval_status_value("Draft")
        get_approval_status_value("Approved")
        get_approval_status_value("Returned")
        get_approval_status_value("Pending")
    """

    try:
        field = AttendanceSubmission._meta.get_field("approval_status")

        choices = field.choices or []

        for value, choice_label in choices:
            if str(choice_label).strip().lower() == str(label).strip().lower():
                return value

            if str(value).strip().lower() == str(label).strip().lower():
                return value

    except Exception:
        pass

    # Fallback to the values your current system has been using.
    return label


DRAFT_STATUS = get_approval_status_value("Draft")
RETURNED_STATUS = get_approval_status_value("Returned")
APPROVED_STATUS = get_approval_status_value("Approved")
PENDING_STATUS = get_approval_status_value("Pending")


# ============================================================
# SAFE TEACHER PROFILE
# ============================================================

def get_teacher_profile(request):
    """
    Safely return the logged-in teacher profile.
    """

    try:
        return request.user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return None


# ============================================================
# MARK ATTENDANCE
# ============================================================

class MarkAttendanceView(APIView):
    """
    GET:
        Load students for a class-teacher assignment.

    POST:
        Save attendance.

    IMPORTANT:
        Attendance is controlled by the class-teacher assignment.
        TeacherAssignment logic is NOT changed.
    """

    permission_classes = [IsAssignedClassTeacher]

    # ========================================================
    # GET — LOAD STUDENTS
    # ========================================================

    @transaction.atomic
    def get(self, request):

        assignment_id = request.query_params.get("assignment")

        if not assignment_id:
            return Response(
                {
                    "error": "Assignment is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Get assignment
        # ----------------------------------------------------

        assignment = get_object_or_404(
            TeacherAssignment.objects.select_related(
                "teacher",
                "classroom",
                "subject",
            ),
            pk=assignment_id,
        )

        # ----------------------------------------------------
        # Get teacher profile
        # ----------------------------------------------------

        teacher_profile = get_teacher_profile(request)

        if not teacher_profile:
            return Response(
                {
                    "error": "Only teachers can access attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify teacher owns assignment
        # ----------------------------------------------------

        if assignment.teacher_id != teacher_profile.id:

            return Response(
                {
                    "error": "You are not assigned to this teaching assignment."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Attendance is only marked through the class-teacher
        # assignment.
        # ----------------------------------------------------

        if not assignment.is_class_teacher:

            return Response(
                {
                    "error": (
                        "You are not the class teacher for this classroom."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Assignment must be active
        # ----------------------------------------------------

        if not assignment.is_active:

            return Response(
                {
                    "error": "This assignment is inactive."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Today's date
        # ----------------------------------------------------

        today = timezone.localdate()

        # ----------------------------------------------------
        # Create or get attendance submission
        # ----------------------------------------------------

        submission, created = AttendanceSubmission.objects.get_or_create(

            assignment=assignment,

            date=today,

            defaults={
                "classroom": assignment.classroom,
                "submitted_by": request.user,
                "approval_status": DRAFT_STATUS,
            },
        )

        # ----------------------------------------------------
        # If an existing submission belongs to another
        # classroom, protect against inconsistent data.
        # ----------------------------------------------------

        if submission.classroom_id != assignment.classroom_id:

            submission.classroom = assignment.classroom
            submission.save(
                update_fields=["classroom"]
            )

        # ----------------------------------------------------
        # Get students
        # ----------------------------------------------------

        students = (
            Student.objects
            .filter(classroom=assignment.classroom)
            .order_by(
                "admission_number",
                "first_name",
                "last_name",
            )
        )

        records = []

        # ----------------------------------------------------
        # Create attendance rows if necessary
        # ----------------------------------------------------

        for student in students:

            attendance, _ = Attendance.objects.get_or_create(

                submission=submission,

                student=student,

                defaults={
                    "status": Attendance.Status.PRESENT,
                    "remarks": "",
                },
            )

            records.append(
                {
                    "id": attendance.id,
                    "student": student.id,
                    "admission_number": student.admission_number,
                    "name": (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    ).strip(),
                    "status": attendance.status,
                    "remarks": attendance.remarks or "",
                }
            )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return Response(
            {
                "submission": submission.id,
                "assignment": assignment.id,
                "classroom": str(assignment.classroom),
                "classroom_id": assignment.classroom_id,
                "subject": (
                    assignment.subject.name
                    if assignment.subject
                    else ""
                ),
                "subject_id": assignment.subject_id,
                "date": submission.date,
                "created": created,
                "is_class_teacher": assignment.is_class_teacher,
                "students": records,
            },
            status=status.HTTP_200_OK,
        )

    # ========================================================
    # POST — SAVE ATTENDANCE
    # ========================================================

    @transaction.atomic
    def post(self, request):

        serializer = BulkAttendanceSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        submission = get_object_or_404(

            AttendanceSubmission.objects
            .select_for_update()
            .select_related(
                "assignment",
                "classroom",
                "assignment__teacher",
            ),

            pk=serializer.validated_data["submission"],
        )

        # ----------------------------------------------------
        # Teacher profile
        # ----------------------------------------------------

        teacher_profile = get_teacher_profile(request)

        if not teacher_profile:

            return Response(
                {
                    "error": "Only teachers can save attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify assignment teacher
        # ----------------------------------------------------

        if (
            not submission.assignment
            or submission.assignment.teacher_id
            != teacher_profile.id
        ):

            return Response(
                {
                    "error": (
                        "This attendance submission does not "
                        "belong to you."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify class teacher
        # ----------------------------------------------------

        if not submission.assignment.is_class_teacher:

            return Response(
                {
                    "error": (
                        "Only the class teacher can save "
                        "attendance for this class."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify active assignment
        # ----------------------------------------------------

        if not submission.assignment.is_active:

            return Response(
                {
                    "error": "This assignment is inactive."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Check approval status
        # ----------------------------------------------------

        if submission.approval_status not in [
            DRAFT_STATUS,
            RETURNED_STATUS,
        ]:

            return Response(
                {
                    "error": (
                        "Attendance has already been finalized."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Teacher name
        # ----------------------------------------------------

        teacher_name = (
            request.user.get_full_name()
            or request.user.username
        )

        attendance_date = submission.date

        # ----------------------------------------------------
        # Save attendance records
        # ----------------------------------------------------

        for record in serializer.validated_data["records"]:

            student = get_object_or_404(
                Student,
                pk=record["student"],
            )

            # ------------------------------------------------
            # SECURITY:
            #
            # Student must belong to the classroom attached
            # to this attendance submission.
            # ------------------------------------------------

            if student.classroom_id != submission.classroom_id:

                return Response(
                    {
                        "error": (
                            f"{student.first_name} "
                            f"{student.last_name} does not "
                            "belong to this classroom."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            attendance, _ = (
                Attendance.objects.update_or_create(

                    submission=submission,

                    student=student,

                    defaults={
                        "status": record["status"],
                        "remarks": (
                            record.get("remarks", "")
                            or ""
                        ),
                    },
                )
            )

            # =================================================
            # NOTIFY PARENT
            # =================================================

            parent_user = None

            try:

                if hasattr(student, "parent") and student.parent:

                    parent_user = getattr(
                        student.parent,
                        "user",
                        None,
                    )

            except Exception:

                parent_user = None

            # ------------------------------------------------
            # Send notification
            # ------------------------------------------------

            if parent_user:

                title = (
                    f"Attendance: "
                    f"{student.first_name} — "
                    f"{attendance.status}"
                )

                message = (
                    f"Dear Parent, your child "
                    f"{student.first_name} "
                    f"{student.last_name} "
                    f"was marked as "
                    f"{attendance.status} "
                    f"on {attendance_date}. "
                    f"Marked by: {teacher_name}."
                )

                if attendance.remarks:

                    message += (
                        f" Remarks: "
                        f"{attendance.remarks}"
                    )

                try:

                    create_notification(
                        recipient=parent_user,
                        triggered_by=request.user,
                        attendance=attendance,
                        title=title,
                        message=message,
                        notification_type="Attendance",
                    )

                except Exception as notification_error:

                    # Do not destroy attendance marking because
                    # of a notification problem.
                    print(
                        "Attendance notification error:",
                        notification_error,
                    )

        # =====================================================
        # AUTO-FINALIZE
        # =====================================================

        submission.approval_status = APPROVED_STATUS
        submission.submitted_by = request.user
        submission.submitted_at = timezone.now()

        submission.save(
            update_fields=[
                "approval_status",
                "submitted_by",
                "submitted_at",
            ]
        )

        # =====================================================
        # RESPONSE
        # =====================================================

        return Response(
            {
                "message": (
                    "Attendance marked successfully. "
                    "Parents have been notified."
                ),
                "submission": submission.id,
                "classroom": str(submission.classroom),
                "date": submission.date,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# SUBMIT ATTENDANCE
# ============================================================

class SubmitAttendanceView(APIView):

    permission_classes = [IsAssignedClassTeacher]

    @transaction.atomic
    def post(self, request):

        serializer = CreateAttendanceSubmissionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        submission = get_object_or_404(

            AttendanceSubmission.objects
            .select_for_update()
            .select_related(
                "classroom",
                "assignment",
                "assignment__teacher",
            ),

            pk=serializer.validated_data["submission"],
        )

        # ----------------------------------------------------
        # Teacher profile
        # ----------------------------------------------------

        teacher_profile = get_teacher_profile(request)

        if not teacher_profile:

            return Response(
                {
                    "error": (
                        "Only teachers can submit attendance."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify class teacher assignment
        # ----------------------------------------------------

        assigned = TeacherAssignment.objects.filter(

            teacher=teacher_profile,

            classroom=submission.classroom,

            is_class_teacher=True,

            is_active=True,

        ).exists()

        if not assigned:

            return Response(
                {
                    "error": (
                        "You are not the class teacher "
                        "for this classroom."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Already approved
        # ----------------------------------------------------

        if submission.approval_status == APPROVED_STATUS:

            return Response(
                {
                    "error": (
                        "Attendance has already been finalized."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Attendance records
        # ----------------------------------------------------

        if not submission.attendance_records.exists():

            return Response(
                {
                    "error": (
                        "Cannot submit attendance before "
                        "marking students."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Finalize
        # ----------------------------------------------------

        submission.approval_status = APPROVED_STATUS
        submission.submitted_by = request.user
        submission.submitted_at = timezone.now()

        submission.save(
            update_fields=[
                "approval_status",
                "submitted_by",
                "submitted_at",
            ]
        )

        return Response(
            {
                "message": (
                    "Attendance submitted and finalized."
                ),
                "submission": submission.id,
                "classroom": str(submission.classroom),
                "date": submission.date,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# ATTENDANCE DETAIL
# ADMIN / ACADEMIC COORDINATOR
# ============================================================

class AttendanceDetailView(APIView):

    def get(self, request, submission_id):

        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
        ]:

            return Response(
                {
                    "error": "Access denied."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        submission = get_object_or_404(

            AttendanceSubmission.objects.select_related(
                "classroom",
                "submitted_by",
            ),

            pk=submission_id,
        )

        records = (
            Attendance.objects
            .filter(submission=submission)
            .select_related("student")
        )

        serializer = AttendanceDetailSerializer(
            records,
            many=True,
        )

        return Response(
            {
                "submission": submission.id,
                "classroom": str(submission.classroom),
                "date": submission.date,
                "attendance": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# STUDENT ATTENDANCE HISTORY
# ============================================================

class StudentAttendanceHistoryView(APIView):

    def get(self, request, student_id):

        student = get_object_or_404(
            Student.objects.select_related("classroom"),
            pk=student_id,
        )

        # ----------------------------------------------------
        # Only finalized attendance
        # ----------------------------------------------------

        records = (
            Attendance.objects
            .filter(
                student=student,
                submission__approval_status=APPROVED_STATUS,
            )
            .select_related(
                "submission",
                "submission__classroom",
            )
            .order_by(
                "-submission__date"
            )
        )

        serializer = StudentAttendanceHistorySerializer(
            records,
            many=True,
        )

        total = records.count()

        present = records.filter(
            status=Attendance.Status.PRESENT
        ).count()

        absent = records.filter(
            status=Attendance.Status.ABSENT
        ).count()

        excused = records.filter(
            status=Attendance.Status.EXCUSED
        ).count()

        attendance_percentage = (
            round((present / total) * 100, 2)
            if total > 0
            else 0
        )

        return Response(
            {
                "student": {
                    "id": student.id,
                    "admission_number": student.admission_number,
                    "name": (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    ).strip(),
                    "classroom": str(
                        student.classroom
                    ),
                },

                "summary": {
                    "total_days": total,
                    "present": present,
                    "absent": absent,
                    "excused": excused,
                    "attendance_percentage":
                        attendance_percentage,
                },

                "attendance": serializer.data,
            },

            status=status.HTTP_200_OK,
        )


# ============================================================
# CREATE ATTENDANCE SUBMISSION
# ============================================================

class AttendanceSubmissionCreateView(APIView):

    permission_classes = [IsAssignedClassTeacher]

    @transaction.atomic
    def post(self, request):

        serializer = CreateAttendanceSubmissionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        assignment = get_object_or_404(

            TeacherAssignment.objects.select_related(
                "teacher",
                "classroom",
                "subject",
            ),

            pk=serializer.validated_data["assignment"],
        )

        # ----------------------------------------------------
        # Teacher profile
        # ----------------------------------------------------

        teacher_profile = get_teacher_profile(request)

        if not teacher_profile:

            return Response(
                {
                    "error": (
                        "Only teachers can create attendance."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify teacher
        # ----------------------------------------------------

        if assignment.teacher_id != teacher_profile.id:

            return Response(
                {
                    "error": (
                        "This assignment does not belong "
                        "to you."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify class teacher
        # ----------------------------------------------------

        if not assignment.is_class_teacher:

            return Response(
                {
                    "error": (
                        "Only the class teacher can "
                        "mark this class."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Active assignment
        # ----------------------------------------------------

        if not assignment.is_active:

            return Response(
                {
                    "error": (
                        "This assignment is inactive."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Today's attendance
        # ----------------------------------------------------

        today = timezone.localdate()

        # ----------------------------------------------------
        # Create or get submission
        # ----------------------------------------------------

        submission, created = (
            AttendanceSubmission.objects.get_or_create(

                assignment=assignment,

                date=today,

                defaults={
                    "classroom": assignment.classroom,
                    "submitted_by": request.user,
                    "approval_status": DRAFT_STATUS,
                },
            )
        )

        # ----------------------------------------------------
        # Make sure classroom is correct
        # ----------------------------------------------------

        if submission.classroom_id != assignment.classroom_id:

            submission.classroom = assignment.classroom

            submission.save(
                update_fields=["classroom"]
            )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # If the attendance was already approved today,
        # don't silently create a new draft.
        # ----------------------------------------------------

        if (
            not created
            and submission.approval_status
            == APPROVED_STATUS
        ):

            return Response(
                {
                    "submission": submission.id,
                    "created": False,
                    "already_finalized": True,
                    "classroom": str(
                        assignment.classroom
                    ),
                    "date": submission.date,
                    "message": (
                        "Attendance for this class "
                        "has already been finalized today."
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "submission": submission.id,
                "created": created,
                "already_finalized": False,
                "assignment": assignment.id,
                "classroom": str(
                    assignment.classroom
                ),
                "classroom_id":
                    assignment.classroom_id,
                "subject": (
                    assignment.subject.name
                    if assignment.subject
                    else ""
                ),
                "subject_id":
                    assignment.subject_id,
                "date": submission.date,
                "is_class_teacher":
                    assignment.is_class_teacher,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


# ============================================================
# TEACHER ATTENDANCE HISTORY
# ============================================================

class TeacherAttendanceHistoryView(APIView):

    permission_classes = [IsAssignedClassTeacher]

    def get(self, request):

        teacher_profile = get_teacher_profile(request)

        if not teacher_profile:

            return Response(
                {
                    "error": (
                        "Only teachers can view "
                        "attendance history."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Attendance marked by this teacher
        # ----------------------------------------------------

        records = (
            Attendance.objects
            .filter(
                submission__submitted_by=request.user
            )
            .select_related(
                "student",
                "submission",
                "submission__classroom",
            )
            .order_by(
                "-submission__date",
                "-id",
            )
        )

        data = []

        for record in records:

            # ------------------------------------------------
            # Student name
            # ------------------------------------------------

            student_name = (
                f"{record.student.first_name or ''} "
                f"{record.student.last_name or ''}"
            ).strip()

            if not student_name:

                student_name = (
                    f"Student #{record.student_id}"
                )

            # ------------------------------------------------
            # Classroom
            # ------------------------------------------------

            classroom_name = (
                str(record.submission.classroom)
                if record.submission.classroom
                else "Unknown Class"
            )

            data.append(
                {
                    "id": record.id,

                    "submission":
                        record.submission.id,

                    "date":
                        record.submission.date,

                    "classroom_name":
                        classroom_name,

                    "student_name":
                        student_name,

                    "admission_number":
                        getattr(
                            record.student,
                            "admission_number",
                            "N/A",
                        ),

                    "status":
                        record.status,

                    "remarks":
                        record.remarks or "",
                }
            )

        return Response(
            data,
            status=status.HTTP_200_OK,
        )