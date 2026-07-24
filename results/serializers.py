from rest_framework import serializers

from .models import (
    GradeScale,
    AssessmentType,
    Assessment,
    ResultSubmission,
    Result,
    StudentResult,
    StudentTermResult,
    ReportComment,
    LearningOutcome,
)


# =====================================================
# Grade Scale
# =====================================================
class GradeScaleSerializer(serializers.ModelSerializer):

    class Meta:
        model = GradeScale
        fields = "__all__"

    def validate(self, attrs):
        minimum = attrs["minimum_score"]
        maximum = attrs["maximum_score"]

        if minimum > maximum:
            raise serializers.ValidationError(
                "Minimum score cannot be greater than maximum score."
            )

        return attrs


# =====================================================
# Assessment Type
# =====================================================
class AssessmentTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AssessmentType
        fields = "__all__"


# =====================================================
# Assessment
# =====================================================
class AssessmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Assessment
        fields = "__all__"

    def validate_total_marks(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Total marks must be greater than zero."
            )
        return value


# =====================================================
# Result Submission
# =====================================================
class ResultSubmissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ResultSubmission
        fields = "__all__"

        read_only_fields = (
            "submitted_at",
            "approved_at",
            "created_at",
            "updated_at",
        )


# =====================================================
# Result
# =====================================================
class ResultSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.__str__",
        read_only=True
    )

    grade_name = serializers.CharField(
        source="grade.level",
        read_only=True
    )

    cbc_code = serializers.CharField(
        read_only=True
    )

    cbc_description = serializers.CharField(
        read_only=True
    )

    class Meta:
        model = Result
        fields = "__all__"

        read_only_fields = (
            "grade",
            "grade_name",
            "cbc_code",
            "cbc_description",
            "weighted_marks",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):

        submission = attrs.get("submission")
        marks = attrs.get("marks")

        if not submission:
            raise serializers.ValidationError(
                "Result submission is required."
            )

        if submission.assessment_id is None:
            raise serializers.ValidationError(
                "This result submission has no assessment assigned."
            )
        try:
            assessment = Assessment.objects.get(
                pk=submission.assessment_id
            )
        except Assessment.DoesNotExist:
            raise serializers.ValidationError(
                "The assessment linked to this submission does not exist."
            )

        assessment = submission.assessment

        if marks is not None:

            if marks < 0:
                raise serializers.ValidationError(
                    "Marks cannot be negative."
                )

            if marks > assessment.total_marks:
                raise serializers.ValidationError(
                    f"Marks cannot exceed {assessment.total_marks}."
                )

        return attrs


# =====================================================
# Student Result
# =====================================================
class StudentResultSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.__str__",
        read_only=True
    )

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    grade = serializers.CharField(
        source="grade.level",
        read_only=True
    )

    subject_position = serializers.IntegerField(
        read_only=True
    )

    class Meta:
        model = StudentResult
        fields = "__all__"


# =====================================================
# Student Term Result
# =====================================================
class StudentTermResultSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.__str__",
        read_only=True
    )

    overall_grade = serializers.CharField(
        source="overall_grade.level",
        read_only=True
    )

    class Meta:
        model = StudentTermResult
        fields = "__all__"


# =====================================================
# Report Comment
# =====================================================
class ReportCommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ReportComment
        fields = "__all__"


# =====================================================
# Learning Outcome
# =====================================================
class LearningOutcomeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LearningOutcome
        fields = "__all__"


# =====================================================
# Bulk Result Entry
# =====================================================
class BulkResultItemSerializer(serializers.Serializer):

    student = serializers.IntegerField()

    status = serializers.ChoiceField(
        choices=Result.ResultStatus.choices
    )

    marks = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
    )

    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
    )


class BulkResultSerializer(serializers.Serializer):

    submission = serializers.IntegerField()

    results = BulkResultItemSerializer(
        many=True
    )








