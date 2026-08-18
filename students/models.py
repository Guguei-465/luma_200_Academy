from django.db import models
from django.core.exceptions import ValidationError

from accounts.models import ParentProfile, CustomUser
from classes.models import ClassRoom


# =====================================================
# Student
# =====================================================

class Student(models.Model):

    class Gender(models.TextChoices):
        MALE = "Male", "Male"
        FEMALE = "Female", "Female"

    class Status(models.TextChoices):
        ACTIVE = "Active", "Active"
        TRANSFERRED = "Transferred", "Transferred"
        GRADUATED = "Graduated", "Graduated"

    # =================================================
    # LOGIN ACCOUNT LINK
    #
    # Connects this academic record (classroom, parent,
    # status, etc.) to the CustomUser the student logs in
    # with (role=STUDENT). Nullable because a student can
    # exist in the roster before a login account is issued,
    # and a login account can exist before the coordinator
    # enrolls them into a classroom — but once both exist,
    # this is the field every "my class" / "my profile"
    # lookup for the STUDENT role relies on.
    # =================================================
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_record",
        limit_choices_to={"role": "STUDENT"},
    )

    admission_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True
    )

    assessment_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_index=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100
    )

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices
    )

    date_of_birth = models.DateField()

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.PROTECT,
        related_name="students"
    )

    # =================================================
    # ONE PARENT -> MANY STUDENTS
    # =================================================
    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.PROTECT,
        related_name="children"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    photo = models.ImageField(
        upload_to="students/",
        blank=True,
        null=True
    )

    date_admitted = models.DateField(
        auto_now_add=True
    )

    date_left = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "admission_number",
            "first_name",
            "last_name"
        ]

        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return (
            f"{self.first_name} "
            f"{self.last_name} "
            f"({self.admission_number})"
        )


# =====================================================
# Student Transfer
# =====================================================

class StudentTransfer(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="transfers"
    )

    from_classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.PROTECT,
        related_name="transfers_from"
    )

    to_classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.PROTECT,
        related_name="transfers_to"
    )

    transferred_by = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        related_name="student_transfers"
    )

    reason = models.TextField(
        blank=True
    )

    transfer_date = models.DateField(
        auto_now_add=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-transfer_date"]

        verbose_name = "Student Transfer"
        verbose_name_plural = "Student Transfers"

    def __str__(self):
        return (
            f"{self.student} : "
            f"{self.from_classroom} → {self.to_classroom}"
        )

    def clean(self):
        if self.from_classroom == self.to_classroom:
            raise ValidationError(
                "Student cannot be transferred to the same classroom."
            )