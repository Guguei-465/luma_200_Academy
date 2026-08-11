from rest_framework import serializers

from .models import Student, StudentTransfer


# =====================================================
# Student
# =====================================================
class StudentSerializer(serializers.ModelSerializer):

    classroom_name = serializers.SerializerMethodField()
    class_teacher = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "admission_number",
            "assessment_number",
            "first_name",
            "last_name",
            "gender",
            "date_of_birth",
            "classroom",
            "classroom_name",
            "class_teacher",
            "national_id",
            "parent_name",
            "status",
            "photo",
            "date_admitted",
            "date_left",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "date_admitted",
            "created_at",
            "updated_at",
        ]

    def get_classroom_name(self, obj):
        return str(obj.classroom)

    def get_class_teacher(self, obj):
        if obj.classroom.class_teacher:
            return obj.classroom.class_teacher.user.get_full_name()
        return None

    def get_parent_name(self, obj):
        return obj.parent.user.get_full_name()


# =====================================================
# Student Transfer
# =====================================================
class StudentTransferSerializer(serializers.ModelSerializer):

    student_name = serializers.CharField(
        source="student.__str__",
        read_only=True,
    )

    from_classroom_name = serializers.SerializerMethodField()

    to_classroom_name = serializers.SerializerMethodField()

    transferred_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentTransfer
        fields = [
            "id",
            "student",
            "student_name",
            "from_classroom",
            "from_classroom_name",
            "to_classroom",
            "to_classroom_name",
            "transferred_by",
            "transferred_by_name",
            "reason",
            "transfer_date",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "transferred_by",
            "transfer_date",
            "created_at",
            "updated_at",
        ]

    def get_from_classroom_name(self, obj):
        return str(obj.from_classroom)

    def get_to_classroom_name(self, obj):
        return str(obj.to_classroom)

    def get_transferred_by_name(self, obj):
        return obj.transferred_by.get_full_name()

    def validate(self, attrs):

        if attrs["from_classroom"] == attrs["to_classroom"]:
            raise serializers.ValidationError(
                {
                    "to_classroom":
                    "Student cannot be transferred to the same classroom."
                }
            )

        if attrs["student"].classroom != attrs["from_classroom"]:
            raise serializers.ValidationError(
                {
                    "from_classroom":
                    "The student's current classroom does not match the selected from_classroom."
                }
            )

        return attrs 