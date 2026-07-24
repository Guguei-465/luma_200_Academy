from rest_framework import serializers

from .models import ParentStudent


class ParentStudentSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(
        source="parent.user.get_full_name",
        read_only=True,
    )

    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ParentStudent
        fields = [
            "id",
            "parent",
            "parent_name",
            "student",
            "student_name",
            "relationship",
        ]

    def get_student_name(self, obj):
        return (
            f"{obj.student.first_name} "
            f"{obj.student.last_name}"
        )