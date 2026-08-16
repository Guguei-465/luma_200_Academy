from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# ✅ YOUR APP NAME: notification
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


# =====================================================
# ✅ Load Attendance Page — Class Teacher Only
# =====================================================
class MarkAttendanceView(APIView):
    permission_classes = [IsAssignedClassTeacher]

    @transaction.atomic
    def get(self, request):
        assignment_id = request.query_params.get("assignment")
        if not assignment_id:
            return Response({"error": "Assignment is required."}, status=status.HTTP_400_BAD_REQUEST)

        assignment = get_object_or_404(
            TeacherAssignment.objects.select_related("teacher", "classroom", "subject"),
            pk=assignment_id,
        )

        try:
            teacher_profile = request.user.teacher_profile
        except TeacherProfile.DoesNotExist:
            return Response({"error": "Only teachers can access attendance."}, status=status.HTTP_403_FORBIDDEN)

        if assignment.teacher != teacher_profile or not assignment.is_class_teacher:
            return Response({"error": "You are not the class teacher for this classroom."}, status=status.HTTP_403_FORBIDDEN)

        submission, created = AttendanceSubmission.objects.get_or_create(
            assignment=assignment,
            date=timezone.localdate(),
            defaults={
                "classroom": assignment.classroom,
                "submitted_by": request.user,
                "approval_status": AttendanceSubmission.ApprovalStatus.DRAFT,
            },
        )

        students = Student.objects.filter(
            classroom=assignment.classroom
        ).order_by("admission_number", "first_name")

        records = []
        for student in students:
            attendance, _ = Attendance.objects.get_or_create(
                submission=submission,
                student=student,
                defaults={"status": Attendance.Status.PRESENT, "remarks": ""},
            )
            records.append({
                "id": attendance.id,
                "student": student.id,
                "admission_number": student.admission_number,
                "name": f"{student.first_name} {student.last_name}",
                "status": attendance.status,
                "remarks": attendance.remarks,
            })

        return Response({
            "submission": submission.id,
            "assignment": assignment.id,
            "classroom": str(assignment.classroom),
            "subject": assignment.subject.name,
            "date": submission.date,
            "students": records,
        })

    # =====================================================
    # ✅ Save Attendance + NOTIFY PARENTS INSTANTLY
    # =====================================================
    @transaction.atomic
    def post(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = get_object_or_404(
            AttendanceSubmission.objects.select_for_update().select_related(
                "assignment", "classroom", "assignment__teacher"
            ),
            pk=serializer.validated_data["submission"],
        )

        try:
            teacher_profile = request.user.teacher_profile
        except TeacherProfile.DoesNotExist:
            return Response({"error": "Only teachers can save attendance."}, status=status.HTTP_403_FORBIDDEN)

        if submission.assignment.teacher != teacher_profile:
            return Response({"error": "This submission does not belong to you."}, status=status.HTTP_403_FORBIDDEN)

        if submission.approval_status not in [
            AttendanceSubmission.ApprovalStatus.DRAFT,
            AttendanceSubmission.ApprovalStatus.RETURNED,
        ]:
            return Response({"error": "Attendance has already been finalized."}, status=status.HTTP_400_BAD_REQUEST)

        teacher_name = request.user.get_full_name()
        attendance_date = submission.date

        # ✅ Save each record + Send notification to parent
        for record in serializer.validated_data["records"]:
            student = get_object_or_404(Student, pk=record["student"])

            attendance, _ = Attendance.objects.update_or_create(
                submission=submission,
                student=student,
                defaults={
                    "status": record["status"],
                    "remarks": record.get("remarks", ""),
                },
            )

            # ✅ NOTIFICATION TO PARENT
            parent_user = None
            if hasattr(student, "parent") and student.parent:
                parent_user = getattr(student.parent, "user", None)

            if parent_user:
                title = f"Attendance: {student.first_name} — {attendance.status}"
                message = (
                    f"Dear Parent, your child {student.first_name} {student.last_name} "
                    f"was marked as {attendance.status} on {attendance_date}. "
                    f"Marked by: {teacher_name}."
                )
                if attendance.remarks:
                    message += f" Remarks: {attendance.remarks}"

                create_notification(
                    recipient=parent_user,
                    triggered_by=request.user,
                    attendance=attendance,
                    title=title,
                    message=message,
                    notification_type="Attendance",
                )

        # ✅ Auto-finalize — NO APPROVAL NEEDED
        submission.approval_status = AttendanceSubmission.ApprovalStatus.APPROVED
        submission.submitted_by = request.user
        submission.submitted_at = timezone.now()
        submission.save(update_fields=["approval_status", "submitted_by", "submitted_at"])

        return Response({
            "message": "✅ Attendance marked successfully. Parents have been notified.",
            "submission": submission.id,
            "classroom": str(submission.classroom),
            "date": submission.date,
        }, status=status.HTTP_200_OK)


# =====================================================
# ✅ Submit Attendance — Finalize Instantly
# =====================================================
class SubmitAttendanceView(APIView):
    permission_classes = [IsAssignedClassTeacher]

    @transaction.atomic
    def post(self, request):
        serializer = CreateAttendanceSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = get_object_or_404(
            AttendanceSubmission.objects.select_for_update().select_related("classroom"),
            pk=serializer.validated_data["submission"],
        )

        try:
            teacher_profile = request.user.teacher_profile
        except TeacherProfile.DoesNotExist:
            return Response({"error": "Only teachers can submit attendance."}, status=status.HTTP_403_FORBIDDEN)

        assigned = TeacherAssignment.objects.filter(
            teacher=teacher_profile,
            classroom=submission.classroom,
            is_class_teacher=True,
            is_active=True,
        ).exists()

        if not assigned:
            return Response({"error": "You are not the class teacher for this classroom."}, status=status.HTTP_403_FORBIDDEN)

        if submission.approval_status == AttendanceSubmission.ApprovalStatus.APPROVED:
            return Response({"error": "Attendance has already been finalized."}, status=status.HTTP_400_BAD_REQUEST)

        if not submission.attendance_records.exists():
            return Response({"error": "Cannot submit attendance before marking students."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Finalize immediately — NO PENDING / NO APPROVAL
        submission.approval_status = AttendanceSubmission.ApprovalStatus.APPROVED
        submission.submitted_by = request.user
        submission.submitted_at = timezone.now()
        submission.save(update_fields=["approval_status", "submitted_by", "submitted_at"])

        return Response({
            "message": "✅ Attendance submitted and finalized. Notifications sent to parents.",
            "submission": submission.id,
            "classroom": str(submission.classroom),
            "date": submission.date,
        }, status=status.HTTP_200_OK)


# =====================================================
# ✅ Attendance Detail (Admin/Coordinator Only)
# =====================================================
class AttendanceDetailView(APIView):
    def get(self, request, submission_id):
        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
        ]:
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        submission = get_object_or_404(
            AttendanceSubmission.objects.select_related("classroom", "submitted_by"),
            pk=submission_id,
        )
        records = Attendance.objects.filter(submission=submission).select_related("student")
        serializer = AttendanceDetailSerializer(records, many=True)

        return Response({
            "submission": submission.id,
            "classroom": str(submission.classroom),
            "date": submission.date,
            "attendance": serializer.data,
        }, status=status.HTTP_200_OK)


# =====================================================
# ✅ Student Attendance History
# =====================================================
class StudentAttendanceHistoryView(APIView):
    def get(self, request, student_id):
        student = get_object_or_404(Student.objects.select_related("classroom"), pk=student_id)
        records = Attendance.objects.filter(
            student=student,
            submission__approval_status="Approved",
        ).select_related("submission", "submission__classroom").order_by("-submission__date")

        serializer = StudentAttendanceHistorySerializer(records, many=True)
        total = records.count()
        present = records.filter(status=Attendance.Status.PRESENT).count()
        absent = records.filter(status=Attendance.Status.ABSENT).count()
        excused = records.filter(status=Attendance.Status.EXCUSED).count()
        attendance_percentage = round((present / total) * 100, 2) if total > 0 else 0

        return Response({
            "student": {
                "id": student.id,
                "admission_number": student.admission_number,
                "name": f"{student.first_name} {student.last_name}",
                "classroom": str(student.classroom),
            },
            "summary": {
                "total_days": total,
                "present": present,
                "absent": absent,
                "excused": excused,
                "attendance_percentage": attendance_percentage,
            },
            "attendance": serializer.data,
        }, status=status.HTTP_200_OK)


# =====================================================
# ✅ Create Attendance Submission
# =====================================================
class AttendanceSubmissionCreateView(APIView):
    permission_classes = [IsAssignedClassTeacher]

    @transaction.atomic
    def post(self, request):
        serializer = CreateAttendanceSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        assignment = get_object_or_404(
            TeacherAssignment.objects.select_related("teacher", "classroom"),
            pk=serializer.validated_data["assignment"],
        )

        try:
            teacher_profile = request.user.teacher_profile
        except TeacherProfile.DoesNotExist:
            return Response({"error": "Only teachers can create attendance."}, status=status.HTTP_403_FORBIDDEN)

        if assignment.teacher != teacher_profile or not assignment.is_class_teacher:
            return Response({"error": "Only the class teacher can mark this class."}, status=status.HTTP_403_FORBIDDEN)

        if not assignment.is_active:
            return Response({"error": "This assignment is inactive."}, status=status.HTTP_400_BAD_REQUEST)

        submission, created = AttendanceSubmission.objects.get_or_create(
            assignment=assignment,
            date=timezone.localdate(),
            defaults={
                "classroom": assignment.classroom,
                "submitted_by": request.user,
                "approval_status": AttendanceSubmission.ApprovalStatus.DRAFT,
            },
        )

        return Response({
            "submission": submission.id,
            "created": created,
            "classroom": str(assignment.classroom),
            "date": submission.date,
        }, status=status.HTTP_201_CREATED)


# =====================================================
# ✅ TEACHER ATTENDANCE HISTORY — NEW
# =====================================================
class TeacherAttendanceHistoryView(APIView):
    permission_classes = [IsAssignedClassTeacher]

    def get(self, request):
        try:
            teacher_profile = request.user.teacher_profile
        except TeacherProfile.DoesNotExist:
            return Response({"error": "Only teachers can view history."}, status=403)

        # Get all finalized attendance marked by this teacher
        records = Attendance.objects.filter(
            submission__submitted_by=request.user,
            submission__approval_status=AttendanceSubmission.ApprovalStatus.APPROVED,
        ).select_related("student", "submission", "submission__classroom").order_by("-submission__date")

        data = []
        for rec in records:
            data.append({
                "id": rec.id,
                "date": rec.submission.date,
                "classroom": str(rec.submission.classroom),
                "student_name": f"{rec.student.first_name} {rec.student.last_name}",
                "admission_number": rec.student.admission_number,
                "status": rec.status,
                "remarks": rec.remarks,
            })

        return Response(data, status=200)