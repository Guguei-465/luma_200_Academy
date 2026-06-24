from django.db import models

class ClassRoom(models.Model):
    name = models.CharField(max_length=50)
    stream = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} {self.stream}"


class Student(models.Model):
    admission_no = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    gender = models.CharField(max_length=10)

    date_of_birth = models.DateField()

    parent_name = models.CharField(max_length=100)

    parent_phone = models.CharField(max_length=20)

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    date_admitted = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.admission_no} - {self.first_name} {self.last_name}" 