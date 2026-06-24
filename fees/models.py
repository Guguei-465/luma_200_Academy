from django.db import models
from students.models import Student


class Fee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    term = models.CharField(max_length=20)
    year = models.IntegerField()

    receipt_no = models.CharField(max_length=50, unique=True)
    date_paid = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.amount_paid}" 