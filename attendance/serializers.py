from rest_framework import serializers

from .models import AttendanceSubmission, Attendance


# ====================================================
# Attendance (Student Record)
# ====================================================
class AttendanceSerializer(serializers.ModelSerializer):

    student_name = serializers.SerializerMethodField()

    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "student_name",
            "admission_number",
            "status",
            "remarks",
            "marked_at",
            "updated_at",
        ]

        read_only_fields = [
            "marked_at",
            "updated_at",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


# ====================================================
# Attendance Submission (Header)
# ====================================================
class AttendanceSubmissionSerializer(serializers.ModelSerializer):

    attendance_records = AttendanceSerializer(
        many=True,
        read_only=True,
    )

    classroom_name = serializers.SerializerMethodField()

    submitted_by_name = serializers.SerializerMethodField()

    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSubmission
        fields = [
            "id",
            "classroom",
            "classroom_name",
            "date",
            "submitted_by",
            "submitted_by_name",
            "submitted_at",
            "approval_status",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "coordinator_comments",
            "created_at",
            "updated_at",
            "attendance_records",
        ]

        read_only_fields = [
            "submitted_by",
            "submitted_at",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        ]

    def get_classroom_name(self, obj):
        return str(obj.classroom)

    def get_submitted_by_name(self, obj):
        if obj.submitted_by:
            return obj.submitted_by.get_full_name()
        return None

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return obj.approved_by.get_full_name()
        return None


# ====================================================
# Single Attendance Record (Input)
# ====================================================
class AttendanceRecordSerializer(serializers.Serializer):

    student = serializers.IntegerField()

    status = serializers.ChoiceField(
        choices=Attendance.Status.choices
    )

    remarks = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):

        if (
            attrs["status"] != Attendance.Status.PRESENT
            and not attrs.get("remarks")
        ):
            raise serializers.ValidationError(
                {
                    "remarks":
                    "Remarks are required when a student is absent or excused."
                }
            )

        return attrs


# ====================================================
# Bulk Attendance
# ====================================================
class BulkAttendanceSerializer(serializers.Serializer):

    submission = serializers.IntegerField()

    records = AttendanceRecordSerializer(
        many=True
    )

    def validate_records(self, records):

        student_ids = [
            record["student"]
            for record in records
        ]

        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError(
                "Duplicate students found in attendance records."
            )

        return records


# ====================================================
# Submit Attendance
# ====================================================
class SubmitAttendanceSerializer(serializers.Serializer):
    submission = serializers.IntegerField()


# ====================================================
# Pending Attendance
# ====================================================
class PendingAttendanceSerializer(serializers.ModelSerializer):

    classroom = serializers.SerializerMethodField()

    submitted_by = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceSubmission

        fields = [
            "id",
            "classroom",
            "date",
            "approval_status",
            "submitted_by",
            "submitted_at",
        ]

    def get_classroom(self, obj):
        return str(obj.classroom)

    def get_submitted_by(self, obj):
        if obj.submitted_by:
            return obj.submitted_by.get_full_name()
        return None


# ====================================================
# Approve Attendance
# ====================================================
class ApproveAttendanceSerializer(serializers.Serializer):
    submission = serializers.IntegerField()


# ====================================================
# Return Attendance
# ====================================================
class ReturnAttendanceSerializer(serializers.Serializer):
    submission = serializers.IntegerField()

    coordinator_comments = serializers.CharField()


# ====================================================
# Attendance Details
# ====================================================
class AttendanceDetailSerializer(serializers.ModelSerializer):

    student_name = serializers.SerializerMethodField()

    admission_number = serializers.CharField(
        source="student.admission_number",
        read_only=True,
    )

    class Meta:
        model = Attendance

        fields = [
            "id",
            "student_name",
            "admission_number",
            "status",
            "remarks",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


# ====================================================
# Student Attendance History
# ====================================================
class StudentAttendanceHistorySerializer(serializers.ModelSerializer):

    classroom = serializers.SerializerMethodField()

    date = serializers.DateField(
        source="submission.date"
    )

    class Meta:
        model = Attendance

        fields = [
            "id",
            "classroom",
            "date",
            "status",
            "remarks",
        ]

    def get_classroom(self, obj):
        return str(obj.submission.classroom)
    

class CreateAttendanceSubmissionSerializer(serializers.Serializer):
    classroom = serializers.IntegerField()
