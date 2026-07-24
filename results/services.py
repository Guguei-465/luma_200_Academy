from decimal import Decimal
from django.db.models import Sum, Avg
from .utils import calculate_cbc_grade
from .models import (
    GradeScale,
    Result,
    StudentResult,
    StudentTermResult,
)
from .models import StudentResult
from django.db.models import Max, Min, Avg, Count



# find grading
def get_grade(score):
    """
    Returns the matching GradeScale object.
    """

    return GradeScale.objects.filter(
        minimum_score__lte=score,
        maximum_score__gte=score
    ).first()


# calculate weighted marks
def calculate_weighted_marks(result):
    """
    Calculates weighted marks based on assessment percentage.
    """

    assessment = result.submission.assessment

    weighted = (
        Decimal(result.marks)
        / Decimal(assessment.total_marks)
    ) * Decimal(assessment.assessment_type.percentage)

    return round(weighted, 2)

# update one result
def update_result(result):
    """
    Calculate weighted marks and CBC grade.
    """

    if result.status != Result.ResultStatus.PRESENT:
        return

    if result.marks is None:
        return

    if not result.submission:
        return

    assessment = result.submission.assessment

    if assessment is None:
        return

    if assessment.total_marks == 0:
        return

    percentage = (
        Decimal(result.marks)
        / Decimal(assessment.total_marks)
    ) * Decimal("100")

    grade = get_grade(percentage)

    cbc_code, cbc_description = calculate_cbc_grade(
        percentage
    )

    result.grade = grade
    result.weighted_marks = calculate_weighted_marks(result)
    result.cbc_code = cbc_code
    result.cbc_description = cbc_description

    print("Percentage:", percentage)
    print("Grade:", grade)
    print("CBC:", cbc_code)
    print("Weighted:", result.weighted_marks)

    result.save(
        update_fields=[
            "grade",
            "weighted_marks",
            "cbc_code",
            "cbc_description",
        ]
    )

# =====================================================
# Update Subject Result
# =====================================================
def update_student_result(student, subject, classroom, term, academic_year):

    results = Result.objects.filter(
        student=student,
        submission__assessment__subject=subject,
        submission__assessment__term=term,
        submission__assessment__academic_year=academic_year,
        submission__approval_status=ResultSubmission.ApprovalStatus.APPROVED,
    )

    if not results.exists():
        return

    total = results.aggregate(
        total=Sum("weighted_marks")
    )["total"] or Decimal("0")

    average = results.aggregate(
        avg=Avg("weighted_marks")
    )["avg"] or Decimal("0")

    grade = get_grade(average)

    cbc_code, cbc_description = calculate_cbc_grade(
        average
    )

    teacher_comment = get_report_comment(grade)

    StudentResult.objects.update_or_create(
        student=student,
        subject=subject,
        classroom=classroom,
        term=term,
        academic_year=academic_year,
        defaults={
            "total_score": total,
            "average_score": average,
            "grade": grade,
            "cbc_code": cbc_code,
            "cbc_description": cbc_description,
            "teacher_comment": teacher_comment,
        }
    )

# =====================================================
# Update Overall Term Result
# =====================================================
def update_student_term_result(student, classroom, term, academic_year):

    subject_results = StudentResult.objects.filter(
        student=student,
        classroom=classroom,
        term=term,
        academic_year=academic_year,
    )

    if not subject_results.exists():
        return

    total_marks = subject_results.aggregate(
        total=Sum("total_score")
    )["total"] or Decimal("0")

    average = subject_results.aggregate(
        avg=Avg("total_score")
    )["avg"] or Decimal("0")

    grade = get_grade(average)

    cbc_code, cbc_description = calculate_cbc_grade(
        average
    )

    class_teacher_comment = get_report_comment(grade)

    StudentTermResult.objects.update_or_create(
        student=student,
        classroom=classroom,
        academic_year=academic_year,
        term=term,
        defaults={
            "total_marks": total_marks,
            "average_marks": average,
            "overall_grade": grade,
            "cbc_code": cbc_code,
            "cbc_description": cbc_description,
            "class_teacher_comment": class_teacher_comment,
            "total_subjects": subject_results.count(),
        }
    )     

# process one result one to another after it has been saved
def process_result(result):
    """
    Processes one learner's result.
    """

    update_result(result)

    assessment = result.submission.assessment

    update_student_result(
        student=result.student,
        subject=assessment.subject,
        classroom=assessment.classroom,
        term=assessment.term,
        academic_year=assessment.academic_year,
    )
    update_student_term_result(
        student=result.student,
        classroom=assessment.classroom,
        term=assessment.term,
        academic_year=assessment.academic_year,
    )

    update_class_positions(
        classroom=assessment.classroom,
        term=assessment.term,
        academic_year=assessment.academic_year,
    )

    update_subject_positions(
        subject=assessment.subject,
        classroom=assessment.classroom,
        term=assessment.term,
        academic_year=assessment.academic_year,
    )

    update_subject_statistics(
        subject=assessment.subject,
        classroom=assessment.classroom,
        term=assessment.term,
        academic_year=assessment.academic_year,
    )

# positional automated for students
def update_class_positions(classroom, term, academic_year):
    """
    Calculate learner positions using competition ranking.
    """

    results = StudentTermResult.objects.filter(
        classroom=classroom,
        term=term,
        academic_year=academic_year
    ).order_by("-average_marks", "student__last_name", "student__first_name")

    previous_average = None
    current_position = 0
    row_number = 0

    for result in results:

        row_number += 1

        if previous_average != result.average_marks:
            current_position = row_number

        result.position = current_position
        result.save(update_fields=["position"])

        previous_average = result.average_marks


def get_report_comment(grade):
    """
    Returns the default comment for a grade.
    """

    if grade is None:
        return ""

    comment = grade.comments.first()

    if comment:
        return comment.comment

    return ""


# =====================================================
# Update Subject Positions
# =====================================================
def update_subject_positions(subject, classroom, term, academic_year):
    """
    Calculate positions for one subject using competition ranking.
    Learners with the same score receive the same position.
    """

    results = StudentResult.objects.filter(
        subject=subject,
        classroom=classroom,
        term=term,
        academic_year=academic_year,
    ).order_by(
        "-total_score",
        "student__last_name",
        "student__first_name",
    )

    previous_score = None
    current_position = 0
    row_number = 0

    for result in results:

        row_number += 1

        if previous_score != result.total_score:
            current_position = row_number

        result.subject_position = current_position
        result.save(update_fields=["subject_position"])

        previous_score = result.total_score


# =====================================================
# Update Subject Statistics
# =====================================================
def update_subject_statistics(subject, classroom, term, academic_year):
    """
    Update class statistics for each learner's subject result.
    """

    queryset = StudentResult.objects.filter(
        subject=subject,
        classroom=classroom,
        term=term,
        academic_year=academic_year,
    )

    if not queryset.exists():
        return

    statistics = queryset.aggregate(
        highest=Max("total_score"),
        lowest=Min("total_score"),
        average=Avg("total_score"),
        assessed=Count("id"),
    )

    queryset.update(
        highest_score=statistics["highest"],
        lowest_score=statistics["lowest"],
        class_average=statistics["average"],
        learners_assessed=statistics["assessed"],
    )
