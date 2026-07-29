from django.db import models
from django.utils import timezone
from assignments.models import TeacherAssignment
from accounts.models import CustomUser
from classes.models import ClassRoom
from students.models import Student


# =====================================================
# Attendance Submission (Header)
# =====================================================
class AttendanceSubmission(models.Model):

    class ApprovalStatus(models.TextChoices):
        DRAFT = "Draft", "Draft"
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        RETURNED = "Returned", "Returned"
    assignment = models.ForeignKey(
            TeacherAssignment,
            on_delete=models.CASCADE,
            related_name="attendance_submissions",
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name="attendance_submissions",
    )

    date = models.DateField(
        default=timezone.localdate,
        db_index=True,
    )

    submitted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_attendance",
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    approval_status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.DRAFT,
    )

    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_attendance",
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    coordinator_comments = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-date",
            "classroom",
        ]

        unique_together = (
            "assignment",
            "date",
        )

        verbose_name = "Attendance Submission"
        verbose_name_plural = "Attendance Submissions"

    def __str__(self):
        return (
            f"{self.assignment.teacher.user.get_full_name()} - "
            f"{self.classroom} - "
            f"{self.date}"
        )


# =====================================================
# Individual Student Attendance (Details)
# =====================================================
class Attendance(models.Model):

    class Status(models.TextChoices):
        PRESENT = "Present", "Present"
        ABSENT = "Absent", "Absent"
        EXCUSED = "Excused", "Excused"

    submission = models.ForeignKey(
        AttendanceSubmission,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    remarks = models.TextField(
        blank=True,
        null=True,
    )

    marked_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "student__admission_number",
        ]

        unique_together = (
            "submission",
            "student",
        )

        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return (
            f"{self.student.admission_number} - "
            f"{self.student.first_name} "
            f"{self.student.last_name} "
            f"({self.status})"
        )