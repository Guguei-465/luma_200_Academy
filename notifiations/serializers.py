from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(
        source="recipient.get_full_name",
        read_only=True,
    )

    triggered_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient",
            "recipient_name",
            "triggered_by",
            "triggered_by_name",
            "notification_type",
            "title",
            "message",
            "is_read",
            "read_at",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "recipient_name",
            "triggered_by_name",
            "triggered_by",
            "is_read",
            "read_at",
        ]

    def get_triggered_by_name(self, obj):
        if not obj.triggered_by:
            return None

        return (
            obj.triggered_by.get_full_name()
            or obj.triggered_by.username
        )