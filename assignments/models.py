from django.db import models
from accounts.models import TeacherProfile, CustomUser
from classes.models import ClassRoom
from subjects.models import Subject
from datetime import date


# ==========================================
# Academic Year Generator
# ==========================================
def current_academic_year():
    return f"{date.today().year}/{date.today().year + 1}"


# ==========================================
# Teacher Assignment
# ==========================================
class TeacherAssignment(models.Model):

    class Term(models.TextChoices):
        TERM_1 = "Term 1", "Term 1"
        TERM_2 = "Term 2", "Term 2"
        TERM_3 = "Term 3", "Term 3"

    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name="teacher_assignments",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="teacher_assignments",
    )

    academic_year = models.CharField(
        max_length=9,
        default=current_academic_year,
    )

    term = models.CharField(
        max_length=10,
        choices=Term.choices,
    )

    is_active = models.BooleanField(default=True)

    # Indicates whether this teacher is the official class teacher
    is_class_teacher = models.BooleanField(default=False)

    assigned_date = models.DateField(auto_now_add=True)

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "academic_year",
            "term",
            "classroom",
        ]

        unique_together = (
            "teacher",
            "classroom",
            "subject",
            "academic_year",
            "term",
        )

    def __str__(self):
        return (
            f"{self.teacher.user.get_full_name()} - "
            f"{self.subject.name} - "
            f"{self.classroom}"
        )
     