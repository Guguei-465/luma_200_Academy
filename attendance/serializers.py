from rest_framework import serializers
from .models import AttendanceSubmission, Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    admission_number = serializers.CharField(source="student.admission_number", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "student", "student_name", "admission_number", "status", "remarks", "marked_at", "updated_at"]
        read_only_fields = ["marked_at", "updated_at"]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class AttendanceSubmissionSerializer(serializers.ModelSerializer):
    attendance_records = AttendanceSerializer(many=True, read_only=True)
    assignment = serializers.IntegerField(source="assignment.id", read_only=True)
    classroom_name = serializers.SerializerMethodField()
    submitted_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSubmission
        fields = [
            "id", "assignment", "classroom", "classroom_name", "date",
            "submitted_by", "submitted_by_name", "status",
            "created_at", "updated_at", "attendance_records",
        ]
        read_only_fields = ["submitted_by", "created_at", "updated_at"]

    def get_classroom_name(self, obj):
        return str(obj.classroom)

    def get_submitted_by_name(self, obj):
        return obj.submitted_by.get_full_name() if obj.submitted_by else None


class AttendanceRecordSerializer(serializers.Serializer):
    student = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Attendance.Status.choices)
    remarks = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["status"] != Attendance.Status.PRESENT and not attrs.get("remarks"):
            raise serializers.ValidationError({"remarks": "Remarks are required when a student is absent or excused."})
        return attrs


class BulkAttendanceSerializer(serializers.Serializer):
    submission = serializers.IntegerField()
    records = AttendanceRecordSerializer(many=True)

    def validate_records(self, records):
        student_ids = [r["student"] for r in records]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError("Duplicate students found.")
        return records


class AttendanceDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    admission_number = serializers.CharField(source="student.admission_number", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "student_name", "admission_number", "status", "remarks"]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class StudentAttendanceHistorySerializer(serializers.ModelSerializer):
    classroom = serializers.SerializerMethodField()
    date = serializers.DateField(source="submission.date")

    class Meta:
        model = Attendance
        fields = ["id", "classroom", "date", "status", "remarks"]

    def get_classroom(self, obj):
        return str(obj.submission.classroom)


class CreateAttendanceSubmissionSerializer(serializers.Serializer):
    assignment = serializers.IntegerField()