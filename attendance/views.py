from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import (
    CustomUser,
    TeacherProfile,
)

from assignments.models import TeacherAssignment

from notifiations.services import create_notification

from students.models import Student

from attendance.models import (
    Attendance,
    AttendanceSubmission,
)

from attendance.serializers import (
    BulkAttendanceSerializer,
    CreateAttendanceSubmissionSerializer,
    AttendanceDetailSerializer,
    StudentAttendanceHistorySerializer,
)

from attendance.permissions import (
    IsAssignedClassTeacher,
)


# ============================================================
# HELPER — GET TEACHER PROFILE
# ============================================================

def get_teacher_profile(request):
    """
    Safely return the TeacherProfile belonging to the
    currently authenticated user.
    """

    try:
        return request.user.teacher_profile

    except TeacherProfile.DoesNotExist:
        return None

    except Exception:
        return None


# ============================================================
# HELPER — VERIFY CLASS TEACHER ASSIGNMENT
# ============================================================

def verify_class_teacher(
    request,
    assignment,
):
    """
    Verify that:

    1. Logged-in user is a teacher.
    2. Teacher owns the assignment.
    3. Assignment is marked as Class Teacher.
    4. Assignment is active.
    """

    teacher_profile = get_teacher_profile(request)

    if not teacher_profile:

        return (
            None,
            Response(
                {
                    "error": (
                        "Only teachers can access "
                        "attendance."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            ),
        )

    # --------------------------------------------------------
    # Teacher must own this assignment
    # --------------------------------------------------------

    if assignment.teacher_id != teacher_profile.id:

        return (
            None,
            Response(
                {
                    "error": (
                        "This assignment does not "
                        "belong to you."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            ),
        )

    # --------------------------------------------------------
    # Must be class teacher
    # --------------------------------------------------------

    if not assignment.is_class_teacher:

        return (
            None,
            Response(
                {
                    "error": (
                        "Only the class teacher can "
                        "mark attendance for this class."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            ),
        )

    # --------------------------------------------------------
    # Assignment must be active
    # --------------------------------------------------------

    if not assignment.is_active:

        return (
            None,
            Response(
                {
                    "error": (
                        "This teaching assignment "
                        "is inactive."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            ),
        )

    return (
        teacher_profile,
        None,
    )


# ============================================================
# CREATE ATTENDANCE SUBMISSION
# ============================================================

class AttendanceSubmissionCreateView(APIView):

    permission_classes = [
        IsAssignedClassTeacher
    ]

    @transaction.atomic
    def post(self, request):

        serializer = (
            CreateAttendanceSubmissionSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        assignment_id = (
            serializer.validated_data[
                "assignment"
            ]
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
        # Verify class teacher
        # ----------------------------------------------------

        (
            teacher_profile,
            error_response,
        ) = verify_class_teacher(
            request,
            assignment,
        )

        if error_response:
            return error_response

        # ----------------------------------------------------
        # Today's date
        # ----------------------------------------------------

        today = timezone.localdate()

        # ----------------------------------------------------
        # Get/create today's attendance session
        # ----------------------------------------------------

        submission, created = (
            AttendanceSubmission.objects.get_or_create(

                assignment=assignment,

                date=today,

                defaults={
                    "classroom": assignment.classroom,
                    "submitted_by": request.user,
                    "status": (
                        AttendanceSubmission.Status.DRAFT
                    ),
                },
            )
        )

        # ----------------------------------------------------
        # Protect classroom relationship
        # ----------------------------------------------------

        if (
            submission.classroom_id
            != assignment.classroom_id
        ):

            submission.classroom = (
                assignment.classroom
            )

            submission.save(
                update_fields=[
                    "classroom"
                ]
            )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return Response(
            {
                "submission": submission.id,

                "created": created,

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

                "status": submission.status,

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
# MARK ATTENDANCE
# ============================================================

class MarkAttendanceView(APIView):

    permission_classes = [
        IsAssignedClassTeacher
    ]

    # ========================================================
    # GET — LOAD STUDENTS
    # ========================================================

    @transaction.atomic
    def get(self, request):

        assignment_id = (
            request.query_params.get(
                "assignment"
            )
        )

        if not assignment_id:

            return Response(
                {
                    "error": (
                        "Assignment is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Assignment
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
        # Verify teacher/class teacher
        # ----------------------------------------------------

        (
            teacher_profile,
            error_response,
        ) = verify_class_teacher(
            request,
            assignment,
        )

        if error_response:
            return error_response

        # ----------------------------------------------------
        # Today's date
        # ----------------------------------------------------

        today = timezone.localdate()

        # ----------------------------------------------------
        # Get/create submission
        # ----------------------------------------------------

        submission, created = (
            AttendanceSubmission.objects.get_or_create(

                assignment=assignment,

                date=today,

                defaults={
                    "classroom": assignment.classroom,
                    "submitted_by": request.user,
                    "status":
                        AttendanceSubmission.Status.DRAFT,
                },
            )
        )

        # ----------------------------------------------------
        # Get students
        # ----------------------------------------------------

        students = (
            Student.objects
            .filter(
                classroom=assignment.classroom
            )
            .order_by(
                "admission_number",
                "first_name",
                "last_name",
            )
        )

        records = []

        for student in students:

            attendance, created_record = (
                Attendance.objects.get_or_create(

                    submission=submission,

                    student=student,

                    defaults={
                        "status":
                            Attendance.Status.PRESENT,

                        "remarks": "",
                    },
                )
            )

            records.append(
                {
                    "id": attendance.id,

                    "student": student.id,

                    "admission_number":
                        student.admission_number,

                    "name": (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    ).strip(),

                    "status":
                        attendance.status,

                    "remarks":
                        attendance.remarks or "",
                }
            )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return Response(
            {
                "submission": submission.id,

                "assignment": assignment.id,

                "classroom":
                    str(assignment.classroom),

                "classroom_id":
                    assignment.classroom_id,

                "subject": (
                    assignment.subject.name
                    if assignment.subject
                    else ""
                ),

                "subject_id":
                    assignment.subject_id,

                "date":
                    submission.date,

                "status":
                    submission.status,

                "created":
                    created,

                "is_class_teacher":
                    assignment.is_class_teacher,

                "students":
                    records,
            },

            status=status.HTTP_200_OK,
        )

    # ========================================================
    # POST — SAVE ATTENDANCE
    #
    # ONE CLICK:
    #
    # 1. Save attendance
    # 2. Finalize attendance
    # 3. Find student's parent
    # 4. Create parent notification
    #
    # NO APPROVAL
    # NO SECOND BUTTON
    # NO PENDING
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
                "assignment__subject",
            ),

            pk=serializer.validated_data[
                "submission"
            ],
        )

        # ----------------------------------------------------
        # Teacher
        # ----------------------------------------------------

        teacher_profile = get_teacher_profile(
            request
        )

        if not teacher_profile:

            return Response(
                {
                    "error": (
                        "Only teachers can "
                        "save attendance."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Assignment
        # ----------------------------------------------------

        assignment = submission.assignment

        if not assignment:

            return Response(
                {
                    "error": (
                        "This attendance submission "
                        "has no teaching assignment."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # Teacher owns assignment
        # ----------------------------------------------------

        if (
            assignment.teacher_id
            != teacher_profile.id
        ):

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
        # Must be class teacher
        # ----------------------------------------------------

        if not assignment.is_class_teacher:

            return Response(
                {
                    "error": (
                        "Only the class teacher can "
                        "save attendance for this class."
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
        # Attendance date
        # ----------------------------------------------------

        attendance_date = submission.date

        # ----------------------------------------------------
        # Teacher name
        # ----------------------------------------------------

        teacher_name = (
            request.user.get_full_name()
            or request.user.username
        )

        # ----------------------------------------------------
        # Tracking
        # ----------------------------------------------------

        saved_records = []

        notifications_sent = 0

        parents_notified = []

        students_without_parent = []

        notification_errors = []

        # ====================================================
        # SAVE EACH STUDENT
        # ====================================================

        for record in (
            serializer.validated_data[
                "records"
            ]
        ):

            student = get_object_or_404(
                Student.objects.select_related(
                    "parent",
                    "parent__user",
                ),
                pk=record["student"],
            )

            # ------------------------------------------------
            # SECURITY:
            #
            # Student must belong to this classroom.
            # ------------------------------------------------

            if (
                student.classroom_id
                != submission.classroom_id
            ):

                return Response(
                    {
                        "error": (
                            f"{student.first_name} "
                            f"{student.last_name} "
                            "does not belong to this "
                            "classroom."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ------------------------------------------------
            # New values
            # ------------------------------------------------

            new_status = record["status"]

            new_remarks = (
                record.get("remarks")
                or ""
            ).strip()

            # ------------------------------------------------
            # Existing attendance
            # ------------------------------------------------

            existing_attendance = (
                Attendance.objects.filter(
                    submission=submission,
                    student=student,
                ).first()
            )

            old_status = (
                existing_attendance.status
                if existing_attendance
                else None
            )

            old_remarks = (
                existing_attendance.remarks or ""
                if existing_attendance
                else ""
            )

            # ------------------------------------------------
            # Save attendance
            # ------------------------------------------------

            attendance, created_record = (
                Attendance.objects.update_or_create(

                    submission=submission,

                    student=student,

                    defaults={
                        "status": new_status,
                        "remarks": new_remarks,
                    },
                )
            )

            saved_records.append(
                {
                    "id":
                        attendance.id,

                    "student":
                        student.id,

                    "student_name": (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    ).strip(),

                    "status":
                        attendance.status,

                    "remarks":
                        attendance.remarks or "",
                }
            )

            # =================================================
            # DETERMINE WHETHER ATTENDANCE CHANGED
            # =================================================

            attendance_changed = (
                created_record
                or old_status != new_status
                or old_remarks != new_remarks
            )

            if not attendance_changed:
                continue

            # =================================================
            # FIND PARENT
            #
            # Student:
            #
            # student.parent
            #
            # ParentProfile:
            #
            # student.parent.user
            # =================================================

            parent_profile = getattr(
                student,
                "parent",
                None,
            )

            if not parent_profile:

                students_without_parent.append(
                    {
                        "student_id":
                            student.id,

                        "student_name": (
                            f"{student.first_name} "
                            f"{student.last_name}"
                        ).strip(),

                        "admission_number":
                            student.admission_number,

                        "reason":
                            "Student has no parent profile."
                    }
                )

                print(
                    "⚠️ No ParentProfile found for student:",
                    student.id,
                    student.first_name,
                    student.last_name,
                )

                continue

            # ------------------------------------------------
            # Parent user
            # ------------------------------------------------

            parent_user = getattr(
                parent_profile,
                "user",
                None,
            )

            if not parent_user:

                students_without_parent.append(
                    {
                        "student_id":
                            student.id,

                        "student_name": (
                            f"{student.first_name} "
                            f"{student.last_name}"
                        ).strip(),

                        "admission_number":
                            student.admission_number,

                        "reason":
                            "ParentProfile has no user."
                    }
                )

                print(
                    "⚠️ ParentProfile has no user:",
                    parent_profile.id,
                )

                continue

            # =================================================
            # CREATE PARENT NOTIFICATION
            # =================================================

            title = (
                "Attendance: "
                f"{student.first_name} — "
                f"{attendance.status}"
            )

            message = (
                "Dear Parent, your child "
                f"{student.first_name} "
                f"{student.last_name} "
                "was marked as "
                f"{attendance.status} "
                f"on {attendance_date}. "
                f"Marked by: {teacher_name}."
            )

            if attendance.remarks:

                message += (
                    " Remarks: "
                    f"{attendance.remarks}"
                )

            print(
                "📢 Creating attendance notification..."
            )

            print(
                "   Student:",
                student.id,
                student.first_name,
                student.last_name,
            )

            print(
                "   ParentProfile:",
                parent_profile.id,
            )

            print(
                "   Parent User:",
                parent_user.id,
                parent_user.username,
            )

            print(
                "   Attendance:",
                attendance.id,
            )

            try:

                notification = create_notification(

                    recipient=parent_user,

                    triggered_by=request.user,

                    attendance=attendance,

                    title=title,

                    message=message,

                    notification_type="Attendance",
                )

                notifications_sent += 1

                parents_notified.append(
                    {
                        "parent_id":
                            parent_user.id,

                        "parent_username":
                            parent_user.username,

                        "student_id":
                            student.id,

                        "student_name": (
                            f"{student.first_name} "
                            f"{student.last_name}"
                        ).strip(),

                        "notification_id":
                            notification.id,
                    }
                )

                print(
                    "✅ Parent notification created:",
                    notification.id,
                )

            except Exception as notification_error:

                error_message = str(
                    notification_error
                )

                notification_errors.append(
                    {
                        "student_id":
                            student.id,

                        "student_name": (
                            f"{student.first_name} "
                            f"{student.last_name}"
                        ).strip(),

                        "parent_id":
                            parent_user.id,

                        "parent_username":
                            parent_user.username,

                        "error":
                            error_message,
                    }
                )

                print(
                    "❌ Attendance notification error:",
                    notification_error,
                )

        # ====================================================
        # FINALIZE IMMEDIATELY
        # ====================================================

        submission.status = (
            AttendanceSubmission.Status.FINAL
        )

        submission.submitted_by = request.user

        submission.submitted_at = timezone.now()

        submission.save(
            update_fields=[
                "status",
                "submitted_by",
                "submitted_at",
                "updated_at",
            ]
        )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return Response(
            {
                "message": (
                    "Attendance marked successfully."
                ),

                "submission":
                    submission.id,

                "classroom":
                    str(submission.classroom),

                "date":
                    submission.date,

                "status":
                    submission.status,

                "saved_records":
                    saved_records,

                # --------------------------------------------
                # Notification information
                # --------------------------------------------

                "notifications_sent":
                    notifications_sent,

                "parent_notified":
                    notifications_sent > 0,

                "parents_notified":
                    parents_notified,

                "students_without_parent":
                    students_without_parent,

                "notification_errors":
                    notification_errors,

                # --------------------------------------------
                # Helpful summary
                # --------------------------------------------

                "notification_summary": {
                    "sent":
                        notifications_sent,

                    "students_without_parent":
                        len(
                            students_without_parent
                        ),

                    "notification_errors":
                        len(
                            notification_errors
                        ),
                },
            },

            status=status.HTTP_200_OK,
        )


# ============================================================
# SUBMIT ATTENDANCE
#
# KEPT FOR BACKWARD COMPATIBILITY.
#
# React DOES NOT need to call this.
#
# Attendance is finalized automatically when saved.
# ============================================================

class SubmitAttendanceView(APIView):

    permission_classes = [
        IsAssignedClassTeacher
    ]

    @transaction.atomic
    def post(self, request):

        # ----------------------------------------------------
        # Old endpoint is no longer needed.
        # ----------------------------------------------------

        submission_id = (
            request.data.get(
                "submission"
            )
        )

        if not submission_id:

            return Response(
                {
                    "error": (
                        "Attendance is saved directly "
                        "when marked. A separate submit "
                        "step is not required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission = get_object_or_404(
            AttendanceSubmission,
            pk=submission_id,
        )

        # ----------------------------------------------------
        # Verify teacher
        # ----------------------------------------------------

        teacher_profile = get_teacher_profile(
            request
        )

        if not teacher_profile:

            return Response(
                {
                    "error": (
                        "Only teachers can access "
                        "attendance."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # Verify assignment
        # ----------------------------------------------------

        assignment = submission.assignment

        if (
            not assignment
            or assignment.teacher_id
            != teacher_profile.id
        ):

            return Response(
                {
                    "error": (
                        "This attendance submission "
                        "does not belong to you."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            {
                "message": (
                    "Attendance is already saved "
                    "automatically. No approval or "
                    "submit step is required."
                ),

                "submission":
                    submission.id,

                "status":
                    submission.status,
            },

            status=status.HTTP_200_OK,
        )


# ============================================================
# ATTENDANCE DETAIL
#
# ADMIN / ACADEMIC COORDINATOR
# ============================================================

class AttendanceDetailView(APIView):

    def get(
        self,
        request,
        submission_id,
    ):

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
                "assignment",
                "assignment__teacher",
                "assignment__subject",
            ),

            pk=submission_id,
        )

        records = (
            Attendance.objects
            .filter(
                submission=submission
            )
            .select_related(
                "student"
            )
        )

        serializer = AttendanceDetailSerializer(
            records,
            many=True,
        )

        return Response(
            {
                "submission":
                    submission.id,

                "assignment":
                    submission.assignment_id,

                "classroom":
                    str(submission.classroom),

                "date":
                    submission.date,

                "status":
                    submission.status,

                "attendance":
                    serializer.data,
            },

            status=status.HTTP_200_OK,
        )


# ============================================================
# STUDENT ATTENDANCE HISTORY
# ============================================================

class StudentAttendanceHistoryView(APIView):

    def get(
        self,
        request,
        student_id,
    ):

        student = get_object_or_404(

            Student.objects.select_related(
                "classroom"
            ),

            pk=student_id,
        )

        # ----------------------------------------------------
        # Only FINAL attendance counts.
        # ----------------------------------------------------

        records = (
            Attendance.objects
            .filter(
                student=student,

                submission__status=(
                    AttendanceSubmission.Status.FINAL
                ),
            )
            .select_related(
                "submission",
                "submission__classroom",
            )
            .order_by(
                "-submission__date"
            )
        )

        serializer = (
            StudentAttendanceHistorySerializer(
                records,
                many=True,
            )
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
            round(
                (present / total) * 100,
                2,
            )
            if total > 0
            else 0
        )

        return Response(
            {
                "student": {

                    "id":
                        student.id,

                    "admission_number":
                        student.admission_number,

                    "name": (
                        f"{student.first_name} "
                        f"{student.last_name}"
                    ).strip(),

                    "classroom":
                        str(student.classroom),
                },

                "summary": {

                    "total_days":
                        total,

                    "present":
                        present,

                    "absent":
                        absent,

                    "excused":
                        excused,

                    "attendance_percentage":
                        attendance_percentage,
                },

                "attendance":
                    serializer.data,
            },

            status=status.HTTP_200_OK,
        )


# ============================================================
# TEACHER ATTENDANCE HISTORY
# ============================================================

class TeacherAttendanceHistoryView(APIView):

    permission_classes = [
        IsAssignedClassTeacher
    ]

    def get(
        self,
        request,
    ):

        teacher_profile = (
            get_teacher_profile(request)
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
                "-submission__date",
                "-id",
            )
        )

        data = []

        for record in records:

            student_name = (
                f"{record.student.first_name or ''} "
                f"{record.student.last_name or ''}"
            ).strip()

            if not student_name:

                student_name = (
                    f"Student #{record.student_id}"
                )

            classroom_name = (
                str(
                    record.submission.classroom
                )
                if record.submission.classroom
                else "Unknown Class"
            )

            subject_name = ""

            if (
                record.submission.assignment
                and record.submission.assignment.subject
            ):

                subject_name = (
                    record
                    .submission
                    .assignment
                    .subject
                    .name
                )

            data.append(
                {
                    "id":
                        record.id,

                    "submission":
                        record.submission.id,

                    "date":
                        record.submission.date,

                    "classroom_name":
                        classroom_name,

                    "subject_name":
                        subject_name,

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

                    "submission_status":
                        record.submission.status,
                }
            )

        return Response(
            data,
            status=status.HTTP_200_OK,
        )