from django.db import models
from accounts.models import TeacherProfile
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

class TeacherProfile(models.Model):
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
    )

    EMPLOYMENT_STATUS = (
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("On Leave", "On Leave"),
        ("Retired", "Retired"),
    )

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="teacher_profile"
    )

    employee_number = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    date_of_birth = models.DateField()

    national_id = models.CharField(
        max_length=20,
        unique=True
    )

    phone_number = models.CharField(max_length=20)

    address = models.TextField(blank=True)

    qualification = models.CharField(max_length=150)

    specialization = models.CharField(
        max_length=150,
        blank=True
    )

    employment_date = models.DateField()

    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default="Active"
    )

    profile_picture = models.ImageField(
        upload_to="teachers/",
        blank=True,
        null=True
    )

    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True
    )

    emergency_contact_phone = models.CharField(
        max_length=20,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_number} - {self.first_name} {self.last_name}"        