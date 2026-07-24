from rest_framework import serializers
from .models import ClassRoom


class ClassRoomSerializer(serializers.ModelSerializer):
    class_teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = ClassRoom
        fields = [
            "id",
            "grade",
            "stream",
            "capacity",
            "class_teacher",
            "class_teacher_name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_class_teacher_name(self, obj):
        if obj.class_teacher:
            return obj.class_teacher.user.get_full_name()
        return None
    
def validate_capacity(self, value):
    if value < 1:
        raise serializers.ValidationError(
            "Capacity must be greater than zero."
        )

    if value > 100:
        raise serializers.ValidationError(
            "Capacity cannot exceed 100 students."
        )

    return value    

def validate_class_teacher(self, teacher):
    if teacher is None:
        return teacher

    queryset = ClassRoom.objects.filter(class_teacher=teacher)

    if self.instance:
        queryset = queryset.exclude(pk=self.instance.pk)

    if queryset.exists():
        raise serializers.ValidationError(
            "This teacher is already assigned as a class teacher."
        )

    return teacher