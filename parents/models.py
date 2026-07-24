from django.db import models
from django.db import models

from accounts.models import ParentProfile
from students.models import Student


# Create your models here.
class ParentStudent(models.Model):

    class Relationship(models.TextChoices):
        FATHER = "Father", "Father"
        MOTHER = "Mother", "Mother"
        GUARDIAN = "Guardian", "Guardian"

    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name="children",
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="parents",
    )

    relationship = models.CharField(
        max_length=20,
        choices=Relationship.choices,
    )

    class Meta:
        unique_together = ("parent", "student")

    def __str__(self):
        return (
            f"{self.parent.user.get_full_name()} - "
            f"{self.student.first_name} "
            f"{self.student.last_name}"
        )