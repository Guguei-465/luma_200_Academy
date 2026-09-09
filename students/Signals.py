from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from classes.models import ClassRoom
from .models import Student


@receiver(post_save, sender=Student)
def increase_student_count(sender, instance, created, **kwargs):
    """
    Increase total_students when a new student is registered.
    """
    if created:
        classroom = instance.classroom
        classroom.total_students += 1
        classroom.save(update_fields=["total_students"])


@receiver(post_delete, sender=Student)
def decrease_student_count(sender, instance, **kwargs):
    """
    Decrease total_students when a student is deleted.
    """
    classroom = instance.classroom
    if classroom.total_students > 0:
        classroom.total_students -= 1
        classroom.save(update_fields=["total_students"])


@receiver(pre_save, sender=Student)
def update_student_count_on_transfer(sender, instance, **kwargs):
    """
    Update student totals when a student changes classroom.
    """
    if not instance.pk:
        return

    try:
        old_student = Student.objects.get(pk=instance.pk)
    except Student.DoesNotExist:
        return

    if old_student.classroom != instance.classroom:
        old_class = old_student.classroom
        new_class = instance.classroom

        if old_class.total_students > 0:
            old_class.total_students -= 1
            old_class.save(update_fields=["total_students"])

        new_class.total_students += 1
        new_class.save(update_fields=["total_students"])