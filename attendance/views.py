from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from notifiations.services import create_notification
from notifiations.models import Notification
from parents.models import ParentStudent
from accounts.models import (
    TeacherProfile,
    AcademicCoordinatorProfile,
)

from assignments.models import TeacherAssignment

from classes.models import ClassRoom
from students.models import Student

from attendance.models import (
    Attendance,
    AttendanceSubmission,
)

from attendance.serializers import (
    BulkAttendanceSerializer,
    CreateAttendanceSubmissionSerializer,
    SubmitAttendanceSerializer,
    PendingAttendanceSerializer,
    ApproveAttendanceSerializer,
    ReturnAttendanceSerializer,
    AttendanceDetailSerializer,
    StudentAttendanceHistorySerializer,
)

from attendance.permissions import IsAssignedClassTeacher

# Notifications will be enabled later
# from notifications.services import create_notification
#  
# create you views here
# =====================================================
# Mark Attendance
# =====================================================
class MarkAttendanceView(APIView):
    permission_classes = [IsAssignedClassTeacher]

    @transaction.atomic
    def post(self, request):

        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = get_object_or_404(
            AttendanceSubmission.objects.select_for_update().select_related(
                "classroom",
            ),
            pk=serializer.validated_data["submission"],
        )

        # =====================================
        # Verify Teacher Profile
        # =====================================
        try:
            teacher_profile = request.user.teacher_profile

        except TeacherProfile.DoesNotExist:
            return Response(
                {
                    "error": "Only teachers can mark attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # =====================================
        # Verify Teacher Assignment
        # =====================================
        assigned = TeacherAssignment.objects.filter(
            teacher=teacher_profile,
            classroom=submission.classroom,
            is_class_teacher=True,
            is_active=True,
        ).exists()

        if not assigned:
            return Response(
                {
                    "error": "You are not assigned as the class teacher for this classroom."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # =====================================
        # Attendance already submitted?
        # =====================================
        if submission.approval_status == AttendanceSubmission.ApprovalStatus.PENDING:
            return Response(
                {
                    "error": "Attendance has already been submitted for approval."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Attendance already approved?
        # =====================================
        if submission.approval_status == AttendanceSubmission.ApprovalStatus.APPROVED:
            return Response(
                {
                    "error": "Approved attendance cannot be edited."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Prevent duplicate students
        # =====================================
        student_ids = [
            record["student"]
            for record in serializer.validated_data["records"]
        ]

        if len(student_ids) != len(set(student_ids)):
            return Response(
                {
                    "error": "Duplicate students were found in the attendance records."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Attendance Summary
        # =====================================
        present = 0
        absent = 0
        excused = 0

        # =====================================
        # Save Attendance
        # =====================================
        for record in serializer.validated_data["records"]:

            student = get_object_or_404(
                Student.objects.select_related("classroom"),
                pk=record["student"],
            )

            # Student must belong to this classroom
            if student.classroom_id != submission.classroom_id:
                return Response(
                    {
                        "error": f"{student.first_name} {student.last_name} does not belong to this classroom."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Attendance.objects.update_or_create(
                submission=submission,
                student=student,
                defaults={
                    "status": record["status"],
                    "remarks": record.get("remarks", ""),
                },
            )

            if record["status"] == Attendance.Status.PRESENT:
                present += 1

            elif record["status"] == Attendance.Status.ABSENT:
                absent += 1

            elif record["status"] == Attendance.Status.EXCUSED:
                excused += 1

                # -------------------------------------
        # Parent Notification
        # -------------------------------------
        parent_links = ParentStudent.objects.filter(student=student)

        for parent_link in parent_links:
            create_notification(
                recipient=parent_link.parent.user,
                notification_type=Notification.NotificationType.ATTENDANCE,
                title="Attendance Marked",
                message=(
                    f"Dear Parent, {student.first_name} "
                    f"{student.last_name} has been marked "
                    f"{record['status']} today."
                ),
                triggered_by=request.user,
            )

        return Response(
            {
                "message": "Attendance saved successfully.",
                "submission": submission.id,
                "classroom": str(submission.classroom),
                "date": submission.date,
                "total_records": len(serializer.validated_data["records"]),
                "summary": {
                    "present": present,
                    "absent": absent,
                    "excused": excused,
                },
            },
            status=status.HTTP_200_OK,
        )

# =====================================================
# Submit Attendance
# =====================================================
class SubmitAttendanceView(APIView):
    permission_classes = [IsAssignedClassTeacher]

    @transaction.atomic
    def post(self, request):

        serializer = SubmitAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = get_object_or_404(
            AttendanceSubmission.objects.select_for_update().select_related(
                "classroom",
            ),
            pk=serializer.validated_data["submission"],
        )

        # =====================================
        # Verify Teacher Profile
        # =====================================
        try:
            teacher_profile = request.user.teacher_profile

        except TeacherProfile.DoesNotExist:
            return Response(
                {
                    "error": "Only teachers can submit attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # =====================================
        # Verify Class Teacher Assignment
        # =====================================
        assigned = TeacherAssignment.objects.filter(
            teacher=teacher_profile,
            classroom=submission.classroom,
            is_class_teacher=True,
            is_active=True,
        ).exists()

        if not assigned:
            return Response(
                {
                    "error": "You are not assigned as the class teacher for this classroom."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # =====================================
        # Already Submitted?
        # =====================================
        if submission.approval_status == AttendanceSubmission.ApprovalStatus.PENDING:
            return Response(
                {
                    "error": "Attendance has already been submitted."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Already Approved?
        # =====================================
        if submission.approval_status == AttendanceSubmission.ApprovalStatus.APPROVED:
            return Response(
                {
                    "error": "Attendance has already been approved."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Ensure Attendance Exists
        # =====================================
        if not submission.attendance_records.exists():
            return Response(
                {
                    "error": "Cannot submit attendance before marking students."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Submit Attendance
        # =====================================
        submission.approval_status = AttendanceSubmission.ApprovalStatus.PENDING
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
                "message": "Attendance submitted successfully.",
                "submission": submission.id,
                "classroom": str(submission.classroom),
                "date": submission.date,
                "status": submission.approval_status,
                "submitted_by": request.user.get_full_name(),
                "submitted_at": submission.submitted_at,
            },
            status=status.HTTP_200_OK,
        )

# =====================================================
# Pending Attendance List
# =====================================================
class PendingAttendanceListView(APIView):

    def get(self, request):

        # =====================================
        # Only Super Admin & Academic Coordinator
        # =====================================
        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
        ]:
            return Response(
                {
                    "error": "Only the Super Admin or Academic Coordinator can view pending attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        submissions = (
            AttendanceSubmission.objects
            .filter(
                approval_status=AttendanceSubmission.ApprovalStatus.PENDING
            )
            .select_related(
                "classroom",
                "submitted_by",
            )
            .order_by(
                "date",
                "classroom",
            )
        )

        serializer = PendingAttendanceSerializer(
            submissions,
            many=True,
        )

        return Response(
            {
                "count": submissions.count(),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

# =====================================================
# Approve Attendance
# =====================================================
class ApproveAttendanceView(APIView):

    @transaction.atomic
    def post(self, request):

        # =====================================
        # Only Super Admin & Academic Coordinator
        # =====================================
        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
        ]:
            return Response(
                {
                    "error": "Only the Super Admin or Academic Coordinator can approve attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ApproveAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = get_object_or_404(
            AttendanceSubmission.objects.select_for_update().select_related(
                "classroom",
                "submitted_by",
            ),
            pk=serializer.validated_data["submission"],
        )

        # =====================================
        # Must be Pending
        # =====================================
        if submission.approval_status != AttendanceSubmission.ApprovalStatus.PENDING:
            return Response(
                {
                    "error": "Only pending attendance can be approved."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Ensure Attendance Records Exist
        # =====================================
        if not submission.attendance_records.exists():
            return Response(
                {
                    "error": "This attendance submission has no student records."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Approve Attendance
        # =====================================
        submission.approval_status = AttendanceSubmission.ApprovalStatus.APPROVED
        submission.approved_by = request.user
        submission.approved_at = timezone.now()

        submission.save(
            update_fields=[
                "approval_status",
                "approved_by",
                "approved_at",
            ]
        )

        return Response(
            {
                "message": "Attendance approved successfully.",
                "submission": submission.id,
                "classroom": str(submission.classroom),
                "date": submission.date,
                "status": submission.approval_status,
                "approved_by": request.user.get_full_name(),
                "approved_at": submission.approved_at,
            },
            status=status.HTTP_200_OK,
        )
            
# =====================================================
# Return Attendance
# =====================================================
class ReturnAttendanceView(APIView):

    @transaction.atomic
    def post(self, request):

        # =====================================
        # Only Super Admin & Academic Coordinator
        # =====================================
        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
        ]:
            return Response(
                {
                    "error": "Only the Super Admin or Academic Coordinator can return attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ReturnAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = get_object_or_404(
            AttendanceSubmission.objects.select_for_update().select_related(
                "classroom",
                "submitted_by",
            ),
            pk=serializer.validated_data["submission"],
        )

        # =====================================
        # Attendance must be Pending
        # =====================================
        if submission.approval_status != AttendanceSubmission.ApprovalStatus.PENDING:
            return Response(
                {
                    "error": "Only pending attendance can be returned."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # =====================================
        # Return Attendance
        # =====================================
        submission.approval_status = AttendanceSubmission.ApprovalStatus.RETURNED
        submission.approved_by = request.user
        submission.approved_at = timezone.now()
        submission.coordinator_comments = serializer.validated_data[
            "coordinator_comments"
        ]

        submission.save(
            update_fields=[
                "approval_status",
                "approved_by",
                "approved_at",
                "coordinator_comments",
            ]
        )

        # =====================================
        # Notification (Enable later)
        # =====================================
        # create_notification(
        #     recipient=submission.submitted_by,
        #     notification_type="Attendance",
        #     title="Attendance Returned",
        #     message=f"Attendance for {submission.classroom} "
        #             f"was returned for correction.",
        #     triggered_by=request.user,
        # )

        return Response(
            {
                "message": "Attendance returned successfully.",
                "submission": submission.id,
                "classroom": str(submission.classroom),
                "date": submission.date,
                "status": submission.approval_status,
                "returned_by": request.user.get_full_name(),
                "returned_at": submission.approved_at,
                "comments": submission.coordinator_comments,
            },
            status=status.HTTP_200_OK,
        )
    
# =====================================================
# Attendance Detail
# =====================================================
class AttendanceDetailView(APIView):

    def get(self, request, submission_id):

        # =====================================
        # Only Super Admin & Academic Coordinator
        # =====================================
        if request.user.role not in [
            CustomUser.Role.SUPER_ADMIN,
            CustomUser.Role.ACADEMIC_COORDINATOR,
        ]:
            return Response(
                {
                    "error": "Only the Super Admin or Academic Coordinator can view attendance details."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        submission = get_object_or_404(
            AttendanceSubmission.objects.select_related(
                "classroom",
                "submitted_by",
                "approved_by",
            ),
            pk=submission_id,
        )

        records = (
            Attendance.objects.filter(
                submission=submission,
            )
            .select_related(
                "student",
            )
            .order_by(
                "student__admission_number",
            )
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
                "approval_status": submission.approval_status,

                "submitted_by": (
                    submission.submitted_by.get_full_name()
                    if submission.submitted_by
                    else None
                ),

                "submitted_at": submission.submitted_at,

                "approved_by": (
                    submission.approved_by.get_full_name()
                    if submission.approved_by
                    else None
                ),

                "approved_at": submission.approved_at,

                "coordinator_comments": submission.coordinator_comments,

                "total_students": records.count(),

                "attendance": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# =====================================================
# Student Attendance History
# =====================================================
class StudentAttendanceHistoryView(APIView):

    def get(self, request, student_id):

        # =====================================
        # Only authenticated users
        # =====================================
        if not request.user.is_authenticated:
            return Response(
                {
                    "error": "Authentication credentials were not provided."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # =====================================
        # Retrieve Student
        # =====================================
        student = get_object_or_404(
            Student.objects.select_related(
                "classroom",
                "parent__user",
            ),
            pk=student_id,
        )

        # =====================================
        # Retrieve Attendance Records
        # =====================================
        records = (
            Attendance.objects.filter(
                student=student,
            )
            .select_related(
                "submission",
                "submission__classroom",
            )
            .order_by(
                "-submission__date",
            )
        )

        serializer = StudentAttendanceHistorySerializer(
            records,
            many=True,
        )

        # =====================================
        # Attendance Summary
        # =====================================
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
                    "assessment_number": student.assessment_number,
                    "name": f"{student.first_name} {student.last_name}",
                    "classroom": str(student.classroom),
                    "status": student.status,
                },

                "summary": {
                    "total_days": total,
                    "present": present,
                    "absent": absent,
                    "excused": excused,
                    "attendance_percentage": attendance_percentage,
                },

                "attendance": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    

# =====================================================
# Create Attendance Submission (Draft)
# =====================================================
class AttendanceSubmissionCreateView(APIView):
    permission_classes = [IsAssignedClassTeacher]

    @transaction.atomic
    def post(self, request):

        serializer = CreateAttendanceSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        classroom = get_object_or_404(
            ClassRoom,
            pk=serializer.validated_data["classroom"],
        )

        # Verify teacher profile
        try:
            teacher_profile = request.user.teacher_profile
        except TeacherProfile.DoesNotExist:
            return Response(
                {
                    "error": "Only teachers can create attendance."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Verify class teacher assignment
        assigned = TeacherAssignment.objects.filter(
            teacher=teacher_profile,
            classroom=classroom,
            is_class_teacher=True,
            is_active=True,
        ).exists()

        if not assigned:
            return Response(
                {
                    "error": "You are not the assigned class teacher."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Prevent duplicate submissions
        submission, created = AttendanceSubmission.objects.get_or_create(
            classroom=classroom,
            date=timezone.localdate(),
            defaults={
                "submitted_by": request.user,
                "approval_status": AttendanceSubmission.ApprovalStatus.DRAFT,
            },
        )

        if not created:
            return Response(
                {
                    "error": "Attendance draft for today already exists.",
                    "submission_id": submission.id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Attendance draft created successfully.",
                "submission": submission.id,
                "classroom": str(classroom),
                "date": submission.date,
                "status": submission.approval_status,
            },
            status=status.HTTP_201_CREATED,
        )

