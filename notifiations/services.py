from .models import Notification


def create_notification(
    recipient,
    title,
    message,
    notification_type,
    triggered_by=None,
    attendance=None,
):
    if recipient is None:
        raise ValueError("Recipient cannot be None.")

    return Notification.objects.create(
        recipient=recipient,
        triggered_by=triggered_by,
        attendance=attendance,
        title=title,
        message=message,
        notification_type=notification_type,
    )


def create_bulk_notifications(
    recipients,
    title,
    message,
    notification_type,
    triggered_by=None,
):
    notifications = [
        Notification(
            recipient=user,
            triggered_by=triggered_by,
            title=title,
            message=message,
            notification_type=notification_type,
        )
        for user in recipients
    ]
    return Notification.objects.bulk_create(notifications)