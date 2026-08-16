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
# HELPER FUNCTIONS
# ============================================================

def get_teacher_profile(user):
    """
    Safely get the TeacherProfile belonging to the logged-in user.
    """
    try:
        return user.teacher_profile
    except TeacherProfile.DoesNotExist:
        return None


def is_class_teacher_assignment(assignment, teacher_profile):
    """
    Attendance is only allowed through the teacher's active
    class-teacher assignment.

    IMPORTANT:
    This does NOT change TeacherAssignment logic.
    A teacher can still have multiple assignments.
    """
    if not assignment:
        return False

    return (
        assignment.teacher_id == teacher_profile.id
        and assignment.is_class_teacher is True
        and assignment.is_active is True
    )


# ============================================================
# MARK ATTENDANCE
# ============================================================

class MarkAttendanceView(APIView):
    """
    GET:
        Load students for the selected class-teacher assignment.

    POST:
        Save attendance records.

    IMPORTANT:
    Only the class teacher can mark attendance.
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

        teacher_profile = get_teacher_profile(request.user)

        if not teacher_profile:
            return Response(
                {
                    "error": "Only teachers can access attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify class teacher
        # ----------------------------------------------------

        if not is_class_teacher_assignment(
            assignment,
            teacher_profile,
        ):
            return Response(
                {
                    "error": (
                        "You are not the class teacher for this classroom. "
                        "Please select your class-teacher assignment."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Create or load today's submission
        # ----------------------------------------------------

        submission, created = (
            AttendanceSubmission.objects.get_or_create(
                assignment=assignment,
                date=timezone.localdate(),
                defaults={
                    "classroom": assignment.classroom,
                    "submitted_by": request.user,
                    "approval_status": (
                        AttendanceSubmission
                        .ApprovalStatus
                        .DRAFT
                    ),
                },
            )
        )

        # ----------------------------------------------------
        # Students in this classroom
        # ----------------------------------------------------

        students = (
            Student.objects
            .filter(classroom=assignment.classroom)
            .order_by(
                "admission_number",
                "first_name",
            )
        )

        records = []

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
                    "admission_number": (
                        student.admission_number
                    ),
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
                "submission_id": submission.id,

                "assignment": assignment.id,
                "assignment_id": assignment.id,

                "classroom": assignment.classroom_id,
                "classroom_name": str(
                    assignment.classroom
                ),

                "subject": assignment.subject_id,
                "subject_name": (
                    assignment.subject.name
                    if assignment.subject
                    else ""
                ),

                "is_class_teacher": True,

                "date": submission.date,

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

        # ----------------------------------------------------
        # Get submission
        # ----------------------------------------------------

        submission = get_object_or_404(
            AttendanceSubmission.objects
            .select_for_update()
            .select_related(
                "assignment",
                "classroom",
                "assignment__teacher",
                "assignment__subject",
            ),
            pk=serializer.validated_data["submission"],
        )

        # ----------------------------------------------------
        # Teacher profile
        # ----------------------------------------------------

        teacher_profile = get_teacher_profile(request.user)

        if not teacher_profile:
            return Response(
                {
                    "error": "Only teachers can save attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        assignment = submission.assignment

        # ----------------------------------------------------
        # Verify assignment belongs to teacher
        # ----------------------------------------------------

        if assignment.teacher_id != teacher_profile.id:
            return Response(
                {
                    "error": (
                        "This attendance submission "
                        "does not belong to you."
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
                        "mark attendance for this class."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify active assignment
        # ----------------------------------------------------

        if not assignment.is_active:
            return Response(
                {
                    "error": "This assignment is inactive."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Verify submission status
        # ----------------------------------------------------

        if submission.approval_status not in [
            AttendanceSubmission.ApprovalStatus.DRAFT,
            AttendanceSubmission.ApprovalStatus.RETURNED,
        ]:
            return Response(
                {
                    "error": (
                        "Attendance has already been finalized."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        teacher_name = (
            request.user.get_full_name()
            or request.user.username
            or "Teacher"
        )

        attendance_date = submission.date

        # ----------------------------------------------------
        # SAVE ATTENDANCE
        # ----------------------------------------------------

        saved_count = 0
        notification_count = 0

        for record in serializer.validated_data["records"]:

            student = get_object_or_404(
                Student,
                pk=record["student"],
            )

            # ------------------------------------------------
            # Security:
            # Student must belong to this classroom
            # ------------------------------------------------

            if student.classroom_id != submission.classroom_id:
                return Response(
                    {
                        "error": (
                            f"Student {student.id} does not "
                            "belong to this classroom."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # Save attendance
            # ------------------------------------------------

            attendance, _ = (
                Attendance.objects.update_or_create(
                    submission=submission,
                    student=student,
                    defaults={
                        "status": record["status"],
                        "remarks": record.get(
                            "remarks",
                            "",
                        ),
                    },
                )
            )

            saved_count += 1

            # ------------------------------------------------
            # Notify parent
            # ------------------------------------------------

            parent_user = None

            # Current relationship
            if hasattr(student, "parent") and student.parent:
                parent_user = getattr(
                    student.parent,
                    "user",
                    None,
                )

            # ------------------------------------------------
            # Create notification if parent exists
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

                    notification_count += 1

                except Exception as notification_error:

                    # Do not destroy attendance saving
                    # because notification has a separate issue.
                    print(
                        "Attendance notification error:",
                        notification_error,
                    )

        # ----------------------------------------------------
        # FINALIZE SUBMISSION
        # ----------------------------------------------------

        submission.approval_status = (
            AttendanceSubmission
            .ApprovalStatus
            .APPROVED
        )

        submission.submitted_by = request.user
        submission.submitted_at = timezone.now()

        submission.save(
            update_fields=[
                "approval_status",
                "submitted_by",
                "submitted_at",
            ]
        )

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return Response(
            {
                "message": (
                    "Attendance marked successfully."
                ),
                "submission": submission.id,
                "classroom": str(
                    submission.classroom
                ),
                "date": submission.date,
                "records_saved": saved_count,
                "parents_notified": notification_count,
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
            pk=serializer.validated_data[
                "submission"
            ],
        )

        teacher_profile = get_teacher_profile(
            request.user
        )

        if not teacher_profile:
            return Response(
                {
                    "error": (
                        "Only teachers can submit attendance."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        assignment = submission.assignment

        # ----------------------------------------------------
        # Verify teacher
        # ----------------------------------------------------

        if assignment.teacher_id != teacher_profile.id:
            return Response(
                {
                    "error": (
                        "This submission does not "
                        "belong to you."
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
                        "You are not the class teacher "
                        "for this classroom."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify active
        # ----------------------------------------------------

        if not assignment.is_active:
            return Response(
                {
                    "error": "This assignment is inactive."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Already approved?
        # ----------------------------------------------------

        if (
            submission.approval_status
            == AttendanceSubmission
            .ApprovalStatus
            .APPROVED
        ):
            return Response(
                {
                    "error": (
                        "Attendance has already "
                        "been finalized."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Check records
        # ----------------------------------------------------

        if not submission.attendance_records.exists():
            return Response(
                {
                    "error": (
                        "Cannot submit attendance "
                        "before marking students."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Finalize
        # ----------------------------------------------------

        submission.approval_status = (
            AttendanceSubmission
            .ApprovalStatus
            .APPROVED
        )

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
                "classroom": str(
                    submission.classroom
                ),
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
                "classroom": str(
                    submission.classroom
                ),
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
            Student.objects.select_related(
                "classroom"
            ),
            pk=student_id,
        )

        records = (
            Attendance.objects
            .filter(
                student=student,
                submission__approval_status="Approved",
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
                    "admission_number": (
                        student.admission_number
                    ),
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
                    "attendance_percentage": (
                        attendance_percentage
                    ),
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
            pk=serializer.validated_data[
                "assignment"
            ],
        )

        teacher_profile = get_teacher_profile(
            request.user
        )

        if not teacher_profile:
            return Response(
                {
                    "error": (
                        "Only teachers can create "
                        "attendance."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # IMPORTANT FIX
        # ----------------------------------------------------

        if assignment.teacher_id != teacher_profile.id:
            return Response(
                {
                    "error": (
                        "This assignment does not "
                        "belong to you."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not assignment.is_class_teacher:
            return Response(
                {
                    "error": (
                        "Only the class teacher can "
                        "mark this class. "
                        "Please select your class-teacher "
                        "assignment."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

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
        # Get/create today's submission
        # ----------------------------------------------------

        submission, created = (
            AttendanceSubmission.objects.get_or_create(
                assignment=assignment,
                date=timezone.localdate(),
                defaults={
                    "classroom": assignment.classroom,
                    "submitted_by": request.user,
                    "approval_status": (
                        AttendanceSubmission
                        .ApprovalStatus
                        .DRAFT
                    ),
                },
            )
        )

        return Response(
            {
                "submission": submission.id,
                "submission_id": submission.id,

                "created": created,

                "assignment": assignment.id,
                "assignment_id": assignment.id,

                "classroom": assignment.classroom_id,
                "classroom_name": str(
                    assignment.classroom
                ),

                "subject": assignment.subject_id,
                "subject_name": (
                    assignment.subject.name
                    if assignment.subject
                    else ""
                ),

                "is_class_teacher": True,

                "date": submission.date,
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

        teacher_profile = get_teacher_profile(
            request.user
        )

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

        records = (
            Attendance.objects
            .filter(
                submission__submitted_by=request.user
            )
            .select_related(
                "student",
                "submission",
                "submission__classroom",
                "submission__assignment",
                "submission__assignment__subject",
            )
            .order_by(
                "-submission__date"
            )
        )

        data = []

        for rec in records:

            student_name = (
                f"{rec.student.first_name or ''} "
                f"{rec.student.last_name or ''}"
            ).strip()

            if not student_name:
                student_name = (
                    f"Student #{rec.student_id}"
                )

            classroom_name = (
                str(rec.submission.classroom)
                if rec.submission.classroom
                else "Unknown Class"
            )

            subject_name = ""

            if (
                rec.submission.assignment
                and rec.submission.assignment.subject
            ):
                subject_name = (
                    rec.submission
                    .assignment
                    .subject
                    .name
                )

            data.append(
                {
                    "id": rec.id,

                    "date": (
                        rec.submission.date
                    ),

                    "classroom_name": (
                        classroom_name
                    ),

                    "subject_name": (
                        subject_name
                    ),

                    "student_name": (
                        student_name
                    ),

                    "admission_number": (
                        getattr(
                            rec.student,
                            "admission_number",
                            "N/A",
                        )
                    ),

                    "status": rec.status,

                    "remarks": (
                        rec.remarks or ""
                    ),
                }
            )

        return Response(
            data,
            status=status.HTTP_200_OK,
        )