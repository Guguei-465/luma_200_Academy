from decimal import Decimal
from django.db.models import Avg, Sum, F
from .models import StudentTermResult, StudentResult, Result, GradeScale


def calculate_cbc_grade(score):
    if score >= 90:
        return "EE1", "Exceeding Expectation"
    elif score >= 75:
        return "EE2", "Exceeding Expectation"
    elif score >= 58:
        return "ME1", "Meeting Expectation"
    elif score >= 41:
        return "ME2", "Meeting Expectation"
    elif score >= 31:
        return "AE1", "Approaching Expectation"
    elif score >= 21:
        return "AE2", "Approaching Expectation"
    elif score >= 11:
        return "BE1", "Below Expectation"
    elif score >= 1:
        return "BE2", "Below Expectation"
    return "N/A", "Not Assessed"


def calculate_grade(score):
    return GradeScale.objects.filter(
        minimum_score__lte=Decimal(score),
        maximum_score__gte=Decimal(score),
    ).first()


def calculate_student_subject_result(student, assessment):

    results = Result.objects.filter(
        submission__assessment__subject=assessment.subject,
        submission__assessment__term=assessment.term,
        submission__assessment__academic_year=assessment.academic_year,
        student=student,
        status=Result.ResultStatus.PRESENT,
    )

    if not results.exists():
        return

    average = results.aggregate(Avg("marks"))["marks__avg"] or Decimal("0")
    grade = calculate_grade(average)

    StudentResult.objects.update_or_create(
        student=student,
        classroom=assessment.classroom,
        subject=assessment.subject,
        academic_year=assessment.academic_year,
        term=assessment.term,
        defaults={
            "average_score": average,
            "total_score": average,
            "grade": grade,
            "cbc_code": grade.level if grade else "",
        },
    )


def calculate_student_term_result(student, classroom, term, academic_year):

    subject_results = StudentResult.objects.filter(
        student=student,
        classroom=classroom,
        term=term,
        academic_year=academic_year,
    )

    if not subject_results.exists():
        return

    total_subjects = subject_results.count()
    total_marks = subject_results.aggregate(Sum("average_score"))["average_score__sum"] or Decimal("0")
    average_marks = total_marks / total_subjects
    grade = calculate_grade(average_marks)

    StudentTermResult.objects.update_or_create(
        student=student,
        classroom=classroom,
        term=term,
        academic_year=academic_year,
        defaults={
            "total_marks": total_marks,
            "average_marks": average_marks,
            "overall_grade": grade,
            "cbc_code": grade.level if grade else "",
            "cbc_description": grade.description if grade else "",
            "total_subjects": total_subjects,
        },
    )


def calculate_class_positions(classroom, term, academic_year):

    results = StudentTermResult.objects.filter(
        classroom=classroom,
        term=term,
        academic_year=academic_year,
    ).order_by("-average_marks", "student__first_name")

    for position, result in enumerate(results, start=1):
        result.position = position
        result.save(update_fields=["position"])
