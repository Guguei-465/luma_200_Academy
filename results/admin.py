from django.contrib import admin
from .models import (
    AssessmentRubric,
    GradeScale,
    AssessmentType,
    Assessment,
    ResultSubmission,
    Result,
    StudentResult,
    StudentTermResult,
    ReportComment,
)


# Register your models here.

# =====================================================
# Grade Scale
# =====================================================
@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = (
        "level",
        "description",
        "minimum_score",
        "maximum_score",
    )

    search_fields = (
        "level",
        "description",
    )

    ordering = (
        "-minimum_score",
    )


# =====================================================
# Assessment Type
# =====================================================
@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "percentage",
    )


# =====================================================
# Assessment
# =====================================================
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "classroom",
        "assessment_type",
        "term",
        "academic_year",
    )

    list_filter = (
        "term",
        "academic_year",
        "subject",
    )


# =====================================================
# Result Submission
# =====================================================
@admin.register(ResultSubmission)
class ResultSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "assessment",
        "approval_status",
        "submitted_by",
        "approved_by",
    )

    list_filter = (
        "approval_status",
    )


# =====================================================
# Result
# =====================================================
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "submission",
        "marks",
        "weighted_marks",
        "grade",
    )

    search_fields = (
        "student__first_name",
        "student__last_name",
    )


# =====================================================
# Student Result
# =====================================================
@admin.register(StudentResult)
class StudentResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "subject",
        "average_score",
        "grade",
    )

    list_filter = (
        "term",
        "academic_year",
    )


# =====================================================
# Student Term Result
# =====================================================
@admin.register(StudentTermResult)
class StudentTermResultAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "term",
        "average_marks",
        "overall_grade",
        "position",
    )


# =====================================================
# Report Comment
# =====================================================
@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = (
        "grade",
        "comment",
    )

# results/admin.py
@admin.register(AssessmentRubric)
class AssessmentRubricAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "min_score", "max_score", "order")
    ordering = ("order",)