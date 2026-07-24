from .models import Notification


def create_notification(
    recipient,
    title,
    message,
    notification_type,
    triggered_by=None,
):
    """
    Create a notification for a single user.
    """

    if recipient is None:
        raise ValueError("Recipient cannot be None.")

    return Notification.objects.create(
        recipient=recipient,
        triggered_by=triggered_by,
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
    """
    Create the same notification for multiple users.
    """

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