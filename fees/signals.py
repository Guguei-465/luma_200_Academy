from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FeePayment, StudentFee


@receiver(post_save, sender=FeePayment)
def update_student_fee(sender, instance, created, **kwargs):
    """
    Automatically update the student's fee account whenever
    a successful payment is recorded.
    """

    if not created:
        return

    # Only successful payments should affect the balance
    if instance.payment_status != FeePayment.PaymentStatus.SUCCESS:
        return

    student_fee = instance.student_fee

    total_paid = sum(
        payment.amount
        for payment in student_fee.payments.filter(
            payment_status=FeePayment.PaymentStatus.SUCCESS
        )
    )

    student_fee.amount_paid = total_paid
    student_fee.balance = student_fee.total_fee - total_paid
    student_fee.save()