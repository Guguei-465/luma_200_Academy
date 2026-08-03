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
        instance = getattr(self, "instance", None)

        # 1. Required assignment check first
        if assignment is None:
            raise serializers.ValidationError({"assignment": "Teacher assignment is required."})

        # 2. End time check
        if end_time <= start_time:
            raise serializers.ValidationError({"end_time": "End time must be later than start time."})

        # 3. Assignment active check
        if not assignment.is_active:
            raise serializers.ValidationError({"assignment": "This teacher assignment is inactive."})

        # 4. Academic year match
        if assignment.academic_year != academic_year:
            raise serializers.ValidationError({"academic_year": "Academic year does not match the assignment."})

        # 5. Term match
        if assignment.term != term:
            raise serializers.ValidationError({"term": "Term does not match the assignment."})

        # Skip conflict checks for breaks if needed
        if data.get("is_break", False):
            return data

        # 6. Conflict checks
        lessons = Timetable.objects.filter(day=day, academic_year=academic_year, term=term)
        if instance:
            lessons = lessons.exclude(pk=instance.pk)

        for lesson in lessons:
            overlap = start_time < lesson.end_time and end_time > lesson.start_time
            if not overlap:
                continue
            if lesson.assignment.teacher == assignment.teacher:
                raise serializers.ValidationError({"teacher": f"{assignment.teacher.user.get_full_name()} is already assigned during this time."})
            if lesson.assignment.classroom == assignment.classroom:
                raise serializers.ValidationError({"classroom": f"{assignment.classroom} already has a lesson during this time."})

        return data
            