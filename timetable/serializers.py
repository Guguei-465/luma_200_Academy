from rest_framework import serializers
from .models import Timetable


class TimetableSerializer(serializers.ModelSerializer):

    teacher = serializers.CharField(
        source="assignment.teacher.user.get_full_name",
        read_only=True
    )

    subject = serializers.CharField(
        source="assignment.subject.name",
        read_only=True
    )

    classroom = serializers.SerializerMethodField()

    class Meta:
        model = Timetable
        fields = "__all__"

    def get_classroom(self, obj):
        return f"{obj.assignment.classroom.grade} {obj.assignment.classroom.stream}"

    def validate(self, data):

        assignment = data.get("assignment")
        day = data.get("day")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        academic_year = data.get("academic_year")
        term = data.get("term")

        # Updating an existing timetable?
        instance = getattr(self, "instance", None)

        # 1. End time must be after start time
        if end_time <= start_time:
            raise serializers.ValidationError(
                {"end_time": "End time must be later than start time."}
            )

        # 2. Assignment must be active
        if not assignment.is_active:
            raise serializers.ValidationError(
                {"assignment": "This teacher assignment is inactive."}
            )

        # 3. Academic year must match assignment
        if assignment.academic_year != academic_year:
            raise serializers.ValidationError(
                {"academic_year": "Academic year does not match the assignment."}
            )

        # 4. Term must match assignment
        if assignment.term != term:
            raise serializers.ValidationError(
                {"term": "Term does not match the assignment."}
            )

        # Existing lessons for the same day/year/term
        lessons = Timetable.objects.filter(
            day=day,
            academic_year=academic_year,
            term=term,
        )

        # Exclude current lesson when updating
        if instance:
            lessons = lessons.exclude(pk=instance.pk)

        for lesson in lessons:

            # Check for overlapping time
            overlap = (
                start_time < lesson.end_time and
                end_time > lesson.start_time
            )

            if not overlap:
                continue

            # 5. Teacher conflict
            if lesson.assignment.teacher == assignment.teacher:
                raise serializers.ValidationError(
                    {
                        "teacher":
                        f"{assignment.teacher.user.get_full_name()} "
                        f"is already assigned during this time."
                    }
                )

            # 6. Classroom conflict
            if lesson.assignment.classroom == assignment.classroom:
                raise serializers.ValidationError(
                    {
                        "classroom":
                        f"{assignment.classroom} already has a lesson during this time."
                    }
                )
            
            # prevent when teacher assign is not the one
            if assignment is None:
                raise serializers.ValidationError(
                    {
                        "assignment": "Teacher assignment is required."
                    }
                )

        return data 