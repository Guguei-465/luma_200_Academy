from django.db import models

from accounts.models import CustomUser
from students.models import Student
from subjects.models import Subject
from students.models import ClassRoom

TERM_CHOICES = [
    ("Term 1", "Term 1"),
    ("Term 2", "Term 2"),
    ("Term 3", "Term 3"),
]
# =====================================================
# CBC Grade Scale
# =====================================================
class GradeScale(models.Model):
    level = models.CharField(
        max_length=5,
        unique=True
    )

    description = models.CharField(
        max_length=100
    )

    minimum_score = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    maximum_score = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    remarks = models.CharField(
        max_length=255,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-minimum_score"]

    def __str__(self):
        return f"{self.level} ({self.minimum_score}-{self.maximum_score})"

# =====================================================
# Learning Outcome
# =====================================================
class LearningOutcome(models.Model):

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="learning_outcomes"
    )

    name = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    maximum_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = (
            "subject",
            "name",
        )
        ordering = [
            "subject",
            "name",
        ]

    def __str__(self):
        return f"{self.subject} - {self.name}"
    

# =====================================================
# Assessment Types
# Example:
# CAT
# Project
# Practical
# End Term Assessment
# =====================================================
class AssessmentType(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


# =====================================================
# Assessment
# =====================================================
class Assessment(models.Model):

    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]

    assessment_type = models.ForeignKey(
        AssessmentType,
        on_delete=models.CASCADE,
        related_name="assessments"
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name="assessments"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="assessments"
    )

    academic_year = models.CharField(
        max_length=20
    )
    
    term = models.CharField(max_length=20, choices=TERM_CHOICES)

    total_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100
    )
    

    assessment_date = models.DateField()

    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_assessments"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.subject} - {self.assessment_type}"


# =====================================================
# Result Submission
# =====================================================
class ResultSubmission(models.Model):
    class ApprovalStatus(models.TextChoices):
        DRAFT = "Draft", "Draft"
        PENDING = "Pending", "Pending"
        APPROVED = "Approved", "Approved"
        RETURNED = "Returned", "Returned"

    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="result_submissions",
        null=True,
        blank=True,
    )

    submitted_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_results"
    )

    submitted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.DRAFT
    )

    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_results"
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    coordinator_comments = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.assessment} ({self.approval_status})"

# =====================================================
# Student Marks
# =====================================================
class Result(models.Model):

    class ResultStatus(models.TextChoices):
        PENDING = "Pending", "Pending"
        PRESENT = "Present", "Present"
        ABSENT = "Absent", "Absent"
        EXCUSED = "Excused", "Excused"
        EXEMPTED = "Exempted", "Exempted"

    submission = models.ForeignKey(
        ResultSubmission,
        on_delete=models.CASCADE,
        related_name="results"
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="results"
    )

    # Student attendance/status for this assessment
    status = models.CharField(
        max_length=20,
        choices=ResultStatus.choices,
        default=ResultStatus.PENDING
    )

    # Null if absent, exempted, excused or pending
    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Automatically calculated by the system
    weighted_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    # Automatically assigned by the grading engine
    grade = models.ForeignKey(
        GradeScale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    cbc_code = models.CharField(
        max_length=5,
        blank=True,
    )

    cbc_description = models.CharField(
        max_length=100,
        blank=True,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True
    )


    entered_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entered_marks"
    )

    # Audit trail
    last_modified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modified_results"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = (
            "submission",
            "student",
        )

    def __str__(self):
        if self.status == self.ResultStatus.PRESENT:
            return f"{self.student} - {self.marks}"
        return f"{self.student} - {self.status}"


# =====================================================
# Final Subject Results
# =====================================================
class StudentResult(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="final_results"
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE
    )

    academic_year = models.CharField(
        max_length=20
    )

    term = models.CharField(
        max_length=20
    )

    total_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    average_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    grade = models.ForeignKey(
        GradeScale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    cbc_code = models.CharField(
        max_length=5,
        blank=True,
    )

    cbc_description = models.CharField(
        max_length=50,
        blank=True,
    )

    teacher_comment = models.TextField(
        blank=True
    )

    class_teacher_comment = models.TextField(
        blank=True
    )

    headteacher_comment = models.TextField(
        blank=True
    )

    generated_at = models.DateTimeField(
        auto_now_add=True
    )
    subject_position = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    highest_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    lowest_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    class_average = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    learners_assessed = models.PositiveIntegerField(
        default=0
    )

    class Meta:
        unique_together = (
            "student",
            "subject",
            "term",
            "academic_year",
        )

    def __str__(self):
        return f"{self.student} - {self.subject}"

# =====================================================
# Student Term Result
# Stores overall performance for one learner in one term
# =====================================================
class StudentTermResult(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="term_results"
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name="term_results"
    )

    academic_year = models.CharField(
        max_length=20
    )

    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]
    term = models.CharField(max_length=20, choices=TERM_CHOICES)


    total_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    average_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )

    overall_grade = models.ForeignKey(
        GradeScale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="overall_results"
    )

    cbc_code = models.CharField(
        max_length=5,
        blank=True,
    )

    cbc_description = models.CharField(
        max_length=100,
        blank=True,
    )

    position = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    total_subjects = models.PositiveIntegerField(
        default=0
    )

    attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    class_teacher_comment = models.TextField(
        blank=True
    )

    headteacher_comment = models.TextField(
        blank=True
    )

    generated_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    teacher_comment = models.TextField(
        blank=True,
        help_text="Subject teacher's comment"
    )

    class Meta:
        unique_together = (
            "student",
            "academic_year",
            "term",
        )
        ordering = [
            "student"
        ]

    def __str__(self):
        return f"{self.student} - {self.term} ({self.academic_year})"

# =====================================================
# Automatic Comments
# =====================================================
class ReportComment(models.Model):

    grade = models.ForeignKey(
        GradeScale,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    comment = models.TextField()

    def __str__(self):
        return self.grade.level
    
class AssessmentRubric(models.Model):
    min_score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField()
    code = models.CharField(max_length=5)
    description = models.CharField(max_length=100)
    order = models.PositiveIntegerField()    