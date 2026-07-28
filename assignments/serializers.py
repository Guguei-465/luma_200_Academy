from rest_framework import serializers
from .models import TeacherProfile
from .models import TeacherAssignment


# =====================================================
# Teacher Assignment
# =====================================================
class TeacherAssignmentSerializer(serializers.ModelSerializer):

    teacher_name = serializers.SerializerMethodField()

    classroom_name = serializers.SerializerMethodField()
    
    def get_classroom_name(self, obj):
        return str(obj.classroom)

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    class Meta:
        model = TeacherAssignment
        fields = [
            "id",
            "teacher",
            "teacher_name",
            "classroom",
            "classroom_name",
            "subject",
            "subject_name",
            "academic_year",
            "term",
            "is_class_teacher",
            "is_active",
            "assigned_date",
            "end_date",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "assigned_date",
            "created_at",
            "updated_at",
        ]

    def get_teacher_name(self, obj):
        return obj.teacher.user.get_full_name()

    def validate(self, attrs):
        """
        Ensure:
        1. A classroom has only one active class teacher.
        2. A teacher cannot be a class teacher for more than one classroom
        in the same academic year and term.
        """

        if attrs.get("is_class_teacher"):

            # Check if the classroom already has a class teacher
            classroom_queryset = TeacherAssignment.objects.filter(
                classroom=attrs["classroom"],
                term=attrs["term"],
                academic_year=attrs["academic_year"],
                is_class_teacher=True,
                is_active=True,
            )

            # Check if the teacher is already a class teacher elsewhere
            teacher_queryset = TeacherAssignment.objects.filter(
                teacher=attrs["teacher"],
                term=attrs["term"],
                academic_year=attrs["academic_year"],
                is_class_teacher=True,
                is_active=True,
            )

            # Ignore the current object during update
            if self.instance:
                classroom_queryset = classroom_queryset.exclude(pk=self.instance.pk)
                teacher_queryset = teacher_queryset.exclude(pk=self.instance.pk)

            if classroom_queryset.exists():
                raise serializers.ValidationError(
                    {
                        "classroom": "This classroom already has an active class teacher."
                    }
                )

            if teacher_queryset.exists():
                raise serializers.ValidationError(
                    {
                        "teacher": "This teacher is already assigned as a class teacher to another classroom."
                    }
                )

        return attrs


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = "__all__"        