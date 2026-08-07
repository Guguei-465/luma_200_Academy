# serializers.py
from rest_framework import serializers
from .models import Timetable


class TimetableSerializer(serializers.ModelSerializer):
    # Readable display fields (no more raw IDs in lists!)
    teacher_name = serializers.CharField(
        source="assignment.teacher.user.get_full_name", 
        read_only=True
    )
    subject_name = serializers.CharField(
        source="assignment.subject.name", 
        read_only=True
    )
    classroom_name = serializers.CharField(
        source="assignment.classroom.__str__", 
        read_only=True
    )
    grade = serializers.CharField(
        source="assignment.classroom.grade", 
        read_only=True
    )
    stream = serializers.CharField(
        source="assignment.classroom.stream", 
        read_only=True
    )
    day_display = serializers.CharField(
        source="get_day_display", 
        read_only=True
    )

    class Meta:
        model = Timetable
        # Include all core fields + extra readable fields
        fields = [
            "id",
            "academic_year",
            "term",
            "day",
            "day_display",
            "start_time",
            "end_time",
            "assignment",         # ID — used for create/edit forms
            "teacher_name",       # Read label for display
            "subject_name",       # Read label for display
            "classroom_name",     # Read label for display
            "grade",
            "stream",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]