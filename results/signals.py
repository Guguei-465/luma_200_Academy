from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Result, ResultSubmission
from .services import process_result


# =====================================================
# Process Individual Result
# =====================================================
@receiver(post_save, sender=Result)
def process_individual_result(sender, instance, **kwargs):
    """
    Automatically process an individual result whenever it is
    created or updated.
    """

    try:
        process_result(instance)
    except Exception as e:
        print("PROCESS RESULT ERROR:", e)


# =====================================================
# Process Entire Submission
# =====================================================
@receiver(post_save, sender=ResultSubmission)
def process_submission_results(sender, instance, **kwargs):
    """
    Process all results whenever a ResultSubmission is saved.
    """

    for result in instance.results.all():
        process_result(result)